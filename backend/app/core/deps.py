from typing import Generator, List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import user_id_ctx, organization_id_ctx, StructuredLogger
from app.core.security import ALGORITHM
from app.middleware.error_handler import PermissionDenied, ResourceNotFound
from app.models.user import User

# OAuth2 standard scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_db() -> Generator[Session, None, None]:
    """
    Yields database sessions with automatic context tear-downs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Authenticates bearer tokens, resolves user profile context, and binds user context variable.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub", "")
        org_id: str = payload.get("org_id", "")
        
        if not user_id or not org_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials: claim fields missing"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: token signature invalid or expired"
        )

    # Fetch User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ResourceNotFound("User profile not found")
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is currently deactivated"
        )

    # Bind thread-local context variables for audit trails & logging
    user_id_ctx.set(str(user.id))
    organization_id_ctx.set(str(user.organization_id))

    return user


# =====================================================================
# Permission Matrix Checker Engine
# =====================================================================

class PermissionChecker:
    """
    Dependency checking engine implementing RBAC matrix verification.
    """
    # Dynamic capabilities matrix mapping allowed roles
    PERMISSION_MATRIX = {
        "create_workflow": ["SuperAdmin", "Admin", "Manager", "Employee"],
        "approve_step": ["SuperAdmin", "Admin", "Manager"],
        "manage_organization": ["SuperAdmin", "Admin"],
        "view_analytics": ["SuperAdmin", "Admin", "Manager"],
        "manage_templates": ["SuperAdmin", "Admin"],
    }

    def __init__(self, action: str):
        if action not in self.PERMISSION_MATRIX:
            raise ValueError(f"Action '{action}' is not defined in Permission Matrix")
        self.action = action
        self.allowed_roles = self.PERMISSION_MATRIX[action]

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        Validates if current active authenticated user meets Role permission standards.
        """
        if current_user.role not in self.allowed_roles:
            StructuredLogger.warning(
                f"RBAC Violation Blocked: User {current_user.email} attempted unauthorized capability '{self.action}'",
                user_id=str(current_user.id),
                user_role=current_user.role,
                attempted_action=self.action
            )
            raise PermissionDenied(
                f"Forbidden: Your role '{current_user.role}' is unauthorized to perform '{self.action}'"
            )
        return current_user
