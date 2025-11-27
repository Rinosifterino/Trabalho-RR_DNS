import os
import json
import uuid
import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles  
from fastapi.responses import FileResponse
from pydantic import BaseModel
import redis
from fastapi.middleware.cors import CORSMiddleware

# --- Configuração ---
SERVER_HOSTNAME = os.environ.get("HOSTNAME", "Servidor_Local_Dev")
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
app = FastAPI(title="Backend Distribuído - Redes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- Funções de Usuário e Sessão (Redis) ---
# (Mantive suas funções auxiliares aqui, sem alterações)
def get_user_by_cpf(cpf: str) -> Optional[dict]:
    user_data_json = redis_client.get(f"user:{cpf}")
    if user_data_json:
        return json.loads(user_data_json)
    return None

def create_session(cpf: str) -> str:
    session_id = str(uuid.uuid4())
    session_data = {
        "user_cpf": cpf,
        "login_time": datetime.datetime.now().isoformat(),
        "server_name_on_login": SERVER_HOSTNAME
    }
    redis_client.set(f"session:{session_id}", json.dumps(session_data), ex=3600)
    return session_id

def get_session(session_id: str) -> Optional[dict]:
    session_data = redis_client.get(f"session:{session_id}")
    if session_data:
        return json.loads(session_data)
    return None

def delete_session(session_id: str):
    redis_client.delete(f"session:{session_id}")

# --- Endpoints da API (DEVEM VIR PRIMEIRO) ---

@app.get("/api/health")
def health_check():
    return {"status": "ok", "server": SERVER_HOSTNAME}

@app.post("/login", response_model=UserProfile)
def login(request: LoginRequest):
    cpf = request.cpf
    user_data = get_user_by_cpf(cpf)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CPF não encontrado ou inválido",
        )
    
    session_id = create_session(cpf)
    session_data = get_session(session_id)

    return UserProfile(
        nome=user_data["nome"],
        cpf=cpf,
        server_name=SERVER_HOSTNAME,
        session_id=session_id,
        login_time=session_data["login_time"]
    )

@app.get("/meu-perfil/{session_id}", response_model=UserProfile)
def meu_perfil(session_id: str):
    session_data = get_session(session_id)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão inválida ou expirada. Faça login novamente.",
        )

    user_cpf = session_data["user_cpf"]
    user_data = get_user_by_cpf(user_cpf)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dados do usuário não encontrados.",
        )

    return UserProfile(
        nome=user_data["nome"],
        cpf=user_cpf,
        server_name=SERVER_HOSTNAME,
        session_id=session_id,
        login_time=session_data["login_time"]
    )

@app.post("/logout/{session_id}")
def logout(session_id: str):
    delete_session(session_id)
    return {"message": "Logout realizado com sucesso."}


# --- Configuração de Arquivos Estáticos (DEVE SER O ÚLTIMO) ---

# 1. Monta a pasta de assets (CSS, JS, Imagens geradas pelo Vite)
# Certifique-se que a pasta backend/static/assets existe no container!
app.mount("/assets", StaticFiles(directory="static/assets"), name="static_assets")

# 2. Rota Catch-All para servir o React (SPA)
# Ela captura tudo que NÃO foi capturado pelas rotas acima.
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # Se o frontend tentar acessar uma API que não existe, retorna 404
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="Not Found")
    
    # Para qualquer outra rota (ex: /login-view, /dashboard), entrega o index.html
    # O React Router no navegador vai ler a URL e mostrar a tela certa.
    return FileResponse("static/index.html")