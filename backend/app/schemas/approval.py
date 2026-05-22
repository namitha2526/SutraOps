from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.user import UserResponse


# =====================================================================
# Approval Schemas
# =====================================================================

class ApprovalAction(BaseModel):
    status: str = Field(..., description="Decision: 'Approved', 'Rejected'")
    comments: Optional[str] = Field(None, max_length=1000)


class ApprovalResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    step_id: UUID
    approver_id: Optional[UUID]
    status: str
    comments: Optional[str]
    sla_deadline: Optional[datetime]
    actioned_at: Optional[datetime]
    created_at: datetime
    approver: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# =====================================================================
# Task (Kanban) Schemas
# =====================================================================

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    priority: str = Field("Medium", description="Low, Medium, High, Urgent")
    assignee_id: Optional[UUID] = None
    deadline: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, description="Todo, InProgress, InReview, Done")
    priority: Optional[str] = None
    assignee_id: Optional[UUID] = None
    deadline: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    title: str
    description: Optional[str]
    status: str
    priority: str
    assignee_id: Optional[UUID]
    deadline: Optional[datetime]
    created_at: datetime
    assignee: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# =====================================================================
# Comments Schemas
# =====================================================================

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    user_id: UUID
    content: str
    created_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True


# =====================================================================
# Attachment Schemas
# =====================================================================

class AttachmentCreate(BaseModel):
    file_name: str = Field(..., max_length=255)
    file_url: str = Field(..., max_length=1000)
    file_size: int = Field(..., description="Bytes size")
    mime_type: str = Field(..., max_length=100)


class AttachmentResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    user_id: UUID
    file_name: str
    file_url: str
    file_size: int
    mime_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# Notification Schemas
# =====================================================================

class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    message: str
    is_read: bool
    type: str
    created_at: datetime

    class Config:
        from_attributes = True
