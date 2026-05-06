import torch
import librosa
from transformers import pipeline, Wav2Vec2ForCTC, Wav2Vec2Processor
from typing import Dict, Any

class TranscriptionModel:
    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError

class Wav2Vec2Model(TranscriptionModel):
    def __init__(self):
        self.model_name = "facebook/wav2vec2-base-960h"
        self.processor = Wav2Vec2Processor.from_pretrained(self.model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name)

    def transcribe(self, audio_path: str) -> str:
        # Load audio
        speech, sample_rate = librosa.load(audio_path, sr=16000)
        
        # Process audio
        input_values = self.processor(speech, return_tensors="pt", sampling_rate=16000).input_values
        
        # Infer
        with torch.no_grad():
            logits = self.model(input_values).logits
        
        # Decode
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]
        return transcription

class WhisperTinyModel(TranscriptionModel):
    def __init__(self):
        self.model_name = "openai/whisper-tiny"
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model_name,
            chunk_length_s=30,
            device="cpu", # Default to CPU, can be changed to "cuda" if GPU is available
        )

    def transcribe(self, audio_path: str) -> str:
        result = self.pipe(audio_path)
        return result["text"]

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
