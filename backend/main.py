import os
import json
import uuid
import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import redis

# --- Configuração ---
# O nome do servidor (hostname) é crucial para o trabalho.
SERVER_HOSTNAME = os.environ.get("HOSTNAME", "Servidor_Local_Dev")

# Configuração do Redis (Banco de Dados de Usuários e Sessão)
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# --- Modelos de Dados ---
class LoginRequest(BaseModel):
    cpf: str

class UserProfile(BaseModel):
    nome: str
    cpf: str
    server_name: str
    session_id: str
    login_time: str

# --- Aplicação FastAPI ---
app = FastAPI(title="Backend Distribuído - Engenharia")

# --- Funções de Usuário (Redis) ---

def get_user_by_cpf(cpf: str) -> Optional[dict]:
    """Busca um usuário no Redis pelo CPF."""
    # A chave para os dados do usuário é prefixada com 'user:'
    user_data_json = redis_client.get(f"user:{cpf}")
    if user_data_json:
        return json.loads(user_data_json)
    return None

# --- Funções de Sessão (Redis) ---

def create_session(cpf: str) -> str:
    """Cria uma sessão no Redis e retorna o ID da sessão."""
    session_id = str(uuid.uuid4())
    session_data = {
        "user_cpf": cpf,
        "login_time": datetime.datetime.now().isoformat(),
        "server_name_on_login": SERVER_HOSTNAME # Apenas para debug
    }
    # A chave para a sessão é prefixada com 'session:'
    # A sessão expira em 1 hora (3600 segundos)
    redis_client.set(f"session:{session_id}", json.dumps(session_data), ex=3600)
    return session_id

def get_session(session_id: str) -> Optional[dict]:
    """Busca a sessão no Redis."""
    session_data = redis_client.get(f"session:{session_id}")
    if session_data:
        return json.loads(session_data)
    return None

def delete_session(session_id: str):
    """Deleta a sessão no Redis."""
    redis_client.delete(f"session:{session_id}")

# --- Endpoints da API ---

@app.get("/")
def read_root():
    """Endpoint de saúde e identificação do servidor."""
    return {"message": "Backend rodando", "server": SERVER_HOSTNAME}

@app.post("/login", response_model=UserProfile)
def login(request: LoginRequest):
    """
    Realiza o login. Se for bem-sucedido, cria uma sessão centralizada
    e retorna os dados do usuário e o ID da sessão.
    """
    cpf = request.cpf
    user_data = get_user_by_cpf(cpf)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF não encontrado ou inválido",
        )

    # 1. Autenticação bem-sucedida (simulada, apenas checando a existência do CPF)
    
    # 2. Criação da Sessão Centralizada (Chave para o Desafio)
    session_id = create_session(cpf)
    session_data = get_session(session_id)

    # 3. Retorna os dados do perfil e o ID da sessão
    return UserProfile(
        nome=user_data["nome"],
        cpf=cpf,
        server_name=SERVER_HOSTNAME, # Nome do servidor que processou o login
        session_id=session_id,
        login_time=session_data["login_time"]
    )

@app.get("/meu-perfil/{session_id}", response_model=UserProfile)
def meu_perfil(session_id: str):
    """
    Endpoint protegido. Verifica a sessão centralizada e retorna os dados
    do usuário e o nome do servidor atual.
    """
    session_data = get_session(session_id)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada. Faça login novamente.",
        )

    user_cpf = session_data["user_cpf"]
    user_data = get_user_by_cpf(user_cpf)

    if not user_data:
        # Isso não deve acontecer se o banco de dados de usuários estiver correto
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dados do usuário não encontrados.",
        )

    # O sucesso aqui demonstra que a sessão é compartilhada.
    return UserProfile(
        nome=user_data["nome"],
        cpf=user_cpf,
        server_name=SERVER_HOSTNAME, # Nome do servidor que processou a requisição AGORA
        session_id=session_id,
        login_time=session_data["login_time"]
    )

@app.post("/logout/{session_id}")
def logout(session_id: str):
    """Invalida a sessão centralizada."""
    delete_session(session_id)
    return {"message": "Logout realizado com sucesso."}

