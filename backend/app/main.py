import os
import shutil
import uuid
from fastapi import FastAPI, Depends, File, UploadFile, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from typing import List, Optional

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
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
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

@app.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the status and result of a transcription task.
    """
    status_info = orchestrator.get_task_status(task_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Task not found")
    return status_info

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
