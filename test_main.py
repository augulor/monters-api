import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_monster_types():
    response = client.get("/monster-types")
    assert response.status_code == 200
    assert "types" in response.json()

def test_create_monster_unauth():
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
