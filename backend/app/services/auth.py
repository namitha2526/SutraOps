from sqlalchemy.orm import Session
from app.core.logging import StructuredLogger
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.middleware.error_handler import NexusFlowException, ResourceNotFound
from app.models.tenant import Organization, Department
from app.models.user import User
from app.repositories.user import user_repo
from app.schemas.auth import OrgRegisterRequest, LoginRequest, Token
from fastapi import status


class AuthService:
    """
    Domain service handling core authentication, user login sessions, and multi-tenant onboarding.
    """
    @staticmethod
    def register_organization(db: Session, req: OrgRegisterRequest) -> User:
        # Check if organization domain exists
        existing_org = db.query(Organization).filter(Organization.domain == req.domain).first()
        if existing_org:
            raise NexusFlowException(
                message=f"Organization domain '{req.domain}' is already registered",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Create Organization
        StructuredLogger.info(
            f"Registering new organization: {req.organization_name} with domain {req.domain}"
        )
        
        org = Organization(
            name=req.organization_name,
            domain=req.domain,
            is_active=True
        )
        db.add(org)
        db.flush()  # Resolve org.id before proceeding to secondary structures

        # Create baseline Departments
        departments_to_create = [
            {"name": "Executive Management", "code": "EXEC"},
            {"name": "Finance & Accounting", "code": "FIN"},
            {"name": "Human Resources", "code": "HR"},
            {"name": "Information Technology", "code": "IT"},
        ]
        
        default_dept = None
        for dept_data in departments_to_create:
            dept = Department(
                organization_id=org.id,
                name=dept_data["name"],
                code=dept_data["code"]
            )
            db.add(dept)
            if dept_data["code"] == "EXEC":
                default_dept = dept
                
        db.flush()

        # Create Administrator Account
        hashed_password = get_password_hash(req.admin_password)
        admin_user = User(
            organization_id=org.id,
            department_id=default_dept.id if default_dept else None,
            email=req.admin_email,
            hashed_password=hashed_password,
            full_name=req.admin_name,
            role="Admin",
            is_active=True
        )
        db.add(admin_user)
        
        try:
            db.commit()
            db.refresh(admin_user)
            StructuredLogger.info(
                f"Successfully onboarded Tenant Organization: {org.name} (ID: {org.id})"
            )
            return admin_user
        except Exception as e:
            db.rollback()
            StructuredLogger.error(
                f"Tenant Onboarding Failed: rollback executed. Error: {str(e)}"
            )
            raise NexusFlowException(
                message="Tenant onboarding transaction failed due to system database error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    def authenticate_user(db: Session, req: LoginRequest) -> Token:
        # Resolve email
        user = user_repo.get_by_email(db, req.email)
        if not user:
            StructuredLogger.warning(
                f"Authentication failed: Email {req.email} not registered"
            )
            raise NexusFlowException(
                message="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Check password
        if not verify_password(req.password, user.hashed_password):
            StructuredLogger.warning(
                f"Authentication failed: Incorrect password attempt for {req.email}"
            )
            raise NexusFlowException(
                message="Invalid email or password",
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Verify account active status
        if not user.is_active:
            raise NexusFlowException(
                message="Your account is deactivated. Please contact support.",
                status_code=status.HTTP_403_FORBIDDEN
            )

        # Create session tokens
        access_token = create_access_token(
            subject=user.id,
            org_id=user.organization_id,
            role=user.role
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            org_id=user.organization_id
        )

        StructuredLogger.info(
            f"User logged in successfully: {user.email} (Tenant ID: {user.organization_id})",
            user_id=str(user.id),
            organization_id=str(user.organization_id)
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
