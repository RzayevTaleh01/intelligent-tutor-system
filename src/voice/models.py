from pydantic import BaseModel

class ASRRequest(BaseModel):
    pass # File upload handled separately

class ASRResponse(BaseModel):
    text: str
    language: str = "en"
    duration: float

class TTSRequest(BaseModel):
    text: str
    voice: str = None

class VoiceChatResponse(BaseModel):
    asr_text: str
    reply_text: str
    audio_url: str = None
    next_step_plan: dict
    items: list
