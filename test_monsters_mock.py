import pytest
from fastapi.testclient import TestClient
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime
from home.ubuntu.monsters_api.main import app
from home.ubuntu.monsters_api.models import Monster, User, MonsterType
from home.ubuntu.monsters_api.auth import get_current_active_user
from home.ubuntu.monsters_api.database import get_db

# Fixtures únicas e utilitárias
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db():
    return Mock()

@pytest.fixture
def mock_user():
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_disabled = False
    return user

@pytest.fixture
def mock_monster():
    monster = Mock(spec=Monster)
    monster.id = 1
    monster.nome = "Dragão Vermelho"
    monster.raca = "Dragão"
    monster.peso = 500.5
    monster.altura = 3.2
    monster.tipo = MonsterType.FOGO
    monster.poder_ataque = 850
    monster.poder_defesa = 720
    monster.nivel = 45
    monster.experiencia = 12500
    monster.descricao = "Um poderoso dragão de fogo"
    monster.created_at = datetime.now()
    monster.updated_at = datetime.now()
    return monster

@pytest.fixture
def sample_monster_data():
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

# Override global para dependências
@pytest.fixture(autouse=True)
def override_dependencies(mock_db, mock_user):
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_active_user] = lambda: mock_user
    yield
    app.dependency_overrides = {}
# Mock de monstro
@pytest.fixture
def mock_monster():
    monster = Mock(spec=Monster)
    monster.id = 1
    monster.nome = "Dragão Vermelho"
    monster.raca = "Dragão"
    monster.peso = 500.5
    monster.altura = 3.2
    monster.tipo = MonsterType.FOGO
    monster.poder_ataque = 850
    monster.poder_defesa = 720
    monster.nivel = 45
    monster.experiencia = 12500
    monster.descricao = "Um poderoso dragão de fogo"
    monster.created_at = datetime.now()
    monster.updated_at = datetime.now()
    return monster

# Cliente de teste
@pytest.fixture
def client():
    return TestClient(app)

# Dados de exemplo para monstro
@pytest.fixture
def sample_monster_data():
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

class TestMonsters:
    """Testes para funcionalidades de monstros"""
    
    def test_get_monster_types(self, client):
        response = client.get("/monster-types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data and "total" in data
        assert "fogo" in data["types"]
    
    @patch('home.ubuntu.monsters_api.auth.jwt.decode', return_value={"sub": "testuser"})
    def test_create_monster_success(self, mock_jwt_decode, client, mock_db, mock_user, sample_monster_data):
        from home.ubuntu.monsters_api.models import Monster, MonsterType
        # Cria um objeto Monster real para simular o retorno após commit/refresh
        monster_obj = Monster(
            id=1,
            nome=sample_monster_data["nome"],
            raca=sample_monster_data["raca"],
            peso=sample_monster_data["peso"],
            altura=sample_monster_data["altura"],
            tipo=MonsterType.FOGO,
            poder_ataque=sample_monster_data["poder_ataque"],
            poder_defesa=sample_monster_data["poder_defesa"],
            nivel=sample_monster_data["nivel"],
            experiencia=sample_monster_data["experiencia"],
            descricao=sample_monster_data["descricao"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_db.add = Mock()
        mock_db.commit = Mock()
        # O refresh deve preencher o objeto passado
        def refresh_side_effect(obj):
            obj.id = monster_obj.id
            obj.created_at = monster_obj.created_at
            obj.updated_at = monster_obj.updated_at
        mock_db.refresh = Mock(side_effect=refresh_side_effect)
        response = client.post(
            "/monsters",
            headers={"Authorization": "Bearer qualquer_token"},
            json=sample_monster_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == sample_monster_data["nome"]
        assert data["raca"] == sample_monster_data["raca"]
        assert data["tipo"] == sample_monster_data["tipo"]
        assert "id" in data and "created_at" in data
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_create_monster_without_auth(self, client, sample_monster_data):
        app.dependency_overrides = {}
        response = client.post("/monsters", json=sample_monster_data)
        assert response.status_code == 401
    
    def test_create_monster_invalid_data(self, client, mock_user):
        invalid_monster = {
            "nome": "",
            "raca": "Dragão",
            "peso": -10,
            "altura": 3.2,
            "tipo": "fogo",
            "poder_ataque": 850,
            "poder_defesa": 720
        }
        response = client.post(
            "/monsters",
            headers={"Authorization": "Bearer qualquer_token"},
            json=invalid_monster
        )
        assert response.status_code == 422
    
    def test_get_monsters_empty(self, client, mock_db):
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.count.return_value = 0
        response = client.get("/monsters")
        assert response.status_code == 200
        data = response.json()
        assert data["monsters"] == []
        assert data["total"] == 0
    
    def test_get_monsters_with_data(self, client, mock_db, mock_monster):
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_monster]
        mock_db.query.return_value.count.return_value = 1
        response = client.get("/monsters")
        assert response.status_code == 200
        data = response.json()
        assert len(data["monsters"]) == 1
        assert data["total"] == 1
        assert data["monsters"][0]["nome"] == "Dragão Vermelho"
    
    def test_get_monster_by_id(self, client, mock_db, mock_monster):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_monster
        response = client.get("/monsters/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["nome"] == "Dragão Vermelho"
    
    def test_get_monster_not_found(self, client, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        response = client.get("/monsters/999")
        assert response.status_code == 404
        assert "Monstro não encontrado" in response.json()["detail"]
    
    def test_update_monster(self, client, mock_db, mock_monster):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_monster
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        update_data = {"nivel": 50, "experiencia": 20000}
        response = client.put(
            "/monsters/1",
            headers={"Authorization": "Bearer qualquer_token"},
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nivel"] == 50
        assert data["experiencia"] == 20000
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_monster_without_auth(self, client):
        app.dependency_overrides = {}
        update_data = {"nivel": 50}
        response = client.put("/monsters/1", json=update_data)
        assert response.status_code == 401
    
    def test_delete_monster(self, client, mock_db, mock_monster):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_monster
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        response = client.delete(
            "/monsters/1",
            headers={"Authorization": "Bearer qualquer_token"}
        )
        assert response.status_code == 200
        assert "deletado com sucesso" in response.json()["message"]
        mock_db.delete.assert_called_once_with(mock_monster)
        mock_db.commit.assert_called_once()
    
    def test_delete_monster_without_auth(self, client):
        app.dependency_overrides = {}
        response = client.delete("/monsters/1")
        assert response.status_code == 401
    
    def test_monsters_pagination(self, client, mock_db):
        from home.ubuntu.monsters_api.models import Monster, MonsterType
        mock_monsters = [
            Monster(
                id=i+1,
                nome=f"Monstro {i+1}",
                raca="Besta",
                peso=100.0 + i,
                altura=2.0 + i*0.1,
                tipo=MonsterType.FOGO,
                poder_ataque=100 + i,
                poder_defesa=80 + i,
                nivel=10 + i,
                experiencia=1000 + i*100,
                descricao=f"Descrição do Monstro {i+1}",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ) for i in range(10)
        ]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_monsters
        mock_db.query.return_value.count.return_value = 15
        response = client.get("/monsters?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["monsters"]) == 10
        assert data["total"] == 15
        assert data["page"] == 1
    
    def test_monsters_filter_by_type(self, client, mock_db):
        from home.ubuntu.monsters_api.models import Monster, MonsterType
        fire_monster = Monster(
            id=1,
            nome="Monstro de Fogo",
            raca="Dragão",
            peso=500.5,
            altura=3.2,
            tipo=MonsterType.FOGO,
            poder_ataque=850,
            poder_defesa=720,
            nivel=45,
            experiencia=12500,
            descricao="Um poderoso dragão de fogo",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [fire_monster]
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        response = client.get("/monsters?tipo=fogo")
        assert response.status_code == 200
        data = response.json()
        assert len(data["monsters"]) == 1
        assert data["monsters"][0]["tipo"] == "fogo"

