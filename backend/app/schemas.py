"""Request/response shapes (like DTOs in Java). FastAPI validates them automatically."""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=72)
    full_name: str = Field(min_length=1, max_length=80)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: int | None = None


class Source(BaseModel):
    source: str
    page: int
    score: float
    snippet: str


class ChatResponse(BaseModel):
    conversation_id: int
    answer: str
    sources: list[Source]
