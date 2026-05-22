from typing import Any
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.security import create_access_token, decode_token, ALGORITHM
from app.middleware.error_handler import NexusFlowException
from app.models.user import User
from app.schemas.auth import OrgRegisterRequest, LoginRequest, Token
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from jose import JWTError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new Organization Workspace Tenant",
    description="Provisions a new corporate organization with baseline departments (Finance, HR, IT, EXEC) and creates the administrator account."
)
def register_tenant(
    req: OrgRegisterRequest,
    db: Session = Depends(get_db)
) -> Any:
    return AuthService.register_organization(db, req)


@router.post(
    "/login",
    response_model=Token,
    summary="User Authentication Login",
    description="Exchanges corporate email and password credentials for JWT access & refresh tokens."
)
def login(
    req: LoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    return AuthService.authenticate_user(db, req)


@router.post(
    "/login/swagger-token",
    response_model=Token,
    include_in_schema=False  # Hide this standard OAuth2 converter endpoint from ReDoc/Swagger but keep it operational for Swagger UI login compatibility
)
def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    # Adapt standard OAuth2 form request structure to LoginRequest
    login_req = LoginRequest(email=form_data.username, password=form_data.password)
    return AuthService.authenticate_user(db, login_req)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Rotate JWT Session Tokens",
    description="Rotates access tokens using a valid active Refresh Token."
)
def refresh_token(
    refresh_token_str: str,
    db: Session = Depends(get_db)
) -> Any:
    try:
        payload = decode_token(refresh_token_str)
        token_type = payload.get("type", "")
        
        if token_type != "refresh":
            raise NexusFlowException(
                message="Invalid token context: Refresh Token type required",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        user_id = payload.get("sub", "")
        org_id = payload.get("org_id", "")
        
        if not user_id or not org_id:
            raise NexusFlowException(
                message="Invalid token claims",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
    except JWTError:
        raise NexusFlowException(
            message="Expired or invalid refresh token signature",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Fetch User to confirm account is active
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise NexusFlowException(
            message="Account is deactivated or not found",
            status_code=status.HTTP_403_FORBIDDEN
        )

    # Generate fresh access token
    new_access_token = create_access_token(
        subject=user.id,
        org_id=user.organization_id,
        role=user.role
    )
    
    return Token(
        access_token=new_access_token,
        refresh_token=refresh_token_str  # Retain same refresh token for rotation length
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Authenticated User Profile",
    description="Resolves active JWT token claims to retrieve current workspace identity and departments information."
)
def get_me(
    current_user: User = Depends(get_current_user)
) -> Any:
    return current_user
