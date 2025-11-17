# Este é um projeto completo de API RESTful para um CRM básico.
# Você pode executar este arquivo Python e ter uma API funcionando.

# Passo 1: Instalar as bibliotecas
# Abra seu terminal e instale o que precisamos:
# pip install fastapi uvicorn sqlmodel

import uvicorn  # Para rodar o servidor da API
from typing import List, Optional, Annotated
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlmodel import Field, SQLModel, Session, create_engine, select
from contextlib import asynccontextmanager # Importação ADICIONADA


# --- PASSO 1: DEFINIR O BANCO DE DADOS (com SQLModel) ---
# Aqui é o "passo a passo" do banco de dados que você pediu.
# Em vez de escrever SQL (CREATE TABLE...), nós descrevemos nossos
# dados como classes Python.

class ClienteBase(SQLModel):
    # Campos que o usuário vai nos enviar
    nome: str = Field(index=True) # "index=True" acelera as buscas por nome
    email: str = Field(unique=True, index=True) # E-mail deve ser único
    telefone: Optional[str] = None
    empresa: Optional[str] = None

class Cliente(ClienteBase, table=True):
    # A classe que representa a tabela no banco de dados
    # Ela herda os campos da ClienteBase e adiciona o 'id'
    id: Optional[int] = Field(default=None, primary_key=True)

class ClienteRead(ClienteBase):
    # Campos que vamos retornar para o usuário (incluindo o id)
    id: int

# --- FIM DO PASSO 1: BANCO DE DADOS ---


# --- PASSO 2: CONFIGURAR O BANCO E A SESSÃO ---

# O "caminho" para o nosso banco de dados.
# "sqlite:///crm.db" significa que ele vai criar um arquivo
# chamado 'crm.db' na mesma pasta deste script.
sqlite_file_name = "crm.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# O "engine" é o "motor" que conecta o SQLModel ao banco de dados.
engine = create_engine(sqlite_url, echo=True) # echo=True mostra os comandos SQL no terminal

def create_db_and_tables():
    # Esta função cria as tabelas no banco de dados
    # (baseado nas classes que definimos, como 'Cliente')
    SQLModel.metadata.create_all(engine)

# "Sessão" é o termo para uma "conversa" com o banco de dados.
# Esta função nos dá uma sessão para trabalhar.
def get_session():
    with Session(engine) as session:
        yield session

# --- FIM DO PASSO 2: CONFIGURAÇÃO DO BANCO ---


# --- PASSO 3: CRIAR A API (com FastAPI) ---

# Bloco de código NOVO para corrigir o @app.on_event("startup")
# Este é o novo jeito (lifespan) de rodar um código quando a API inicia
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que roda ANTES da API começar a aceitar conexões
    print("Iniciando a API e criando tabelas no banco de dados...")
    create_db_and_tables()
    yield
    # Código que roda DEPOIS que a API é desligada (se necessário)
    print("Desligando a API...")


# Cria a aplicação FastAPI
app = FastAPI(
    title="API do Meu CRM Básico",
    description="Um projeto de API RESTful com Python, FastAPI e SQLModel.",
    lifespan=lifespan  # Diz ao FastAPI para usar nosso lifespan
)

# Bloco de código REMOVIDO
# @app.on_event("startup") # Quando a API iniciar...
# def on_startup():
#     create_db_and_tables() # ...crie o banco de dados e tabelas

# ---
# Endpoint para CRIAR um novo cliente (Create)
# ---
@app.post("/clientes/", response_model=ClienteRead, tags=["Clientes"])
def create_cliente(
    *, 
    session: Annotated[Session, Depends(get_session)],
    cliente: ClienteBase
):
    """
    Cria um novo cliente no banco de dados.
    """
    # Verifica se o cliente já existe (pelo e-mail)
    db_cliente_existente = session.exec(
        select(Cliente).where(Cliente.email == cliente.email)
    ).first()
    
    if db_cliente_existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    # Cria uma instância do modelo 'Cliente' (a tabela)
    db_cliente = Cliente.model_validate(cliente)
    
    # Adiciona ao banco
    session.add(db_cliente)
    session.commit()
    session.refresh(db_cliente) # Atualiza o 'db_cliente' com o ID do banco
    
    return db_cliente

# ---
# Endpoint para LER todos os clientes (Read)
# ---
@app.get("/clientes/", response_model=List[ClienteRead], tags=["Clientes"])
def read_clientes(
    *,
    session: Annotated[Session, Depends(get_session)],
    offset: int = 0, # Para paginação (pular os N primeiros)
    limit: int = Query(default=10, le=100) # 'le=100' limita a 100 por página
):
    """
    Lê uma lista de clientes do banco de dados, com paginação.
    """
    # Cria a consulta (query)
    query = select(Cliente).offset(offset).limit(limit)
    
    # Executa a consulta
    clientes = session.exec(query).all()
    
    return clientes

# ---
# Endpoint para LER um cliente específico (Read)
# ---
@app.get("/clientes/{cliente_id}", response_model=ClienteRead, tags=["Clientes"])
def read_cliente(
    *, 
    session: Annotated[Session, Depends(get_session)], 
    cliente_id: int
):
    """
    Lê um cliente específico pelo seu ID.
    """
    # Busca o cliente pelo ID
    db_cliente = session.get(Cliente, cliente_id)
    
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    return db_cliente

# ---
# Endpoint para ATUALIZAR um cliente (Update)
# ---
@app.patch("/clientes/{cliente_id}", response_model=ClienteRead, tags=["Clientes"])
def update_cliente(
    *,
    session: Annotated[Session, Depends(get_session)],
    cliente_id: int,
    cliente_update: ClienteBase # Os dados que o usuário quer mudar
):
    """
    Atualiza um cliente existente no banco de dados.
    """
    db_cliente = session.get(Cliente, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Pega os dados do 'cliente_update' e converte para um dicionário
    # exclude_unset=True garante que só vamos atualizar os campos
    # que o usuário realmente enviou (ex: só o telefone)
    update_data = cliente_update.model_dump(exclude_unset=True)

    # Atualiza o objeto 'db_cliente'
    db_cliente.sqlmodel_update(update_data)
    
    # Salva no banco
    session.add(db_cliente)
    session.commit()
    session.refresh(db_cliente)
    
    return db_cliente

# ---
# Endpoint para DELETAR um cliente (Delete)
# ---
@app.delete("/clientes/{cliente_id}", tags=["Clientes"])
def delete_cliente(
    *,
    session: Annotated[Session, Depends(get_session)],
    cliente_id: int
):
    """
    Deleta um cliente do banco de dados.
    """
    db_cliente = session.get(Cliente, cliente_id)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    session.delete(db_cliente)
    session.commit()
    
    # Retorna uma mensagem de sucesso
    return {"message": "Cliente deletado com sucesso"}
