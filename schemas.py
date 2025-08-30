from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from models import MonsterType

class MonsterBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100, description="Nome do monstro")
    raca: str = Field(..., min_length=1, max_length=50, description="Raça do monstro")
    peso: float = Field(..., gt=0, description="Peso do monstro em kg")
    altura: float = Field(..., gt=0, description="Altura do monstro em metros")
    tipo: MonsterType = Field(..., description="Tipo elemental do monstro")
    poder_ataque: int = Field(..., ge=1, le=999, description="Poder de ataque (1-999)")
    poder_defesa: int = Field(..., ge=1, le=999, description="Poder de defesa (1-999)")
    nivel: Optional[int] = Field(1, ge=1, le=100, description="Nível do monstro (1-100)")
    experiencia: Optional[int] = Field(0, ge=0, description="Pontos de experiência")
    descricao: Optional[str] = Field(None, max_length=500, description="Descrição do monstro")

class MonsterCreate(MonsterBase):
    pass

class MonsterUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    raca: Optional[str] = Field(None, min_length=1, max_length=50)
    peso: Optional[float] = Field(None, gt=0)
    altura: Optional[float] = Field(None, gt=0)
    tipo: Optional[MonsterType] = None
    poder_ataque: Optional[int] = Field(None, ge=1, le=999)
    poder_defesa: Optional[int] = Field(None, ge=1, le=999)
    nivel: Optional[int] = Field(None, ge=1, le=100)
    experiencia: Optional[int] = Field(None, ge=0)
    descricao: Optional[str] = Field(None, max_length=500)

class MonsterResponse(MonsterBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class MonsterList(BaseModel):
    monsters: list[MonsterResponse]
    total: int
    page: int
    per_page: int

