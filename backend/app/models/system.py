from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedUUIDModel


class Notification(TimeStampedUUIDModel):
    __tablename__ = "notifications"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    type = Column(String(100), nullable=False, default="Workflow_Update")  # "Workflow_Update", "Approval_Request", "System_Notice"

    # Relationships
    user = relationship("User", back_populates="notifications")


class AuditLog(TimeStampedUUIDModel):
    __tablename__ = "audit_logs"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    action = Column(String(100), nullable=False)  # "Create_Workflow", "Approve_Step", "User_Login", etc.
    entity_name = Column(String(100), nullable=False)  # "workflows", "approvals", etc.
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    payload = Column(JSON, nullable=True)  # JSON representation of states or parameters
    ip_address = Column(String(50), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
    workflow = relationship("Workflow", back_populates="audit_logs")


class DeadLetterLog(TimeStampedUUIDModel):
    __tablename__ = "dead_letter_logs"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    event_type = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    error_message = Column(Text, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)
