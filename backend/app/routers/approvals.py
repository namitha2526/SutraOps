import os
import shutil
from typing import Any, List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, get_current_user
from app.middleware.error_handler import ResourceNotFound, NexusFlowException
from app.models.approval import Task, Comment, Attachment
from app.models.user import User
from app.schemas.approval import (
    ApprovalAction,
    ApprovalResponse,
    TaskResponse,
    CommentCreate,
    CommentResponse,
    AttachmentResponse
)
from app.services.approval import ApprovalService

router = APIRouter(prefix="/approvals", tags=["Approvals & Kanban Tasks"])


@router.post(
    "/{approval_id}/action",
    response_model=ApprovalResponse,
    summary="Sign off Step Approval",
    description="Signs off on a step (Approve/Reject), executing cascading rules evaluations and concurrency locks."
)
def action_step(
    approval_id: UUID,
    req: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return ApprovalService.action_approval(
        db, current_user, approval_id, req.status, req.comments
    )


@router.get(
    "/pending",
    response_model=List[ApprovalResponse],
    summary="List active pending step assignments",
    description="Returns all active approvals requiring the user's role authorization."
)
def list_pending(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return ApprovalService.get_pending_approvals(db, current_user)


@router.get(
    "/tasks",
    response_model=List[TaskResponse],
    summary="List Kanban Tasks",
    description="Fetches all Kanban tasks matching the active organization tenant."
)
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return db.query(Task).join(Task.workflow).filter(
        Task.workflow_id == Task.workflow_id,
        Task.workflow.has(organization_id=current_user.organization_id)
    ).all()


@router.put(
    "/tasks/{task_id}/status",
    response_model=TaskResponse,
    summary="Update Kanban task column status",
    description="Transitions a task across board columns (Todo, InProgress, InReview, Done) for dynamic optimistic updates."
)
def update_task(
    task_id: UUID,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return ApprovalService.update_task_status(db, current_user, task_id, status)


@router.post(
    "/{workflow_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add collaborative Comment",
    description="Adds a comment log to the workflow discussion."
)
def post_comment(
    workflow_id: UUID,
    req: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return ApprovalService.add_comment(db, current_user, workflow_id, req.content)


@router.get(
    "/{workflow_id}/comments",
    response_model=List[CommentResponse],
    summary="Get workflow discussion thread",
    description="Retrieves all comments associated with the workflow audit history."
)
def list_comments(
    workflow_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    return db.query(Comment).filter(
        Comment.workflow_id == workflow_id
    ).order_by(Comment.created_at.asc()).all()


@router.post(
    "/{workflow_id}/upload",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload secure Document Attachment",
    description="Uploads multipart documents, committing metadata to DB. Defaults to local storage subfolders in /uploads for local dev."
)
def upload_document(
    workflow_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Ensure local upload dir structure
    os.makedirs(settings.LOCAL_UPLOAD_DIR, exist_ok=True)

    # Clean filename and generate isolated unique target paths
    unique_filename = f"{uuid4()}_{file.filename}"
    file_path = os.path.join(settings.LOCAL_UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise NexusFlowException(f"Failed to write file to local storage. Error: {str(e)}")

    # Calculate file size in bytes
    file.file.seek(0, 2)
    file_size = file.file.tell()

    # Create Attachment DB record
    attachment = Attachment(
        workflow_id=workflow_id,
        user_id=current_user.id,
        file_name=file.filename,
        file_url=f"/static/{unique_filename}",  # Static local fallback URL
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream"
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment
