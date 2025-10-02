
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


import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="function")
def client():
    return TestClient(app)


class TestBasicAPI:
    """Testes básicos para a API de monstros"""

    def test_get_monster_types(self, client):
        """Teste básico para obter tipos de monstros"""
        response = client.get("/monster-types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert "total" in data
        assert isinstance(data["types"], list)
        assert data["total"] > 0
    
    def test_get_monsters_list(self, client):
        """Teste básico para listar monstros"""
        response = client.get("/monsters")
        assert response.status_code == 200
        data = response.json()
        assert "monsters" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert isinstance(data["monsters"], list)
    
    def test_get_monster_by_id_not_found(self, client):
        """Teste básico para buscar monstro inexistente"""
        response = client.get("/monsters/99999")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_post_monster_without_auth(self, client):
        """Teste básico para criar monstro sem autenticação"""
        monster_data = {
            "nome": "Dragão de Teste",
            "raca": "Dragão",
            "peso": 100.0,
            "altura": 2.0,
            "tipo": "fogo",
            "poder_ataque": 50,
            "poder_defesa": 40,
            "nivel": 1,
            "experiencia": 0,
            "descricao": "Um dragão para teste"
        }
        response = client.post("/monsters", json=monster_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_put_monster_without_auth(self, client):
        """Teste básico para atualizar monstro sem autenticação"""
        update_data = {"nivel": 10}
        response = client.put("/monsters/1", json=update_data)
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_delete_monster_without_auth(self, client):
        """Teste básico para deletar monstro sem autenticação"""
        response = client.delete("/monsters/1")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_monsters_stats(self, client):
        """Teste básico para obter estatísticas dos monstros"""
        response = client.get("/monsters/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_monsters" in data
        assert "monsters_by_type" in data
        assert isinstance(data["total_monsters"], int)
        assert isinstance(data["monsters_by_type"], dict)

class TestUserAPI:
    """Testes básicos para a API de usuários"""
    
    def test_post_create_user_invalid_data(self, client):
        """Teste básico para criar usuário com dados inválidos"""
        invalid_user = {
            "username": "",  # Username vazio
            "email": "invalid-email",  # Email inválido
            "password": "123"  # Senha muito curta
        }
        response = client.post("/users", json=invalid_user)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_post_login_invalid_credentials(self, client):
        """Teste básico para login com credenciais inválidas"""
        response = client.post(
            "/token",
            data={"username": "usuario_inexistente", "password": "senha_errada"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_current_user_without_token(self, client):
        """Teste básico para obter usuário atual sem token"""
        response = client.get("/users/me")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_get_current_user_invalid_token(self, client):
        """Teste básico para obter usuário atual com token inválido"""
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer token_invalido"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

class TestValidation:
    """Testes básicos para validação de dados"""
    
    def test_post_monster_invalid_tipo(self, client):
        """Teste básico para criar monstro com tipo inválido"""
        monster_data = {
            "nome": "Monstro Teste",
            "raca": "Teste",
            "peso": 100.0,
            "altura": 2.0,
            "tipo": "tipo_inexistente",  # Tipo inválido
            "poder_ataque": 50,
            "poder_defesa": 40
        }
        response = client.post("/monsters", json=monster_data)
        # Pode retornar 401 (sem auth) ou 422 (dados inválidos)
        assert response.status_code in [401, 422]
    
    def test_post_monster_negative_values(self, client):
        """Teste básico para criar monstro com valores negativos"""
        monster_data = {
            "nome": "Monstro Teste",
            "raca": "Teste",
            "peso": -10.0,  # Peso negativo
            "altura": -2.0,  # Altura negativa
            "tipo": "fogo",
            "poder_ataque": -50,  # Poder negativo
            "poder_defesa": -40   # Poder negativo
        }
        response = client.post("/monsters", json=monster_data)
        # Pode retornar 401 (sem auth) ou 422 (dados inválidos)
        assert response.status_code in [401, 422]

class TestPagination:
    """Testes básicos para paginação"""
    
    def test_get_monsters_with_pagination(self, client):
        """Teste básico para paginação na listagem de monstros"""
        response = client.get("/monsters?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "monsters" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert data["per_page"] == 5
        assert data["page"] == 1
    
    def test_get_monsters_filter_by_type(self, client):
        """Teste básico para filtro por tipo"""
        response = client.get("/monsters?tipo=fogo")
        assert response.status_code == 200
        data = response.json()
        assert "monsters" in data
        assert isinstance(data["monsters"], list)

if __name__ == "__main__":
    # Executar testes básicos
    pytest.main([__file__, "-v"])

