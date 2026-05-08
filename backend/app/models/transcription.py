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

        # Simple noise reduction using spectral gating
        # This is a basic implementation; for better results, consider noisereduce library
        stft = librosa.stft(speech)
        magnitude, phase = librosa.magphase(stft)

        # Estimate noise from first 0.5 seconds
        noise_samples = int(0.5 * sample_rate)
        if len(speech) > noise_samples:
            noise_stft = librosa.stft(speech[:noise_samples])
            noise_magnitude = np.abs(noise_stft)
            noise_threshold = np.mean(noise_magnitude, axis=1, keepdims=True)

            # Apply spectral gating
            mask = magnitude > noise_threshold * 1.5
            magnitude_clean = magnitude * mask
        else:
            magnitude_clean = magnitude

        # Reconstruct audio
        stft_clean = magnitude_clean * phase
        speech_clean = librosa.istft(stft_clean)

        # Normalize
        speech_clean = librosa.util.normalize(speech_clean)

        logger.info(f"Audio preprocessing completed. Shape: {speech_clean.shape}")
        return speech_clean

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
        transcription = self.processor.batch_decode(predicted_ids)[0]
        logger.info(f"Transcription completed: {transcription}")
        return transcription

    def transcribe_streaming(self, audio_path: str) -> List[str]:
        """
        Simulate streaming by returning tokens progressively.
        In a real implementation, this would process chunks.
        """
        logger.info("Starting streaming Wav2Vec2 transcription")
        speech = self.preprocessor.preprocess_audio(audio_path)

        # Process audio
        input_values = self.processor(speech, return_tensors="pt", sampling_rate=16000).input_values

        # Infer
        with torch.no_grad():
            logits = self.model(input_values).logits

        # Decode to tokens
        predicted_ids = torch.argmax(logits, dim=-1).squeeze().tolist()

        # Calculate token confidence scores
        token_ids = torch.tensor(predicted_ids, device=logits.device)
        probs = torch.softmax(logits, dim=-1)[0, torch.arange(logits.shape[1]), token_ids]
        precision_score = float(probs.mean().item())
        prob_np = probs.cpu().numpy()
        precision_history = [float(v) for v in prob_np[:10].tolist()]
        std = float(prob_np.std()) if float(prob_np.std()) > 1e-9 else 1e-9
        z_score = float(((prob_np - prob_np.mean()) / std).mean())

        # Get vocabulary for token mapping
        vocab = self.processor.tokenizer.get_vocab()
        id_to_token = {v: k for k, v in vocab.items()}

        tokens = []
        for token_id in predicted_ids:
            if token_id in id_to_token:
                token = id_to_token[token_id]
                if token not in ['[PAD]', '[UNK]', '|']:  # Filter out special tokens
                    tokens.append(token)

        precision_percent = precision_score * 100
        filled = int(min(max(precision_percent / 10, 0), 10))
        precision_graph = "█" * filled + "░" * (10 - filled) + f" {precision_percent:.1f}%"

        logger.info(f"Streaming tokens generated: {len(tokens)} tokens")
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
