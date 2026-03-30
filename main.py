from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

from config import get_settings
from models.faiss_store import add_embeddings, list_documents, user_chunks
from schemas import (
    DocumentsResponse,
    FlashcardsResponse,
    HealthResponse,
    LoginResponse,
    QueryResponse,
    SourceSnippet,
    UploadResponse,
)
from services.auth_service import create_token, verify_token
from services.chunk_service import chunk_text
from services.embedding_service import get_embedding
from services.llm_service import generate_answer, generate_flashcards
from services.pdf_service import extract_text_from_pdf
from services.retrieval_service import retrieve_chunks

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version="1.0.0",
)
bearer_scheme = HTTPBearer(auto_error=False)
frontend_dir = Path(__file__).parent / "frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return user_id


def validate_user_id(user_id: str) -> str:
    cleaned = user_id.strip()
    if len(cleaned) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID must be at least 3 characters long",
        )
    if len(cleaned) > 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID must be 64 characters or fewer",
        )
    return cleaned


def validate_pdf_upload(file: UploadFile, contents: bytes) -> None:
    filename = (file.filename or "").lower()

    if not filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_size_mb} MB upload limit",
        )


if frontend_dir.exists():
    app.mount(settings.frontend_mount_path, StaticFiles(directory=frontend_dir), name="frontend")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    index_file = frontend_dir / "index.html"
    if not index_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frontend not found",
        )
    return FileResponse(index_file)


@app.get("/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", app=settings.app_name)


@app.post("/login", response_model=LoginResponse)
async def login(user_id: str) -> LoginResponse:
    validated_user_id = validate_user_id(user_id)
    token = create_token(validated_user_id)
    return LoginResponse(access_token=token)


@app.get("/documents", response_model=DocumentsResponse)
async def documents(user_id: str = Depends(get_current_user_id)) -> DocumentsResponse:
    return DocumentsResponse(documents=list_documents(user_id))


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
) -> UploadResponse:
    contents = await file.read()
    validate_pdf_upload(file, contents)

    text = extract_text_from_pdf(contents)
    chunks = chunk_text(text, chunk_size=settings.chunk_size_words)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF did not contain readable text",
        )

    embeddings = [get_embedding(chunk) for chunk in chunks]
    document_name = file.filename or f"document-{len(list_documents(user_id)) + 1}.pdf"
    add_embeddings(user_id, document_name, chunks, embeddings)

    return UploadResponse(
        message="Document uploaded successfully",
        document_name=document_name,
        chunks=len(chunks),
        documents=list_documents(user_id),
    )


@app.get("/query", response_model=QueryResponse)
async def query(
    q: str,
    document_name: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
) -> QueryResponse:
    question = q.strip()
    if len(question) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must be at least 3 characters long",
        )

    retrieved_items, _ = retrieve_chunks(user_id, question, document_name=document_name)
    if retrieved_items is None:
        return QueryResponse(
            user_id=user_id,
            query=question,
            document_name=document_name,
            answer="Not found in document",
            sources=[],
        )

    context = "\n".join(item["chunk"] for item in retrieved_items)
    answer = generate_answer(context, question).strip()
    sources = [
        SourceSnippet(
            document_name=item["document_name"],
            preview=item["chunk"][:220].strip(),
        )
        for item in retrieved_items
    ]

    return QueryResponse(
        user_id=user_id,
        query=question,
        document_name=document_name,
        answer=answer,
        sources=sources,
    )


@app.get("/flashcards", response_model=FlashcardsResponse)
async def flashcards(
    document_name: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
) -> FlashcardsResponse:
    if user_id not in user_chunks or len(user_chunks[user_id]) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded",
        )

    if document_name:
        retrieved_items, _ = retrieve_chunks(
            user_id,
            f"Important concepts from {document_name}",
            document_name=document_name,
        )
        if retrieved_items is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant content found for that document",
            )
        context = "\n".join(item["chunk"] for item in retrieved_items)
    else:
        context = "\n".join(user_chunks[user_id][:settings.top_k_chunks])

    return FlashcardsResponse(
        document_name=document_name,
        flashcards=generate_flashcards(context),
    )


@app.get("/flashcards/topic", response_model=FlashcardsResponse)
async def flashcards_topic(
    topic: str,
    document_name: str | None = Query(default=None),
    user_id: str = Depends(get_current_user_id),
) -> FlashcardsResponse:
    cleaned_topic = topic.strip()
    if len(cleaned_topic) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Topic too vague",
        )

    retrieved_items, _ = retrieve_chunks(user_id, cleaned_topic, document_name=document_name)
    if retrieved_items is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No relevant content found",
        )

    context = "\n".join(item["chunk"] for item in retrieved_items)
    return FlashcardsResponse(
        document_name=document_name,
        topic=cleaned_topic,
        flashcards=generate_flashcards(context),
    )
