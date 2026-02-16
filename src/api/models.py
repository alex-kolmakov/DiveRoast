from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class UploadResponse(BaseModel):
    session_id: str
    dive_count: int
    dive_numbers: list[str]
    message: str
