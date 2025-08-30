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
cd monsters-api
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
python main.py
```

A API estará disponível em `http://localhost:8000`

### Documentação Interativa

Acesse `http://localhost:8000/docs` para ver a documentação interativa (Swagger UI).

## Endpoints da API

### Informações Gerais

- `GET /` - Informações da API
- `GET /monster-types` - Lista todos os tipos de monstros disponíveis

### CRUD de Monstros

- `POST /monsters` - Criar um novo monstro
- `GET /monsters` - Listar monstros (com paginação e filtros)
- `GET /monsters/{id}` - Obter um monstro específico
- `PUT /monsters/{id}` - Atualizar um monstro
- `DELETE /monsters/{id}` - Deletar um monstro

### Estatísticas

- `GET /monsters/stats/summary` - Estatísticas resumidas dos monstros

## Exemplos de Uso

### Criar um Monstro

```bash
curl -X POST "http://localhost:8000/monsters" \
     -H "Content-Type: application/json" \
     -d '{
       "nome": "Dragão Vermelho",
       "raca": "Dragão",
       "peso": 500.5,
       "altura": 3.2,
       "tipo": "fogo",
       "poder_ataque": 850,
       "poder_defesa": 720,
       "nivel": 45,
       "experiencia": 12500,
       "descricao": "Um poderoso dragão de fogo com escamas vermelhas brilhantes"
     }'
```

### Listar Monstros com Filtros

```bash
# Listar todos os monstros de fogo, página 1, 5 por página
curl "http://localhost:8000/monsters?tipo=fogo&skip=0&limit=5"

# Buscar monstros por nome
curl "http://localhost:8000/monsters?nome=dragão"
```

### Atualizar um Monstro

```bash
curl -X PUT "http://localhost:8000/monsters/1" \
     -H "Content-Type: application/json" \
     -d '{
       "nivel": 50,
       "experiencia": 15000
     }'
```

## Estrutura do Projeto

```
monsters-api/
├── main.py          # Aplicação principal FastAPI
├── models.py        # Modelos SQLAlchemy
├── schemas.py       # Schemas Pydantic
├── database.py      # Configuração do banco de dados
├── requirements.txt # Dependências
├── README.md        # Documentação
└── monsters.db      # Banco de dados SQLite (criado automaticamente)
```

## Tecnologias Utilizadas

- **FastAPI**: Framework web moderno e rápido para Python
- **SQLAlchemy**: ORM para Python
- **Pydantic**: Validação de dados usando type hints
- **Uvicorn**: Servidor ASGI para aplicações Python
- **SQLite**: Banco de dados (pode ser facilmente alterado para PostgreSQL, MySQL, etc.)

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

