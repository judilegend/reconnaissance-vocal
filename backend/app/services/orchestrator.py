import uuid
import time
import asyncio
from typing import Dict, Any, Optional, List
from app.models.transcription import ModelFactory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptionTask:
    def __init__(self, task_id: str, model_type: str):
        self.task_id = task_id
        self.model_type = model_type
        self.status = "PENDING"
        self.result = None
        self.streaming_tokens: List[str] = []
        self.performance_metrics: Optional[Dict[str, Any]] = None
        self.error = None
        self.start_time = None
        self.end_time = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "model_type": self.model_type,
            "status": self.status,
            "result": self.result,
            "streaming_tokens": self.streaming_tokens,
            "performance_metrics": self.performance_metrics,
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

        logger.info(f"Created task {task_id} with model {model_type}")

        # Start processing in the background
        asyncio.create_task(self._process_task(task, audio_path))

        return task_id

    async def _process_task(self, task: TranscriptionTask, audio_path: str):
        task.status = "PROCESSING"
        task.start_time = time.time()
        logger.info(f"Starting processing for task {task.task_id}")

        try:
            model = ModelFactory.get_model(task.model_type)

            # Use streaming transcription and collect metrics
            start = time.time()
            result = await asyncio.get_event_loop().run_in_executor(None, model.transcribe_streaming, audio_path)
            elapsed_ms = (time.time() - start) * 1000

            if isinstance(result, tuple):
                tokens, metrics = result
            else:
                tokens = result
                metrics = {}

            metrics["latency_ms"] = round(elapsed_ms, 2)

            # Simulate streaming by adding tokens progressively
            task.streaming_tokens = []
            for token in tokens:
                task.streaming_tokens.append(token)
                await asyncio.sleep(0.1)  # Simulate delay between tokens

            # Combine tokens into final result
            task.result = " ".join(task.streaming_tokens).strip()
            task.performance_metrics = metrics
            task.status = "COMPLETED"
            logger.info(f"Task {task.task_id} completed: {task.result}")

        except Exception as e:
            task.status = "FAILED"
            task.error = str(e)
            logger.error(f"Task {task.task_id} failed: {e}")
        finally:
            task.end_time = time.time()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None

# Singleton instance
orchestrator = Orchestrator()
