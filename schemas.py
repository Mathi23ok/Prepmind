from pydantic import BaseModel, Field


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DocumentsResponse(BaseModel):
    documents: list[str]


class UploadResponse(BaseModel):
    message: str
    document_name: str
    chunks: int
    documents: list[str]


class SourceSnippet(BaseModel):
    document_name: str
    preview: str


class QueryResponse(BaseModel):
    user_id: str
    query: str
    document_name: str | None = None
    answer: str
    sources: list[SourceSnippet] = Field(default_factory=list)


class Flashcard(BaseModel):
    question: str
    answer: str


class FlashcardsResponse(BaseModel):
    document_name: str | None = None
    topic: str | None = None
    flashcards: list[Flashcard]


class HealthResponse(BaseModel):
    status: str
    app: str
