from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedUUIDModel


class WorkflowTemplate(TimeStampedUUIDModel):
    __tablename__ = "workflow_templates"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,  # Null indicates a pre-built marketplace template accessible to all orgs
        index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    category = Column(String(100), nullable=False, default="Procurement")  # e.g., HR, Finance, IT
    structure = Column(JSON, nullable=False)  # JSON structure containing steps & default rules
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="templates")
    workflows = relationship("Workflow", back_populates="template")


class Workflow(TimeStampedUUIDModel):
    __tablename__ = "workflows"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    creator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(String(50), nullable=False, default="Draft")  # "Draft", "Pending", "Approved", "Rejected", "Escalated"
    current_step_id = Column(UUID(as_uuid=True), nullable=True)

    # Optimistic Concurrency Control
    version_id = Column(Integer, nullable=False, default=1)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    # Relationships
    organization = relationship("Organization", back_populates="workflows")
    creator = relationship("User")
    template = relationship("WorkflowTemplate", back_populates="workflows")
    
    steps = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_order"
    )
    approvals = relationship(
        "Approval",
        back_populates="workflow",
        cascade="all, delete-orphan"
    )
    tasks = relationship(
        "Task",
        back_populates="workflow",
        cascade="all, delete-orphan"
    )
    comments = relationship(
        "Comment",
        back_populates="workflow",
        cascade="all, delete-orphan"
    )
    attachments = relationship(
        "Attachment",
        back_populates="workflow",
        cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="workflow",
        cascade="all, delete-orphan"
    )


class WorkflowStep(TimeStampedUUIDModel):
    __tablename__ = "workflow_steps"

    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    step_order = Column(Integer, nullable=False)
    approver_role = Column(String(50), nullable=False)  # "Admin", "Manager", "Employee", etc.
    approver_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Rules Engine JSON Definition
    # e.g., {"conditions": [{"field": "amount", "operator": ">", "value": 10000}], "action": "ROUTE_TO_DIRECTOR"}
    rule_definition = Column(JSON, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")
    approver = relationship("User")
    approvals = relationship(
        "Approval",
        back_populates="step",
        cascade="all, delete-orphan"
    )
