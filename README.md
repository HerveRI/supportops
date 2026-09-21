# SupportOps

An Agentic RAG application for answering questions from internal support documents.

SupportOps combines FastAPI, React, PostgreSQL + pgvector, local Sentence Transformers embeddings, BM25 keyword retrieval, hybrid search with Reciprocal Rank Fusion (RRF), and local Ollama inference with Qwen3.5 to provide authenticated document retrieval, agent-driven question answering, and validated source citations.

### Demo
https://github.com/user-attachments/assets/4f43cd04-d07f-4d82-bd44-e4bf592bf52e

#### Part I - MVP - Complete
#### Part II - In Progress - Hybrid Retrieval, Streaming, Evaluation, Conversation Persistence, and Full Dockerization
The hybrid retrieval baseline is implemented. Current Part II work focuses on streaming stability, retrieval evaluation, conversation persistence, and deployment improvements.

## Features
- JWT authentication with HttpOnly cookies
- Member and admin roles
- Admin-only document upload and ingestion - json and txt
- Text extraction and overlapping character chunking
- Local all-MiniLM-L6-v2 embeddings
- PostgreSQL VECTOR(384) storage with pgvector
- Cosine-similarity semantic search
- BM25 keyword search with lexical preprocessing and Porter stemming
- In-memory BM25 inverted index
- BM25 index rebuild after successful ingestion
- Hybrid retrieval using Reciprocal Rank Fusion (RRF)
- Explicit LLM tool calling for retrieval
- Local Qwen3.5 inference through Ollama
- React chat interface
- Validated numbered citations
- Expandable source passages
- Session-only chat history

## Tech Stack
- Backend: Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL 17, pgvector, Alembic, Psycopg 3, Sentence Transformers, NLTK, HTTPX, Ollama, pytest, Ruff, uv
- Frontend: React, TypeScript, Vite, React Router, native fetch, Node.js 22
- Retrieval: pgvector cosine similarity, BM25, Reciprocal Rank Fusion

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

User queries are embedded with the same model and ranked using cosine distance. Semantic queries use the original natural-language query rather than BM25 preprocessing.

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

### Current Part II Work

The following work remains in progress:

- Stabilize streamed Ollama responses
- Benchmark retrieval and generation latency
- Aggregate structured movie results by title before RRF
- Run golden-dataset evaluation across BM25, semantic, and hybrid retrieval
- Compare Precision@K, Recall@K, F1@K, MRR, and latency
- Persistent conversation history
- Full Dockerized application workflow

#### Current Limitations

SupportOps does not currently include:

- PDF or DOCX ingestion
- Persistent conversation history
- Query rewriting or LLM query enhancement
- Cross-encoder reranking
- LLM reranking
- Vector indexes such as HNSW or IVFFlat
- Background workers
- A document deletion API
- Persisted BM25 indexes
- Generalized multi-agent orchestration

