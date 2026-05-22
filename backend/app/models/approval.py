from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedUUIDModel


class Approval(TimeStampedUUIDModel):
    __tablename__ = "approvals"

    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    step_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_steps.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    approver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    status = Column(String(50), nullable=False, default="Pending")  # "Pending", "Approved", "Rejected"
    comments = Column(Text, nullable=True)
    sla_deadline = Column(DateTime, nullable=True)
    actioned_at = Column(DateTime, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="approvals")
    step = relationship("WorkflowStep", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")


class Task(TimeStampedUUIDModel):
    __tablename__ = "tasks"

    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="Todo")  # "Todo", "InProgress", "InReview", "Done"
    priority = Column(String(50), nullable=False, default="Medium")  # "Low", "Medium", "High", "Urgent"
    assignee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    deadline = Column(DateTime, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="tasks")
    assignee = relationship("User")


class Comment(TimeStampedUUIDModel):
    __tablename__ = "comments"

    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    content = Column(Text, nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Attachment(TimeStampedUUIDModel):
    __tablename__ = "attachments"

    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String(100), nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="attachments")
    user = relationship("User", back_populates="attachments")
