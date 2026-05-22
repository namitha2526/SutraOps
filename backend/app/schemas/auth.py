from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


from typing import Optional

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    org_id: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OrgRegisterRequest(BaseModel):
    organization_name: str = Field(..., min_length=2, max_length=100)
    domain: str = Field(..., min_length=3, max_length=100)  # e.g., "acme.com"
    admin_name: str = Field(..., min_length=2, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6, max_length=100)
