# Aarogya AI – Intelligent Medical Chatbot

**Aarogya AI** is a production-ready medical education chatbot that answers health-related questions using **Retrieval-Augmented Generation (RAG)** over a MedQuAD-derived knowledge base.

> ⚠️ **Disclaimer:** This information is for educational purposes only. Please consult a licensed healthcare professional for medical advice. Aarogya AI is **not** a replacement for emergency services or clinical care.

---

## Features

- **JWT auth** – register, login, profile, password change
- **RAG medical chat** – FAISS + Sentence Transformers + Ollama (Llama 3.1 / Qwen2.5)
- **ChatGPT-like UI** – streaming, markdown, sources, confidence, voice (STT/TTS)
- **Emergency detection** – chest pain, breathing difficulty, suicidal ideation, etc.
- **Categories** – Symptoms, Diseases, Medicines, First Aid, Nutrition, Mental Health, Pregnancy, Child Care, Fitness
- **Bonus tools** – BMI calculator, symptom checker, medicine reminders, health tips, hospital placeholders, PDF/text export
- **Admin panel** – users, chats, analytics (Chart.js), dataset upload, logs
- **Dark mode**, responsive layout, Framer Motion animations
- **Docker** + Docker Compose ready

---

## Tech Stack

| Layer | Stack |
|-------|--------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, SQLite, JWT, bcrypt |
| AI | LangChain-ready, HuggingFace Sentence Transformers, FAISS, Ollama |
| Frontend | React, Vite, TypeScript, Tailwind CSS, Framer Motion, Axios, Chart.js |
| Ops | Docker, Docker Compose, `.env` configuration |

---

## Project Structure

```
aarogya-ai/
├── backend/app/
│   ├── api/          # Auth, chat, profile, tools, admin routes
│   ├── auth/         # JWT + password hashing
│   ├── database/     # SQLAlchemy engine
│   ├── models/       # Users, Chats, Messages, Documents, Embeddings…
│   ├── rag/          # RAG pipeline (embed → retrieve → generate)
│   ├── schemas/      # Pydantic models
│   ├── services/     # Business logic
│   ├── utils/        # Config, helpers, emergency detection
│   └── main.py
├── frontend/         # React + Vite app
├── dataset/          # MedQuAD sample JSON
├── vector_db/        # FAISS index (built on first run / script)
├── scripts/          # build_index.py
├── docker-compose.yml
└── .env.example
```

---

## Quick Start (Local)

## Prerequisites

- Python **3.11+** (3.11 or 3.12 recommended; 3.13 works with TF-IDF retrieval)
- Node.js **20+**
- (Optional) [Ollama](https://ollama.com) with `llama3.1` or `qwen2.5`
- (Optional) Set `ENABLE_FAISS=true` for sentence-transformer embeddings on supported platforms

On first run, Aarogya AI uses a **pure-Python TF-IDF retriever** over MedQuAD so the API starts without downloading Torch. When `ENABLE_FAISS=true` and the embedding stack is healthy, FAISS semantic search is used instead.

### 1. Clone / open the project

```bash
cd aarogya-ai
cp .env.example .env
```

### 2. Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy ..\.env .env   # or: cp ../.env .env

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

On first startup the app builds a FAISS index from `dataset/medquad_sample.json` (requires downloading the embedding model once).

**Optional – rebuild index manually:**

```bash
cd aarogya-ai
python scripts/build_index.py
```

**Optional – Ollama LLM:**

```bash
ollama pull llama3.1
ollama serve
```

If Ollama is offline, Aarogya AI falls back to **extractive RAG** answers from retrieved MedQuAD documents.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

### Default admin

| Field | Value |
|-------|--------|
| Email | `admin@aarogya.ai` |
| Password | `Admin@12345` |

---

## Docker

```bash
docker compose up --build
```

- Frontend (nginx): http://localhost  
- Backend API: http://localhost:8000  

Ollama on the host is reachable via `host.docker.internal:11434`.

---

## RAG Pipeline

```
User Question → Embedding → FAISS Top-5 → LLM Prompt (Ollama) → Answer + Sources + Confidence
```

Emergency phrases short-circuit to a safety warning instead of a normal answer.

---

## Key API Routes

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login (JWT) |
| POST | `/api/chat` | Ask a medical question |
| POST | `/api/chat/stream` | SSE streaming chat |
| GET | `/api/history` | List conversations |
| DELETE | `/api/history/{id}` | Delete chat |
| GET/PUT | `/api/profile` | Profile |
| POST | `/api/voice` | Voice helper stub |
| GET | `/api/admin/dashboard` | Admin stats |

---

## Dataset

Primary corpus: **MedQuAD**-style Q&A (sample included under `dataset/medquad_sample.json`).

Preprocessing: dedupe → text clean → sentence embeddings → FAISS `IndexFlatIP`.

To expand knowledge, upload JSON via Admin → Dataset (then rebuild the index).

---

## Security

- bcrypt password hashing  
- JWT bearer auth  
- Pydantic input validation  
- SlowAPI rate limiting  
- Environment-based secrets  
- Structured error handling & logging  

---

## License / Ethics

Educational project only. Always display the medical disclaimer. Do not use for clinical decision-making.

---

Built with care for accessible health education — **Aarogya AI**.
