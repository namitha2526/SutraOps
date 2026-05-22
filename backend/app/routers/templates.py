from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user, PermissionChecker
from app.middleware.error_handler import ResourceNotFound
from app.models.user import User
from app.models.workflow import WorkflowTemplate
from app.repositories.workflow import template_repo
from app.schemas.workflow import WorkflowTemplateCreate, WorkflowTemplateResponse

router = APIRouter(prefix="/templates", tags=["Workflow Templates"])


@router.get(
    "",
    response_model=List[WorkflowTemplateResponse],
    summary="List available Workflow Templates",
    description="Fetches all global public templates from the marketplace and tenant-scoped custom blueprints."
)
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Resolves tenant boundary from context, matching NULL or organization_id
    return template_repo.get_marketplace_templates(db)


@router.post(
    "",
    response_model=WorkflowTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom Workflow Template",
    description="Registers a new template blueprint for this tenant. Restricted to Admin and SuperAdmin roles.",
    dependencies=[Depends(PermissionChecker("manage_templates"))]
)
def create_template(
    req: WorkflowTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    obj_in = {
        "organization_id": current_user.organization_id,
        "name": req.name,
        "description": req.description,
        "category": req.category,
        "structure": req.structure,
        "is_active": True
    }
    return template_repo.create(db, obj_in=obj_in)


@router.post(
    "/import-blueprint",
    response_model=WorkflowTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import Workflow Blueprint from Marketplace",
    description="Imports a standard JSON template schema, copying it directly into the organization's active directory.",
    dependencies=[Depends(PermissionChecker("manage_templates"))]
)
def import_blueprint(
    req: WorkflowTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Simulates importing/copying template
    obj_in = {
        "organization_id": current_user.organization_id,
        "name": f"[Imported] {req.name}",
        "description": req.description,
        "category": req.category,
        "structure": req.structure,
        "is_active": True
    }
    return template_repo.create(db, obj_in=obj_in)


@router.get(
    "/{template_id}",
    response_model=WorkflowTemplateResponse,
    summary="Get Template details",
    description="Fetches full step structure of a specific template."
)
def get_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    template = template_repo.get(db, template_id)
    if not template:
        raise ResourceNotFound("Selected template not found")
    return template
