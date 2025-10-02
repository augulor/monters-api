
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from home.ubuntu.monsters_api.main import app
from home.ubuntu.monsters_api.database import Base
from home.ubuntu.monsters_api.models import User
from home.ubuntu.monsters_api.auth import get_password_hash, create_access_token

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
    import uuid
    unique_username = f"testuser_{uuid.uuid4()}"
    unique_email = f"{unique_username}@example.com"
    user = User(
        username=unique_username,
        email=unique_email,
        full_name="Test User",
        hashed_password=get_password_hash("testpassword"),
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


import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="function")
def client():
    return TestClient(app)

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_monster_types(client):
    response = client.get("/monster-types")
    assert response.status_code == 200
    assert "types" in response.json()

def test_create_monster_unauth(client):
    # Sem token, deve retornar 401
    monster = {
        "nome": "Teste",
        "raca": "Teste",
        "peso": 10.0,
        "altura": 1.5,
        "tipo": "fogo",
        "poder_ataque": 100,
        "poder_defesa": 100
    }
    response = client.post("/monsters", json=monster)
    assert response.status_code == 401
