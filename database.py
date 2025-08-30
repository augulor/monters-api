from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Usando SQLite para simplicidade (pode ser alterado para PostgreSQL, MySQL, etc.)
SQLALCHEMY_DATABASE_URL = "sqlite:///./monsters.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Necessário apenas para SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Cria as tabelas no banco de dados"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency para obter sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

