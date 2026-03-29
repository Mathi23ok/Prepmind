
# PrepMind 

A document-first revision system built for students who want answers from *their own material*, not generic internet responses.

---

## What it does

PrepMind lets you:

* Upload PDFs (notes, books, PYQs)
* Ask questions grounded in your documents
* Get clean, context-based answers
* Generate revision flashcards from your content
* Focus on specific documents or topics

This is not just a chatbot.
It’s a **personalized study system**.

---

## Why this exists

Most AI tools:

* give generic answers
* don’t remember your material
* don’t help with revision

PrepMind fixes that by:

* grounding answers in your PDFs
* isolating user data
* turning doubts into flashcards

---

## Core Features

### 1. Document-based Q&A

Ask questions and get answers strictly from your uploaded PDFs.

### 2. Multi-user system

Each user has isolated data (no mixing of documents).

### 3. Semantic search (RAG)

* Text is chunked and embedded
* FAISS is used for similarity search
* Only relevant chunks are passed to the model

### 4. Flashcard generation

* General flashcards
* Topic-based flashcards
* Query-based flashcards (from your doubts)

### 5. Clean UI

* Upload → Ask → Revise flow
* Source snippets for transparency
* Interactive flashcards

---

## Tech Stack

**Backend**

* FastAPI
* FAISS (vector search)
* Sentence Transformers (embeddings)
* OpenAI API

**Frontend**

* Vanilla HTML / CSS / JS

**Auth**

* JWT-based authentication

---

## How it works

1. Upload PDF
2. Extract text
3. Chunk text
4. Convert chunks → embeddings
5. Store in FAISS index (per user)
6. On query:

   * embed query
   * retrieve top chunks
   * send to LLM
7. Generate answer / flashcards



## API Overview

* `POST /login` → get token
* `POST /upload` → upload PDF
* `GET /query` → ask questions
* `GET /flashcards` → generate cards
* `GET /flashcards/topic` → topic-based cards
* `GET /documents` → list uploaded docs

---

## Limitations

* In-memory storage (data lost on restart)
* No background processing for heavy uploads
* No rate limiting
* Not optimized for large-scale users yet

---

## Next Improvements

* Persistent storage (PostgreSQL / vector DB)
* Batch embeddings
* Background processing
* Spaced repetition system
* Better evaluation of answer quality

---

## What I learned

* Designing a real system > writing isolated code
* Handling authentication and user isolation
* Building a complete RAG pipeline end-to-end
* Turning a simple idea into a usable product

---

## Author

Built by someone trying to move from “coding projects” to “building systems”.
