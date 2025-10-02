
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from home.ubuntu.monsters_api.main import app
from home.ubuntu.monsters_api.database import Base, get_db
from home.ubuntu.monsters_api.models import User
from home.ubuntu.monsters_api.auth import get_password_hash, create_access_token

# Engine e Session compartilhados para todos os testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Cria as tabelas uma vez por sessão de teste
@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# Fixture de sessão de banco compartilhada
@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fixture de client que faz override do get_db para usar a mesma sessão
@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# Criação de usuário de teste usando a mesma sessão do client
@pytest.fixture(scope="function")
def create_test_user(db_session):
    import uuid
    unique_username = f"testuser_{uuid.uuid4()}"
    unique_email = f"{unique_username}@example.com"
    user = User(
        username=unique_username,
        email=unique_email,
        full_name="Test User",
        hashed_password=get_password_hash("testpass123"),
        is_disabled=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def test_create_user(client):
    """Teste de criação de usuário"""
    import uuid
    unique_username = f"newuser_{uuid.uuid4()}"
    unique_email = f"{unique_username}@example.com"
    response = client.post(
        "/users",
        json={
            "username": unique_username,
            "email": unique_email,
            "full_name": "New User",
            "password": "newpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == unique_username
    assert data["email"] == unique_email
    assert "hashed_password" not in data

def test_create_duplicate_user(client, create_test_user):
    """Teste de criação de usuário duplicado"""
    response = client.post(
        "/users",
        json={
            "username": create_test_user.username,
            "email": "different@example.com",
            "full_name": "Different User",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert (
        "Nome de usuário já existe" in detail or
        "Email já está em uso" in detail
    )

def test_login_success(client, create_test_user):
    """Teste de login bem-sucedido"""
    response = client.post(
        "/token",
        data={"username": create_test_user.username, "password": "testpass123"}
    )
    # Se falhar, mostrar o motivo
    if response.status_code != 200:
        print("Login response:", response.json())
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client, create_test_user):
    """Teste de login com credenciais inválidas"""
    response = client.post(
        "/token",
        data={"username": create_test_user.username, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Usuário ou senha incorretos" in response.json()["detail"]

def test_get_current_user(client, create_test_user):
    """Teste de obtenção do usuário atual"""
    # Primeiro, fazer login para obter o token
    login_response = client.post(
        "/token",
        data={"username": create_test_user.username, "password": "testpass123"}
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
    token = login_response.json()["access_token"]
    # Usar o token para acessar informações do usuário
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == create_test_user.username
    assert data["email"] == create_test_user.email

def test_access_protected_endpoint_without_token(client):
    """Teste de acesso a endpoint protegido sem token"""
    response = client.post(
        "/monsters",
        json={
            "nome": "Test Monster",
            "raca": "Test Race",
            "peso": 100.0,
            "altura": 2.0,
            "tipo": "fogo",
            "poder_ataque": 50,
            "poder_defesa": 40
        }
    )
    assert response.status_code == 401

def test_access_protected_endpoint_with_invalid_token(client):
    """Teste de acesso a endpoint protegido com token inválido"""
    response = client.post(
        "/monsters",
        headers={"Authorization": "Bearer invalid_token"},
        json={
            "nome": "Test Monster",
            "raca": "Test Race",
            "peso": 100.0,
            "altura": 2.0,
            "tipo": "fogo",
            "poder_ataque": 50,
            "poder_defesa": 40
        }
    )
    assert response.status_code == 401

