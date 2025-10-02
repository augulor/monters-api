from sqlalchemy.orm import Session
from home.ubuntu.monsters_api.database import SessionLocal, engine
from home.ubuntu.monsters_api.models import Base, User
from home.ubuntu.monsters_api.auth import get_password_hash

def create_tables():
    """Cria todas as tabelas no banco de dados"""
    Base.metadata.create_all(bind=engine)

def create_admin_user():
    """Cria o usuário administrador padrão se não existir"""
    db = SessionLocal()
    try:
        # Verifica se já existe um usuário admin
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@monsters-api.com",
                full_name="Administrador",
                hashed_password=get_password_hash("admin123"),
                is_disabled=False
            )
            db.add(admin_user)
            db.commit()
            print("Usuário administrador criado com sucesso!")
        else:
            print("Usuário administrador já existe.")
    finally:
        db.close()

if __name__ == "__main__":
    print("Criando tabelas...")
    create_tables()
    print("Criando usuário administrador...")
    create_admin_user()
    print("Inicialização concluída!")

