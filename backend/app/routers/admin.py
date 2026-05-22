from typing import Any, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core import config
from app.core.deps import get_db, get_current_user, PermissionChecker
from app.core.logging import StructuredLogger
from app.core.security import get_password_hash
from app.middleware.error_handler import NexusFlowException, ResourceNotFound
from app.models.tenant import Department
from app.models.user import User
from app.repositories.user import user_repo, department_repo
from app.schemas.user import UserCreate, UserResponse, DepartmentCreate, DepartmentResponse

router = APIRouter(prefix="/admin", tags=["Tenant Administration"])


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="List all Tenant Users",
    description="Returns all registered personnel profiles for the active organization. Admin role standard required.",
    dependencies=[Depends(PermissionChecker("manage_organization"))]
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Repository automatically scopes lists by organization context
    return db.query(User).filter(User.organization_id == current_user.organization_id).all()


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard new User",
    description="Registers a new employee or manager in the organization workspace. Restricted to Admin.",
    dependencies=[Depends(PermissionChecker("manage_organization"))]
)
def onboard_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Verify if email exists
    existing = user_repo.get_by_email(db, req.email)
    if existing:
        raise NexusFlowException("Email address already registered in systems", status.HTTP_400_BAD_REQUEST)

    # Hash passwords
    hashed = get_password_hash(req.password)
    
    obj_in = {
        "organization_id": current_user.organization_id,
        "department_id": req.department_id,
        "email": req.email,
        "hashed_password": hashed,
        "full_name": req.full_name,
        "role": req.role,
        "is_active": True
    }
    
    return user_repo.create(db, obj_in=obj_in)


@router.get(
    "/departments",
    response_model=List[DepartmentResponse],
    summary="List Departments",
    description="Returns all registered department codes inside current organization."
)
def list_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return db.query(Department).filter(Department.organization_id == current_user.organization_id).all()


@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create dynamic Department",
    description="Provisions a new department code within the tenant organization. Restricted to Admin.",
    dependencies=[Depends(PermissionChecker("manage_organization"))]
)
def create_dept(
    req: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Check if department code already exists in organization
    existing = db.query(Department).filter(
        Department.organization_id == current_user.organization_id,
        Department.code == req.code
    ).first()
    if existing:
        raise NexusFlowException("Department code already exists inside organization", status.HTTP_400_BAD_REQUEST)

    obj_in = {
        "organization_id": current_user.organization_id,
        "name": req.name,
        "code": req.code
    }
    
    return department_repo.create(db, obj_in=obj_in)


@router.post(
    "/feature-flags",
    summary="Toggle Enterprise Feature Flags",
    description="Dynamically activates/deactivates system capabilities (notifications, analytic charts, step escalations). Admin role required.",
    dependencies=[Depends(PermissionChecker("manage_organization"))]
)
def toggle_feature_flags(
    enable_notifications: bool = True,
    enable_escalation: bool = True,
    enable_analytics: bool = True
) -> Any:
    # Mutates global settings context
    config.settings.ENABLE_NOTIFICATIONS = enable_notifications
    config.settings.ENABLE_ESCALATION = enable_escalation
    config.settings.ENABLE_ANALYTICS = enable_analytics

    StructuredLogger.info(
        f"Feature Flags modified: Notifications={enable_notifications}, "
        f"Escalation={enable_escalation}, Analytics={enable_analytics}"
    )

    return {
        "status": "Success",
        "message": "Dynamic feature flags updated successfully",
        "current_state": {
            "enable_notifications": config.settings.ENABLE_NOTIFICATIONS,
            "enable_escalation": config.settings.ENABLE_ESCALATION,
            "enable_analytics": config.settings.ENABLE_ANALYTICS
        }
    }
