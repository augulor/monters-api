from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
import logging
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
import uvicorn

from home.ubuntu.monsters_api.database import get_db
from home.ubuntu.monsters_api.models import Monster, MonsterType, User
from home.ubuntu.monsters_api.schemas import MonsterCreate, MonsterUpdate, MonsterResponse, MonsterList
from home.ubuntu.monsters_api.user_schemas import UserCreate, UserResponse, Token
from home.ubuntu.monsters_api.auth import authenticate_user, create_access_token, get_current_active_user, get_password_hash
from home.ubuntu.monsters_api.init_db import create_tables, create_admin_user

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Criar as tabelas e usuário admin ao iniciar
create_tables()
create_admin_user()

app = FastAPI(
    title="Monsters API",
    description="API CRUD para cadastro e gerenciamento de monstros com autenticação JWT",
    version="2.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tratamento global de erros
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Erro inesperado: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "Bem-vindo à Monsters API!",
        "version": "2.0.0",
        "docs": "/docs",
        "authentication": "JWT Bearer Token required for protected endpoints",
        "endpoints": {
            "autenticacao": "POST /token",
            "criar_usuario": "POST /users",
            "listar_monstros": "GET /monsters",
            "criar_monstro": "POST /monsters (protegido)",
            "obter_monstro": "GET /monsters/{monster_id}",
            "atualizar_monstro": "PUT /monsters/{monster_id} (protegido)",
            "deletar_monstro": "DELETE /monsters/{monster_id} (protegido)",
            "tipos_disponiveis": "GET /monster-types"
        }
    }

# Endpoints de Autenticação
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Endpoint para autenticação - retorna token JWT"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Criar um novo usuário"""
    # Verificar se usuário já existe
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Nome de usuário já existe")
    
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já está em uso")
    
    # Criar novo usuário
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Obter informações do usuário atual"""
    return current_user

# Endpoints de Monstros
@app.get("/monster-types")
async def get_monster_types():
    """Retorna todos os tipos de monstros disponíveis"""
    return {
        "types": [tipo.value for tipo in MonsterType],
        "total": len(MonsterType)
    }

@app.post("/monsters", response_model=MonsterResponse)
async def create_monster(
    monster: MonsterCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """Criar um novo monstro (requer autenticação)"""
    db_monster = Monster(**monster.model_dump())
    db.add(db_monster)
    db.commit()
    db.refresh(db_monster)
    logging.info(f"Monstro '{db_monster.nome}' criado pelo usuário '{current_user.username}'")
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Atualizar um monstro existente (requer autenticação)"""
    monster = db.query(Monster).filter(Monster.id == monster_id).first()
    if monster is None:
        raise HTTPException(status_code=404, detail="Monstro não encontrado")
    
    # Atualizar apenas os campos fornecidos
    update_data = monster_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(monster, field, value)
    
    db.commit()
    db.refresh(monster)
    logging.info(f"Monstro '{monster.nome}' atualizado pelo usuário '{current_user.username}'")
    return monster

@app.delete("/monsters/{monster_id}")
async def delete_monster(
    monster_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """Deletar um monstro (requer autenticação)"""
    monster = db.query(Monster).filter(Monster.id == monster_id).first()
    if monster is None:
        raise HTTPException(status_code=404, detail="Monstro não encontrado")
    
    monster_name = monster.nome
    db.delete(monster)
    db.commit()
    logging.info(f"Monstro '{monster_name}' deletado pelo usuário '{current_user.username}'")
    return {"message": f"Monstro '{monster_name}' deletado com sucesso"}

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
    logging.info("Iniciando Monsters API v2.0...")
    uvicorn.run(
        "main_updated:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )

