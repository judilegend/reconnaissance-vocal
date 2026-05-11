import os
import shutil
import uuid
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from datetime import timedelta
from typing import Dict, List, Optional, Any

from app.auth import (
    Token, 
    create_access_token, 
    get_current_active_user, 
    User, 
    fake_users_db, 
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.services.orchestrator import orchestrator

app = FastAPI(
    title="Speech Recognition API",
    description="Secure and Orchestrated Speech Recognition using Hugging Face Models",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"persistAuthorization": True}
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Speech Recognition API",
        version="1.0.0",
        description="Secure and Orchestrated Speech Recognition using Hugging Face Models",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/token",
                    "scopes": {}
                }
            }
        }
    }
    for path in openapi_schema["paths"]:
        if path == "/token":
            continue
        for method in openapi_schema["paths"][path]:
            if method.lower() != "options":
                openapi_schema["paths"][path][method]["security"] = [{"OAuth2PasswordBearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

class PerformanceMetrics(BaseModel):
    model_weight_millions: float
    precision_score: float
    z_score: float
    latency_ms: float
    precision_graph: str
    precision_history: List[float]

class TaskStatus(BaseModel):
    task_id: str
    model_type: str
    status: str
    result: Optional[str] = None
    streaming_tokens: Optional[List[str]] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    error: Optional[str] = None
    duration: Optional[float] = None

# CORS configuration
allow_origins = os.getenv("ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.post("/transcribe")
async def transcribe_audio(
    model_type: str = Form("wav2vec2"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload an audio file for transcription.
    Returns a task ID that can be used to track the progress.
    """
    if model_type not in ["wav2vec2", "whisper-tiny"]:
        raise HTTPException(status_code=400, detail="Invalid model type")

    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    task_id = await orchestrator.create_task(model_type, file_path)
    return {"task_id": task_id, "message": "Transcription task started"}

@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the status and result of a transcription task.
    Returns model performance metrics including precision, z-score, and a simple precision graph.
    """
    status_info = orchestrator.get_task_status(task_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Task not found")
    return status_info

@app.get("/tasks/{task_id}/metrics", response_model=PerformanceMetrics)
async def get_task_metrics(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get only the performance metrics for a completed transcription task.
    Returns precision score, z-score, latency and model weight.
    """
    status_info = orchestrator.get_task_status(task_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Task not found")
    metrics = status_info.get("performance_metrics")
    if not metrics:
        raise HTTPException(status_code=404, detail="Metrics not available yet")
    return metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
