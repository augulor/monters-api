import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock
from home.ubuntu.monsters_api.main import app
from home.ubuntu.monsters_api.models import User, Monster, MonsterType
from home.ubuntu.monsters_api.auth import get_password_hash, create_access_token, verify_password
from home.ubuntu.monsters_api.database import get_db
from datetime import datetime

@pytest.fixture(scope="function")
def client():
    return TestClient(app)

class TestAuth:
    def test_password_hashing(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert not verify_password("wrongpassword", hashed)

    def test_create_access_token(self):
        data = {"sub": "testuser"}
        token = create_access_token(data)
        assert token and isinstance(token, str)

class TestMonsters:
    def test_get_monster_types(self, client):
        response = client.get("/monster-types")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data and "fogo" in data["types"]

    def test_get_monsters_empty(self, client):
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value.count.return_value = 0
        app.dependency_overrides[get_db] = lambda: mock_session
        response = client.get("/monsters")
        assert response.status_code == 200
        data = response.json()
        assert data["monsters"] == []
        app.dependency_overrides = {}

    def test_get_monsters_with_data(self, client):
        mock_session = Mock(spec=Session)
        mock_monster = Mock(spec=Monster)
        mock_monster.id = 1
        mock_monster.nome = "Dragão Vermelho"
        mock_monster.raca = "Dragão"
        mock_monster.peso = 500.5
        mock_monster.altura = 3.2
        mock_monster.tipo = MonsterType.FOGO
        mock_monster.poder_ataque = 850
        mock_monster.poder_defesa = 720
        mock_monster.nivel = 45
        mock_monster.experiencia = 12500
        mock_monster.descricao = "Um poderoso dragão de fogo"
        mock_monster.created_at = datetime.now()
        mock_monster.updated_at = datetime.now()
        mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_monster]
        mock_session.query.return_value.count.return_value = 1
        app.dependency_overrides[get_db] = lambda: mock_session
        response = client.get("/monsters")
        assert response.status_code == 200
        data = response.json()
        assert len(data["monsters"]) == 1
        assert data["monsters"][0]["nome"] == "Dragão Vermelho"
        app.dependency_overrides = {}

    def test_get_monster_by_id_found(self, client):
            mock_session = Mock(spec=Session)
            # Preenche todos os campos obrigatórios do Monster com valores válidos
            mock_monster = Monster(
                id=1,
                nome="Dragão Vermelho",
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
            mock_session.query.return_value.filter.return_value.first.return_value = mock_monster
            app.dependency_overrides[get_db] = lambda: mock_session
            response = client.get("/monsters/1")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["nome"] == "Dragão Vermelho"
            assert data["tipo"] == "fogo"
            app.dependency_overrides = {}

    def test_get_monster_by_id_not_found(self, client):
        mock_session = Mock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None
        app.dependency_overrides[get_db] = lambda: mock_session
        response = client.get("/monsters/999")
        assert response.status_code == 404
        app.dependency_overrides = {}

    def test_create_monster_with_auth(self, client):
            from home.ubuntu.monsters_api.auth import get_current_active_user
            mock_user = User(
                id=1,
                username="testuser",
                email="testuser@example.com",
                full_name="Test User",
                hashed_password="hashed",
                is_disabled=False,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            mock_session = Mock(spec=Session)
            mock_session.add = Mock()
            mock_session.commit = Mock()
            # O objeto Monster criado deve ser retornado por refresh
            def mock_refresh(monster):
                monster.id = 1
                monster.created_at = datetime.now()
                monster.updated_at = datetime.now()
            mock_session.refresh.side_effect = mock_refresh
            app.dependency_overrides[get_db] = lambda: mock_session
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            monster_data = {
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
            response = client.post(
                "/monsters",
                headers={"Authorization": "Bearer valid_token"},
                json=monster_data
            )
            assert response.status_code == 200
            data = response.json()
            assert data["nome"] == monster_data["nome"]
            assert data["tipo"] == "fogo"
            assert data["id"] == 1
            assert "created_at" in data
            app.dependency_overrides = {}

    def test_create_monster_without_auth(self, client):
            monster_data = {
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
            # Simula a ausência de autenticação, sem sobrescrever dependências
            response = client.post("/monsters", json=monster_data)
            assert response.status_code == 401

class TestUserManagement:

    def test_create_user_duplicate(self, client):
        mock_session = Mock(spec=Session)
        existing_user = Mock(spec=User)
        existing_user.username = "testuser"
        mock_session.query.return_value.filter.return_value.first.return_value = existing_user
        app.dependency_overrides[get_db] = lambda: mock_session
        user_data = {
            "username": "testuser",
            "email": "different@example.com",
            "full_name": "Different User",
            "password": "password123"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 400
        app.dependency_overrides = {}

    def test_login_success(self, client):
        mock_session = Mock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.hashed_password = get_password_hash("testpass123")
        mock_user.is_disabled = False
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        app.dependency_overrides[get_db] = lambda: mock_session
        response = client.post(
            "/token",
            data={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        app.dependency_overrides = {}

    def test_login_invalid_credentials(self, client):
        mock_session = Mock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.hashed_password = get_password_hash("testpass123")
        mock_user.is_disabled = False
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        app.dependency_overrides[get_db] = lambda: mock_session
        response = client.post(
            "/token",
            data={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        app.dependency_overrides = {}

    def test_get_current_user_success(self, client):
        from home.ubuntu.monsters_api.auth import get_current_active_user
        from datetime import datetime
        mock_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed",
            is_disabled=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        app.dependency_overrides = {}
    
    def test_create_monster_without_auth(self, client):
        """Teste de criação de monstro sem autenticação"""
        monster_data = {
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
        response = client.post("/monsters", json=monster_data)
        assert response.status_code == 401
    
    class TestMonsters:
        def test_get_monsters_empty(self, client):
            """Teste de listagem de monstros quando não há nenhum"""
            from home.ubuntu.monsters_api.database import get_db
            mock_session = Mock(spec=Session)
            mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
            mock_session.query.return_value.count.return_value = 0
            app.dependency_overrides[get_db] = lambda: mock_session
            response = client.get("/monsters")
            assert response.status_code == 200
            data = response.json()
            assert data["monsters"] == []
            assert data["total"] == 0
            app.dependency_overrides = {}

        def test_get_monsters_with_data(self, client):
            """Teste de listagem de monstros com dados"""
            from home.ubuntu.monsters_api.database import get_db
            from datetime import datetime
            mock_session = Mock(spec=Session)
            mock_monster = Mock(spec=Monster)
            mock_monster.id = 1
            mock_monster.nome = "Dragão Vermelho"
            mock_monster.raca = "Dragão"
            mock_monster.peso = 500.5
            mock_monster.altura = 3.2
            mock_monster.tipo = MonsterType.FOGO
            mock_monster.poder_ataque = 850
            mock_monster.poder_defesa = 720
            mock_monster.nivel = 45
            mock_monster.experiencia = 12500
            mock_monster.descricao = "Um poderoso dragão de fogo"
            mock_monster.created_at = datetime.now()
            mock_monster.updated_at = datetime.now()
            mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_monster]
            mock_session.query.return_value.count.return_value = 1
            app.dependency_overrides[get_db] = lambda: mock_session
            response = client.get("/monsters")
            assert response.status_code == 200
            data = response.json()
            assert len(data["monsters"]) == 1
            assert data["total"] == 1
            assert data["monsters"][0]["nome"] == "Dragão Vermelho"
            app.dependency_overrides = {}

        def test_get_monster_by_id_not_found(self, client):
            """Teste de obtenção de monstro inexistente"""
            mock_session = Mock(spec=Session)
            mock_session.query.return_value.filter.return_value.first.return_value = None
            app.dependency_overrides[get_db] = lambda: mock_session
            response = client.get("/monsters/999")
            assert response.status_code == 404
            assert "Monstro não encontrado" in response.json()["detail"]
    
        def test_get_monster_by_id_found(self, client):
            """Teste de obtenção de monstro por ID"""
            from home.ubuntu.monsters_api.database import get_db
            from datetime import datetime
            mock_session = Mock(spec=Session)
            mock_monster = Mock(spec=Monster)
            mock_monster.id = 1
            mock_monster.nome = "Dragão Vermelho"
            mock_monster.raca = "Dragão"
            mock_monster.peso = 500.5
            mock_monster.altura = 3.2
            mock_monster.tipo = MonsterType.FOGO
            mock_monster.poder_ataque = 850
            mock_monster.poder_defesa = 720
            mock_monster.nivel = 45
            mock_monster.experiencia = 12500
            mock_monster.descricao = "Um poderoso dragão de fogo"
            mock_monster.created_at = datetime.now()
            mock_monster.updated_at = datetime.now()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_monster
            app.dependency_overrides[get_db] = lambda: mock_session
            response = client.get("/monsters/1")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["nome"] == "Dragão Vermelho"
            app.dependency_overrides = {}

        def test_update_monster_without_auth(self, client):
            """Teste de atualização de monstro sem autenticação"""
            update_data = {"nivel": 50}
            response = client.put("/monsters/1", json=update_data)
            assert response.status_code == 401
    
        def test_delete_monster_without_auth(self, client):
            """Teste de exclusão de monstro sem autenticação"""
            response = client.delete("/monsters/1")
            assert response.status_code == 401
    
        def test_create_monster_with_auth(self, client):
            """Teste de criação de monstro com autenticação mockada"""
            from home.ubuntu.monsters_api.database import get_db
            from home.ubuntu.monsters_api.auth import get_current_active_user
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.username = "testuser"
            mock_session = Mock(spec=Session)
            mock_session.add = Mock()
            mock_session.commit = Mock()
            mock_session.refresh = Mock()
            def mock_refresh(monster):
                monster.id = 1
            mock_session.refresh.side_effect = mock_refresh
            app.dependency_overrides[get_db] = lambda: mock_session
            app.dependency_overrides[get_current_active_user] = lambda: mock_user
            monster_data = {
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
            response = client.post(
                "/monsters",
                headers={"Authorization": "Bearer valid_token"},
                json=monster_data
            )
            assert response.status_code == 200
            data = response.json()
            assert data["nome"] == monster_data["nome"]
            assert data["raca"] == monster_data["raca"]
            assert data["tipo"] == monster_data["tipo"]
            assert "id" in data
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once()
            app.dependency_overrides = {}

class TestUserManagement:
    """Testes para gerenciamento de usuários"""
    

    def test_create_user_duplicate(self, client):
        """Teste de criação de usuário duplicado"""
        mock_session = Mock(spec=Session)
        existing_user = Mock(spec=User)
        existing_user.username = "testuser"
        mock_session.query.return_value.filter.return_value.first.return_value = existing_user
        app.dependency_overrides[get_db] = lambda: mock_session
        user_data = {
            "username": "testuser",
            "email": "different@example.com",
            "full_name": "Different User",
            "password": "password123"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 400
        app.dependency_overrides = {}

    def test_login_success(self, client):
        """Teste de login bem-sucedido"""
        from home.ubuntu.monsters_api.database import get_db
        mock_session = Mock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.hashed_password = get_password_hash("testpass123")
        mock_user.is_disabled = False
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        app.dependency_overrides[get_db] = lambda: mock_session
        response = client.post(
            "/token",
            data={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        app.dependency_overrides = {}

    def test_login_invalid_credentials(self, client):
        """Teste de login com credenciais inválidas"""
        mock_session = Mock(spec=Session)
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.hashed_password = get_password_hash("testpass123")
        mock_user.is_disabled = False
        mock_session.query.return_value.filter.return_value.first.return_value = mock_user
        app.dependency_overrides[get_db] = lambda: mock_session
        response = client.post(
            "/token",
            data={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        app.dependency_overrides = {}

    def test_get_current_user_success(self, client):
        """Teste de obtenção do usuário atual"""
        from home.ubuntu.monsters_api.auth import get_current_active_user
        from home.ubuntu.monsters_api.models import User
        from datetime import datetime
        mock_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed",
            is_disabled=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        app.dependency_overrides = {}


