import uuid
import time
import asyncio
from typing import Dict, Any, Optional
from app.models.transcription import ModelFactory

class TranscriptionTask:
    def __init__(self, task_id: str, model_type: str):
        self.task_id = task_id
        self.model_type = model_type
        self.status = "PENDING"
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "model_type": self.model_type,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "duration": (self.end_time - self.start_time) if self.end_time and self.start_time else None
        }

class Orchestrator:
    def __init__(self):
        self.tasks: Dict[str, TranscriptionTask] = {}

    async def create_task(self, model_type: str, audio_path: str) -> str:
        task_id = str(uuid.uuid4())
        task = TranscriptionTask(task_id, model_type)
        self.tasks[task_id] = task
        
        # Start processing in the background
        asyncio.create_task(self._process_task(task, audio_path))
        
        return task_id

    async def _process_task(self, task: TranscriptionTask, audio_path: str):
        task.status = "PROCESSING"
        task.start_time = time.time()
        try:
            model = ModelFactory.get_model(task.model_type)
            # Run transcription in a thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(None, model.transcribe, audio_path)
            task.result = transcription
            task.status = "COMPLETED"
        except Exception as e:
            task.status = "FAILED"
            task.error = str(e)
        finally:
            task.end_time = time.time()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None

# Singleton instance
orchestrator = Orchestrator()
