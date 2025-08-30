from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class MonsterType(enum.Enum):
    FOGO = "fogo"
    AGUA = "agua"
    TERRA = "terra"
    AR = "ar"
    ELETRICO = "eletrico"
    GELO = "gelo"
    VENENO = "veneno"
    PSIQUICO = "psiquico"
    SOMBRIO = "sombrio"
    LUZ = "luz"

class Monster(Base):
    __tablename__ = "monsters"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, index=True)
    raca = Column(String(50), nullable=False)
    peso = Column(Float, nullable=False)  # em kg
    altura = Column(Float, nullable=False)  # em metros
    tipo = Column(Enum(MonsterType), nullable=False)
    poder_ataque = Column(Integer, nullable=False)
    poder_defesa = Column(Integer, nullable=False)
    nivel = Column(Integer, default=1)
    experiencia = Column(Integer, default=0)
    descricao = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Monster(nome='{self.nome}', raca='{self.raca}', tipo='{self.tipo.value}')>"

