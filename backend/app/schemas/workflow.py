from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.user import UserResponse


# =====================================================================
# Rules Engine Configuration Schemas
# =====================================================================

class StepConditionSchema(BaseModel):
    field: str = Field(..., description="Target attribute (e.g., 'amount', 'department_code')")
    operator: str = Field(..., description="Operators: '>', '<', '==', '!=', 'contains'")
    value: Any = Field(..., description="Comparison value")


class RuleDefinitionSchema(BaseModel):
    conditions: List[StepConditionSchema] = Field(default=[])
    action: str = Field(..., description="Actions: 'ROUTE_TO_ROLE', 'SKIP_STEP', 'AUTO_APPROVE'")
    action_value: Optional[str] = Field(None, description="Action parameter (e.g., target role 'FinanceDirector')")


# =====================================================================
# Workflow Step Schemas
# =====================================================================

class WorkflowStepCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    step_order: int = Field(..., ge=1)
    approver_role: str = Field("Manager", description="Role standard required for step (e.g., Manager, Admin)")
    approver_id: Optional[UUID] = None
    rule_definition: Optional[RuleDefinitionSchema] = None


class WorkflowStepResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    name: str
    step_order: int
    approver_role: str
    approver_id: Optional[UUID] = None
    rule_definition: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# Workflow Template (Marketplace Blueprint) Schemas
# =====================================================================

class WorkflowTemplateCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    category: str = Field("Procurement", description="Procurement, HR, IT, Compliance")
    structure: Dict[str, Any] = Field(..., description="Array blueprint steps and rules definitions")


class WorkflowTemplateResponse(BaseModel):
    id: UUID
    organization_id: Optional[UUID] = None
    name: str
    description: Optional[str]
    category: str
    structure: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# Workflow Transactional Schemas
# =====================================================================

class WorkflowCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_id: Optional[UUID] = None
    # If no template is selected, the user can manually define steps:
    steps: Optional[List[WorkflowStepCreate]] = None
    # Dynamic values payload parsed by rules engine (e.g., {"amount": 15000, "department_code": "FIN"})
    context_data: Optional[Dict[str, Any]] = Field(default={})


class WorkflowUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class WorkflowResponse(BaseModel):
    id: UUID
    organization_id: UUID
    creator_id: UUID
    template_id: Optional[UUID]
    title: str
    description: Optional[str]
    status: str
    current_step_id: Optional[UUID]
    version_id: int
    created_at: datetime
    updated_at: datetime
    steps: List[WorkflowStepResponse] = []
    creator: UserResponse

    class Config:
        from_attributes = True
