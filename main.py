from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import uvicorn

from database import get_db, create_tables
from models import Monster, MonsterType
from schemas import MonsterCreate, MonsterUpdate, MonsterResponse, MonsterList

# Criar as tabelas ao iniciar
create_tables()

app = FastAPI(
    title="Monsters API",
    description="API CRUD para cadastro e gerenciamento de monstros",
    version="1.0.0"
)

# Configurar CORS para permitir acesso de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "Bem-vindo à Monsters API!",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "listar_monstros": "GET /monsters",
            "criar_monstro": "POST /monsters",
            "obter_monstro": "GET /monsters/{monster_id}",
            "atualizar_monstro": "PUT /monsters/{monster_id}",
            "deletar_monstro": "DELETE /monsters/{monster_id}",
            "tipos_disponiveis": "GET /monster-types"
        }
    }

@app.get("/monster-types")
async def get_monster_types():
    """Retorna todos os tipos de monstros disponíveis"""
    return {
        "types": [tipo.value for tipo in MonsterType],
        "total": len(MonsterType)
    }

@app.post("/monsters", response_model=MonsterResponse)
async def create_monster(monster: MonsterCreate, db: Session = Depends(get_db)):
    """Criar um novo monstro"""
    db_monster = Monster(**monster.dict())
    db.add(db_monster)
    db.commit()
    db.refresh(db_monster)
    return db_monster

@app.get("/monsters", response_model=MonsterList)
async def get_monsters(
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar"),
    tipo: Optional[MonsterType] = Query(None, description="Filtrar por tipo de monstro"),
    raca: Optional[str] = Query(None, description="Filtrar por raça"),
    nome: Optional[str] = Query(None, description="Buscar por nome (busca parcial)"),
    db: Session = Depends(get_db)
):
    """Listar monstros com paginação e filtros opcionais"""
    query = db.query(Monster)
    
    # Aplicar filtros
    if tipo:
        query = query.filter(Monster.tipo == tipo)
    if raca:
        query = query.filter(Monster.raca.ilike(f"%{raca}%"))
    if nome:
        query = query.filter(Monster.nome.ilike(f"%{nome}%"))
    
    # Contar total de registros
    total = query.count()
    
    # Aplicar paginação
    monsters = query.offset(skip).limit(limit).all()
    
    return MonsterList(
        monsters=monsters,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@app.get("/monsters/{monster_id}", response_model=MonsterResponse)
async def get_monster(monster_id: int, db: Session = Depends(get_db)):
    """Obter um monstro específico por ID"""
    monster = db.query(Monster).filter(Monster.id == monster_id).first()
    if monster is None:
        raise HTTPException(status_code=404, detail="Monstro não encontrado")
    return monster

@app.put("/monsters/{monster_id}", response_model=MonsterResponse)
async def update_monster(
    monster_id: int, 
    monster_update: MonsterUpdate, 
    db: Session = Depends(get_db)
):
    """Atualizar um monstro existente"""
    monster = db.query(Monster).filter(Monster.id == monster_id).first()
    if monster is None:
        raise HTTPException(status_code=404, detail="Monstro não encontrado")
    
    # Atualizar apenas os campos fornecidos
    update_data = monster_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(monster, field, value)
    
    db.commit()
    db.refresh(monster)
    return monster

@app.delete("/monsters/{monster_id}")
async def delete_monster(monster_id: int, db: Session = Depends(get_db)):
    """Deletar um monstro"""
    monster = db.query(Monster).filter(Monster.id == monster_id).first()
    if monster is None:
        raise HTTPException(status_code=404, detail="Monstro não encontrado")
    
    db.delete(monster)
    db.commit()
    return {"message": f"Monstro '{monster.nome}' deletado com sucesso"}

@app.get("/monsters/stats/summary")
async def get_monsters_stats(db: Session = Depends(get_db)):
    """Obter estatísticas resumidas dos monstros"""
    total_monsters = db.query(Monster).count()
    
    # Estatísticas por tipo
    type_stats = {}
    for tipo in MonsterType:
        count = db.query(Monster).filter(Monster.tipo == tipo).count()
        type_stats[tipo.value] = count
    
    # Monstro mais forte (maior poder de ataque)
    strongest = db.query(Monster).order_by(Monster.poder_ataque.desc()).first()
    
    # Monstro mais resistente (maior poder de defesa)
    most_defensive = db.query(Monster).order_by(Monster.poder_defesa.desc()).first()
    
    return {
        "total_monsters": total_monsters,
        "monsters_by_type": type_stats,
        "strongest_monster": strongest.nome if strongest else None,
        "most_defensive_monster": most_defensive.nome if most_defensive else None
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )

