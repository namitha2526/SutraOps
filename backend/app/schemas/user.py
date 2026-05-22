from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


# =====================================================================
# Department Schemas
# =====================================================================

class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=50)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    id: UUID
    organization_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# User Schemas
# =====================================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: str = Field("Employee", description="Employee, Manager, Admin")
    department_id: Optional[UUID] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    organization_id: UUID
    is_active: bool
    created_at: datetime
    department: Optional[DepartmentResponse] = None

    class Config:
        from_attributes = True
