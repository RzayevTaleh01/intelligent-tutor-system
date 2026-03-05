import os
from faster_whisper import WhisperModel
from src.config import get_settings

settings = get_settings()

class ASRService:
    def __init__(self):
        # Initialize model on startup (lazy loading is better if memory is tight, 
        # but for responsiveness we init here. 'tiny' is small)
        model_size = settings.WHISPER_MODEL
        try:
            # Run on CPU with INT8 for compatibility/speed on standard machines
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self.available = True
        except Exception as e:
            print(f"ASR Init Failed: {e}")
            self.available = False

    def transcribe(self, audio_file_path: str) -> str:
        if not self.available:
            return "[ASR Unavailable]"
        
        try:
            segments, info = self.model.transcribe(audio_file_path, beam_size=5)
            text = " ".join([segment.text for segment in segments])
            return text.strip()
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""
