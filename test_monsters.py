import pytest
# Fixture de sessão do banco de dados para uso nos testes
@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from home.ubuntu.monsters_api.main import app
from home.ubuntu.monsters_api.database import Base, get_db
from home.ubuntu.monsters_api.models import User
from home.ubuntu.monsters_api.auth import get_password_hash

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


# Limpa a tabela de monstros antes de cada teste para garantir isolamento
@pytest.fixture(autouse=True)
def clear_monsters(db_session):
    db_session.execute(text('DELETE FROM monsters'))
    db_session.commit()


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
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# (Removido: duplicatas e fragmentos de fixtures já definidos corretamente acima)

@pytest.fixture
def auth_token(client, create_test_user):
    response = client.post(
        "/token",
        data={"username": create_test_user.username, "password": "testpass123"}
    )
    return response.json()["access_token"]

@pytest.fixture
def sample_monster():
    return {
        "nome": "Dragão Vermelho",
        "raca": "Dragão",
        "peso": 500.5,
        "altura": 3.2,
        "tipo": "fogo",
        "poder_ataque": 850,
        "poder_defesa": 720,
        "nivel": 45,
        "experiencia": 12500,
        "descricao": "Um poderoso dragão de fogo"
    }

def test_get_monster_types(client):
    """Teste de obtenção dos tipos de monstros"""
    response = client.get("/monster-types")
    assert response.status_code == 200
    data = response.json()
    assert "types" in data
    assert "total" in data
    assert len(data["types"]) == 10
    assert "fogo" in data["types"]

def test_create_monster_success(client, auth_token, sample_monster):
    """Teste de criação de monstro bem-sucedida"""
    response = client.post(
        "/monsters",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=sample_monster
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == sample_monster["nome"]
    assert data["raca"] == sample_monster["raca"]
    assert data["tipo"] == sample_monster["tipo"]
    assert "id" in data
    assert "created_at" in data

def test_create_monster_without_auth(client, sample_monster):
    """Teste de criação de monstro sem autenticação"""
    response = client.post("/monsters", json=sample_monster)
    assert response.status_code == 401

def test_create_monster_invalid_data(client, auth_token):
    """Teste de criação de monstro com dados inválidos"""
    invalid_monster = {
        "nome": "",  # Nome vazio
        "raca": "Dragão",
        "peso": -10,  # Peso negativo
        "altura": 3.2,
        "tipo": "fogo",
        "poder_ataque": 850,
        "poder_defesa": 720
    }
    response = client.post(
        "/monsters",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=invalid_monster
    )
    assert response.status_code == 422

def test_get_monsters_empty(client):
    """Teste de listagem de monstros quando não há nenhum"""
    response = client.get("/monsters")
    assert response.status_code == 200
    data = response.json()
    assert data["monsters"] == []
    assert data["total"] == 0

def test_get_monsters_with_data(client, auth_token, sample_monster):
    """Teste de listagem de monstros com dados"""
    # Primeiro, criar um monstro
    client.post(
        "/monsters",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=sample_monster
    )
    
    # Depois, listar monstros
    response = client.get("/monsters")
    assert response.status_code == 200
    data = response.json()
    assert len(data["monsters"]) == 1
    assert data["total"] == 1
    assert data["monsters"][0]["nome"] == sample_monster["nome"]

def test_get_monster_by_id(client, auth_token, sample_monster):
    """Teste de obtenção de monstro por ID"""
    # Criar monstro
    create_response = client.post(
        "/monsters",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=sample_monster
    )
    monster_id = create_response.json()["id"]
    
    # Obter monstro por ID
    response = client.get(f"/monsters/{monster_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == monster_id
    assert data["nome"] == sample_monster["nome"]

def test_get_monster_not_found(client):
    """Teste de obtenção de monstro inexistente"""
    response = client.get("/monsters/999")
    assert response.status_code == 404
    assert "Monstro não encontrado" in response.json()["detail"]

def test_update_monster(client, auth_token, sample_monster):
    """Teste de atualização de monstro"""
    # Criar monstro
    create_response = client.post(
        "/monsters",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=sample_monster
    )
    monster_id = create_response.json()["id"]
    
    # Atualizar monstro
    update_data = {"nivel": 50, "experiencia": 20000}
    response = client.put(
        f"/monsters/{monster_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nivel"] == 50
    assert data["experiencia"] == 20000
    assert data["nome"] == sample_monster["nome"]  # Outros campos não alterados

def test_update_monster_without_auth(client, auth_token, sample_monster):
    """Teste de atualização de monstro sem autenticação"""
    # Criar monstro
    create_response = client.post(
        "/monsters",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=sample_monster
    )
    monster_id = create_response.json()["id"]
    
    # Tentar atualizar sem autenticação
    update_data = {"nivel": 50}
    response = client.put(f"/monsters/{monster_id}", json=update_data)
    assert response.status_code == 401

def test_delete_monster(client, auth_token, sample_monster):
    """Teste de exclusão de monstro"""
    # Criar monstro
    create_response = client.post(
        "/monsters",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=sample_monster
    )
    monster_id = create_response.json()["id"]
    
    # Deletar monstro
    response = client.delete(
        f"/monsters/{monster_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert "deletado com sucesso" in response.json()["message"]
    
    # Verificar se foi realmente deletado
    get_response = client.get(f"/monsters/{monster_id}")
    assert get_response.status_code == 404

def test_delete_monster_without_auth(client, auth_token, sample_monster):
    """Teste de exclusão de monstro sem autenticação"""
    # Criar monstro
    create_response = client.post(
        "/monsters",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=sample_monster
    )
    monster_id = create_response.json()["id"]
    
    # Tentar deletar sem autenticação
    response = client.delete(f"/monsters/{monster_id}")
    assert response.status_code == 401

def test_get_monsters_stats(client, auth_token, sample_monster):
    """Teste de obtenção de estatísticas dos monstros"""
    # Criar alguns monstros
    client.post(
        "/monsters",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=sample_monster
    )
    
    water_monster = sample_monster.copy()
    water_monster["nome"] = "Leviatã"
    water_monster["tipo"] = "agua"
    water_monster["poder_ataque"] = 900
    
    client.post(
        "/monsters",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=water_monster
    )
    
    # Obter estatísticas
    response = client.get("/monsters/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_monsters"] == 2
    assert "monsters_by_type" in data
    assert data["monsters_by_type"]["fogo"] == 1
    assert data["monsters_by_type"]["agua"] == 1
    assert data["strongest_monster"] == "Leviatã"  # Maior poder de ataque

def test_monsters_pagination(client, auth_token, sample_monster):
    """Teste de paginação na listagem de monstros"""
    # Criar vários monstros
    for i in range(15):
        monster = sample_monster.copy()
        monster["nome"] = f"Monstro {i+1}"
        client.post(
            "/monsters",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=monster
        )
    
    # Testar primeira página
    response = client.get("/monsters?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["monsters"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1
    
    # Testar segunda página
    response = client.get("/monsters?skip=10&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["monsters"]) == 5
    assert data["total"] == 15
    assert data["page"] == 2

def test_monsters_filter_by_type(client, auth_token, sample_monster):
    """Teste de filtro por tipo de monstro"""
    # Criar monstros de diferentes tipos
    fire_monster = sample_monster.copy()
    fire_monster["nome"] = "Monstro de Fogo"
    fire_monster["tipo"] = "fogo"
    
    water_monster = sample_monster.copy()
    water_monster["nome"] = "Monstro de Água"
    water_monster["tipo"] = "agua"
    
    client.post("/monsters", headers={"Authorization": f"Bearer {auth_token}"}, json=fire_monster)
    client.post("/monsters", headers={"Authorization": f"Bearer {auth_token}"}, json=water_monster)
    
    # Filtrar por tipo fogo
    response = client.get("/monsters?tipo=fogo")
    assert response.status_code == 200
    data = response.json()
    assert len(data["monsters"]) == 1
    assert data["monsters"][0]["tipo"] == "fogo"

