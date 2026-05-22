from typing import Any, Dict, List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.middleware.error_handler import ResourceNotFound
from app.models.user import User
from app.models.workflow import Workflow
from app.repositories.workflow import workflow_repo
from app.schemas.workflow import WorkflowCreate, WorkflowResponse, WorkflowUpdate
from app.services.workflow import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Workflows Orchestrator"])


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create dynamic Workflow instance",
    description="Registers a new workflow in Draft state. You can specify a template_id or manually pass steps configuration."
)
def create_workflow(
    req: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Inject current user as initiator
    return WorkflowService.create_workflow(db, current_user, req)


@router.post(
    "/{workflow_id}/start",
    response_model=WorkflowResponse,
    summary="Initiate Draft Workflow processing",
    description="Starts step executions, evaluating the dynamic Rules Engine predicates recursively."
)
def start_workflow(
    workflow_id: UUID,
    context_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return WorkflowService.start_processing(db, workflow_id, context_data)


@router.get(
    "",
    response_model=List[WorkflowResponse],
    summary="List all tenant-isolated Workflows",
    description="Fetches all workflows belonging to the current organization."
)
def list_workflows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return workflow_repo.get_multi(db)


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get Workflow details",
    description="Fetches complete status and detailed steps configurations."
)
def get_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    workflow = workflow_repo.get(db, workflow_id)
    if not workflow:
        raise ResourceNotFound("Selected workflow not found")
    return workflow


@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Workflow instance",
    description="Deletes the workflow. Standard CASCADE delete rules will wipe associated approvals and tasks."
)
def delete_workflow(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    workflow_repo.remove(db, id=workflow_id)
    return
