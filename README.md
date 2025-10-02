# Monsters API

Uma API REST completa para cadastro e gerenciamento de monstros, construída com FastAPI e SQLAlchemy.

## Características

- **CRUD completo**: Criar, ler, atualizar e deletar monstros
- **Validação de dados**: Usando Pydantic para validação robusta
- **Paginação**: Listagem de monstros com paginação
- **Filtros**: Busca por nome, tipo e raça
- **Estatísticas**: Endpoint para estatísticas dos monstros
- **Documentação automática**: Swagger UI disponível em `/docs`
- **CORS habilitado**: Permite acesso de qualquer origem
- **Autenticação JWT**: Proteção de endpoints com JSON Web Tokens

## Estrutura de Dados

Cada monstro possui os seguintes atributos:

- **id**: Identificador único (gerado automaticamente)
- **nome**: Nome do monstro (obrigatório, 1-100 caracteres)
- **raca**: Raça do monstro (obrigatório, 1-50 caracteres)
- **peso**: Peso em kg (obrigatório, > 0)
- **altura**: Altura em metros (obrigatório, > 0)
- **tipo**: Tipo elemental (obrigatório, ver tipos disponíveis)
- **poder_ataque**: Poder de ataque (obrigatório, 1-999)
- **poder_defesa**: Poder de defesa (obrigatório, 1-999)
- **nivel**: Nível do monstro (opcional, padrão 1, 1-100)
- **experiencia**: Pontos de experiência (opcional, padrão 0)
- **descricao**: Descrição do monstro (opcional, máx 500 caracteres)
- **created_at**: Data de criação (gerado automaticamente)
- **updated_at**: Data da última atualização (gerado automaticamente)

## Tipos de Monstros Disponíveis

- fogo
- agua
- terra
- ar
- eletrico
- gelo
- veneno
- psiquico
- sombrio
- luz

## Instalação e Execução

### Pré-requisitos

- Python 3.7+
- pip

### Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd monters-api
```

2. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```
SECRET_KEY="sua_chave_secreta_aqui"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute a aplicação:
```bash
python main.py
```

A API estará disponível em `http://localhost:8000`

### Documentação Interativa

Acesse `http://localhost:8000/docs` para ver a documentação interativa (Swagger UI).

## Endpoints da API

### Autenticação

- `POST /token` - Obtém um token de acesso JWT. Requer `username` e `password` no corpo da requisição (form-data).

### Informações Gerais

- `GET /` - Informações da API
- `GET /monster-types` - Lista todos os tipos de monstros disponíveis

### CRUD de Monstros (Protegidos por Autenticação)

Os endpoints abaixo requerem um token JWT válido no cabeçalho `Authorization: Bearer <token>`.

- `POST /monsters` - Criar um novo monstro
- `GET /monsters` - Listar monstros (com paginação e filtros)
- `GET /monsters/{id}` - Obter um monstro específico
- `PUT /monsters/{id}` - Atualizar um monstro
- `DELETE /monsters/{id}` - Deletar um monstro

### Estatísticas

- `GET /monsters/stats/summary` - Estatísticas resumidas dos monstros

## Exemplos de Uso

### 1. Obter um Token de Acesso

Use o usuário `admin` e senha `admin123` (apenas para desenvolvimento):

```bash
curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=admin123"
```

Isso retornará um JSON com o `access_token` e `token_type`.

### 2. Criar um Monstro (com Autenticação)

Substitua `<YOUR_ACCESS_TOKEN>` pelo token obtido no passo anterior.

```bash
curl -X POST "http://localhost:8000/monsters" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
     -d 
```

