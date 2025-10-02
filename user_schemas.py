from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Nome de usuário")
    email: EmailStr = Field(..., description="Email do usuário")
    full_name: str = Field(..., min_length=1, max_length=100, description="Nome completo")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Senha do usuário (mínimo 6 caracteres)")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_disabled: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_disabled: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

