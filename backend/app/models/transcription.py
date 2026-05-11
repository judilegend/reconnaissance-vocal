import time
import torch
import librosa
import numpy as np
from transformers import pipeline, Wav2Vec2ForCTC, Wav2Vec2Processor
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioPreprocessor:
    @staticmethod
    def preprocess_audio(audio_path: str, max_duration: float = 15.0) -> np.ndarray:
        """
        Preprocess audio: load, trim to max_duration, reduce noise, normalize.
        """
        logger.info(f"Loading audio from {audio_path}")
        speech, sample_rate = librosa.load(audio_path, sr=16000)

        # Trim to max_duration seconds
        max_samples = int(max_duration * sample_rate)
        if len(speech) > max_samples:
            speech = speech[:max_samples]
            logger.info(f"Trimmed audio to {max_duration}s")

        # Trim silence at beginning/end to avoid transcribing non-speech noise
        speech, _ = librosa.effects.trim(speech, top_db=20)

        # Normalize audio amplitude
        speech = librosa.util.normalize(speech)

        logger.info(f"Audio preprocessing completed. Shape: {speech.shape}")
        return speech

class TranscriptionModel:
    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError

    def transcribe_streaming(self, audio_path: str) -> List[str]:
        """
        Return transcription tokens progressively.
        """
        raise NotImplementedError

class Wav2Vec2Model(TranscriptionModel):
    def __init__(self):
        self.model_name = "facebook/wav2vec2-base-960h"
        self.processor = Wav2Vec2Processor.from_pretrained(self.model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)
        self.preprocessor = AudioPreprocessor()
        self.model_weight_millions = sum(p.numel() for p in self.model.parameters()) / 1e6

    def transcribe(self, audio_path: str) -> str:
        logger.info("Starting Wav2Vec2 transcription")
        speech = self.preprocessor.preprocess_audio(audio_path)

        # Process audio
        input_values = self.processor(speech, return_tensors="pt", sampling_rate=16000).input_values

        # Infer
        with torch.no_grad():
            logits = self.model(input_values).logits

        # Decode
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        transcription = transcription.replace("|", " ").strip()
        logger.info(f"Transcription completed: {transcription}")
        return transcription

    def transcribe_streaming(self, audio_path: str) -> Any:
        """
        Simulate streaming by returning readable text and metrics.
        """
        logger.info("Starting streaming Wav2Vec2 transcription")
        speech = self.preprocessor.preprocess_audio(audio_path)

        # Process audio
        input_values = self.processor(speech, return_tensors="pt", sampling_rate=16000).input_values

        # Infer
        with torch.no_grad():
            logits = self.model(input_values).logits

        # Token prediction
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        transcription = transcription.replace("|", " ").strip()

        # Create word-level streaming chunks
        tokens = [word for word in transcription.split(" ") if word]

        # Calculate token confidence scores
        token_ids = predicted_ids.squeeze()
        probs = torch.softmax(logits, dim=-1)[0, torch.arange(logits.shape[1]), token_ids]
        precision_score = float(probs.mean().item())
        prob_np = probs.cpu().numpy()
        precision_history = [float(v) for v in prob_np[:10].tolist()]
        std = float(prob_np.std()) if float(prob_np.std()) > 1e-9 else 1e-9
        z_score = float(((prob_np - prob_np.mean()) / std).mean())

        precision_percent = precision_score * 100
        filled = int(min(max(precision_percent / 10, 0), 10))
        precision_graph = "█" * filled + "░" * (10 - filled) + f" {precision_percent:.1f}%"

        logger.info(f"Streaming text generated: {transcription}")
        return tokens, {
            "model_weight_millions": round(self.model_weight_millions, 2),
            "precision_score": round(precision_score, 4),
            "z_score": round(z_score, 4),
            "precision_graph": precision_graph,
            "precision_history": precision_history,
        }

class WhisperTinyModel(TranscriptionModel):
    def __init__(self):
        self.model_name = "openai/whisper-tiny"
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model_name,
            chunk_length_s=30,
            device="cpu",
        )

    def transcribe(self, audio_path: str) -> str:
        result = self.pipe(audio_path)
        return result["text"]

    def transcribe_streaming(self, audio_path: str) -> List[str]:
        # For simplicity, return the full text as a single "token"
        result = self.pipe(audio_path)
        return [result["text"]]

# Model Factory
class ModelFactory:
    _models: Dict[str, TranscriptionModel] = {}

    @classmethod
    def get_model(cls, model_type: str) -> TranscriptionModel:
        if model_type not in cls._models:
            if model_type == "wav2vec2":
                cls._models[model_type] = Wav2Vec2Model()
            elif model_type == "whisper-tiny":
                cls._models[model_type] = WhisperTinyModel()
            else:
                raise ValueError(f"Unknown model type: {model_type}")
        return cls._models[model_type]
