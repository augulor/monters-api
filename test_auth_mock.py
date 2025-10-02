# Imports necessários para o setup de testes
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from home.ubuntu.monsters_api.main import app
from home.ubuntu.monsters_api.database import Base
from home.ubuntu.monsters_api.models import User
from home.ubuntu.monsters_api.auth import get_password_hash, create_access_token, verify_password
# Banco de dados in-memory compartilhado
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def override_get_db(monkeypatch):
    def _get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    monkeypatch.setattr("home.ubuntu.monsters_api.database.get_db", _get_db)

@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def create_test_user(db_session):
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        is_disabled=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def user_token(create_test_user):
    token = create_access_token({"sub": create_test_user.username})
    return token

@pytest.fixture(scope="function")
def client():
    return TestClient(app)

class TestAuth:
    """Testes para funcionalidades de autenticação"""
    
    def test_password_hashing(self):
        """Teste de hash de senha"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False
    
    def test_create_access_token(self):
        """Teste de criação de token de acesso"""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0



