# SupportOps

An Agentic RAG application for answering questions from internal support documents.

SupportOps combines FastAPI, React, PostgreSQL + pgvector, local Sentence Transformers embeddings, and Ollama with Qwen3.5 to provide authenticated semantic search, agent-driven retrieval, source citations.

#### Part I - MVP - Complete
#### Part II - In Progress - Better Retrieval with Hybrid Search, Better Agentic Calls, Chat Streaming, Conversation Persistance, Full Dockerization

## Features
- JWT authentication with HttpOnly cookies
- Member and admin roles
- Admin-only .txt document upload
- Text extraction and overlapping chunking
- Local all-MiniLM-L6-v2 embeddings
- PostgreSQL VECTOR(384) storage with pgvector
- Cosine-similarity semantic search
- Simple RAG baseline
- Explicit LLM tool calling for retrieval
- Local Qwen3.5 inference through Ollama
- React chat interface
- Validated numbered citations
- Expandable source passages
- Session-only chat history

## Tech Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL 17, pgvector, Alembic, Psycopg 3, Sentence Transformers, HTTPX, Ollama, pytest, Ruff, uv
- Frontend: React, TypeScript, Vite, React Router, native fetch, Node.js 22

## Getting Started

### Start PostgreSQL
docker compose up -d db

### Start Ollama
ollama pull qwen3.5:9b

Ollama should be available at:
http://localhost:11434
### Start the backend
- cd backend
- cp .env.example .env
- uv sync
- uv run alembic upgrade head
- uv run uvicorn app.main:app --reload

Example .env values:

- DATABASE_URL=postgresql+psycopg://supportops:supportops@localhost:5432/supportops
- AUTH_SECRET_KEY=change-me
- FRONTEND_ORIGIN=http://localhost:5173
- OLLAMA_BASE_URL=http://localhost:11434
- OLLAMA_MODEL=qwen3.5:9b

Backend:
http://localhost:8000

### Start the frontend
- cd frontend
- nvm use
- npm install
- cp .env.example .env.local
- npm run dev

Example .env.local:
- VITE_API_BASE_URL=http://localhost:8000

Frontend:
- http://localhost:5173

## Retrieval
- Chunks are embedded with:
- sentence-transformers/all-MiniLM-L6-v2

The resulting normalized 384-dimensional vectors are stored in PostgreSQL using pgvector.
Queries are embedded with the same model and ranked using cosine distance.

## Agent Flow

For internal support questions, Qwen can request:
search_knowledge_base

The application executes the tool, retrieves relevant chunks from pgvector, returns them to the model, and validates any citations used in the final answer.

Simple messages such as greetings can be answered without retrieval.

Citations
Retrieved chunks receive temporary labels such as:
[1] [2] [3]

When the model uses retrieved evidence, it references the corresponding label.

The backend validates citation numbers before returning them to the frontend, where users can inspect the supporting filename, chunk, and source passage.

## Tests

Backend:
- cd backend
- uv run ruff format .
- uv run ruff check .
- uv run pytest

## Frontend:
- cd frontend
- npm run lint
- npm run build

### Current Scope

Part I keeps the system simple and does not yet include:

- PDF or DOCX ingestion
- streaming responses
- persistent conversation history
- hybrid search
- reranking
- vector indexes such as HNSW or IVFFlat
- background workers
- generalized multi-agent orchestration
