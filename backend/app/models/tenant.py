from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedUUIDModel


class Organization(TimeStampedUUIDModel):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    domain = Column(String(255), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    departments = relationship(
        "Department",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    users = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    workflows = relationship(
        "Workflow",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    templates = relationship(
        "WorkflowTemplate",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="organization",
        cascade="all, delete-orphan"
    )


class Department(TimeStampedUUIDModel):
    __tablename__ = "departments"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, index=True)

    # Relationships
    organization = relationship("Organization", back_populates="departments")
    users = relationship("User", back_populates="department")
