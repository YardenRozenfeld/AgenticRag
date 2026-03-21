# Nexus AI — Agentic RAG Chatbot

A production-grade Agentic RAG chatbot powered by **LangGraph**, featuring adaptive retrieval, self-grading, hallucination detection, and Supabase-backed authentication with per-user conversation memory.

Built on the original [LangChain Cookbook](https://github.com/mistralai/cookbook/tree/main/third_party/langchain) by [Sophia Young](https://x.com/sophiamyang) (Mistral) and [Lance Martin](https://x.com/RLanceMartin) (LangChain) — then significantly extended with a full web UI, auth layer, persistent memory, and a clean package architecture.

---

## Features

- **Adaptive RAG** — Routes questions between local vector store retrieval and live Tavily web search
- **Self-RAG** — Grades retrieved documents for relevance before generating answers
- **Reflective RAG** — Evaluates answers for hallucinations and usefulness, looping back to improve if needed
- **Auth & Memory** — Supabase email/password auth with per-user conversation threads persisted via Postgres checkpointer
- **Web UI** — Dark-themed responsive frontend with sign-in/sign-up and a chat interface with thread sidebar
- **Test Coverage** — Integration tests for all LLM chains (graders, generator, router)

---

## Architecture

```
User Question
      │
      ▼
┌─────────────┐
│   Router     │──── vectorstore ──▶ Retrieve ──▶ Grade Documents
│              │                                        │
│              │──── websearch ──────────────────┐      │ (irrelevant docs)
└──────────────┘                                 │      ▼
                                                 │   Web Search
                                                 │      │
                                                 └──▶ Generate
                                                        │
                                              Hallucination Check
                                              ├── not grounded ──▶ Generate (retry)
                                              └── grounded ──▶ Answer Check
                                                              ├── not useful ──▶ Web Search
                                                              └── useful ──▶ Return Answer
```

Each box is a **LangGraph node**. Conditional edges between nodes implement the self-correcting loop — the graph can retry generation or fall back to web search automatically until it produces a grounded, useful answer.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Orchestration | **LangGraph** | Stateful graph-based agent with conditional routing |
| LLM | **OpenAI** (via LangChain) | Chat completion for all chains |
| Vector Store | **ChromaDB** | Local persistent embedding store |
| Web Search | **Tavily** | Real-time web search fallback |
| Auth & DB | **Supabase** | Email/password auth + Postgres conversation memory |
| API | **FastAPI** | REST API with dependency injection |
| Observability | **LangSmith** | Tracing and debugging (optional) |

---

## Quick Start

### Prerequisites

- Python 3.12+
- A [Supabase](https://supabase.com) project (free tier works)
- API keys: [OpenAI](https://platform.openai.com/api-keys), [Tavily](https://tavily.com)

### 1. Clone and install

```bash
git clone <repo-url>
cd AgenticRag

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your actual keys
```

See [`.env.example`](.env.example) for all required variables. Key ones:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | OpenAI API access for all LLM chains |
| `TAVILY_API_KEY` | Web search fallback when vector store docs are irrelevant |
| `SUPABASE_URL` | Supabase project URL for auth |
| `SUPABASE_ANON_KEY` | Public key for client-side auth operations |
| `SUPABASE_SERVICE_ROLE_KEY` | Admin key for thread management |
| `SUPABASE_DB_URL` | Direct Postgres connection for LangGraph checkpointer |

> **LangSmith** (optional): Set `LANGCHAIN_TRACING_V2=true` and provide a `LANGCHAIN_API_KEY` to enable tracing.

### 3. Run the Supabase migration

Open **Supabase Dashboard → SQL Editor → New query** and run:

```sql
-- contents of migrations/001_create_threads.sql
```

This creates the `threads` table with Row Level Security policies.

### 4. Ingest documents

Run once to load source documents (three Lilian Weng blog posts), chunk them, and persist embeddings:

```bash
python -m app.ingestion
```

### 5. Start the server

```bash
uvicorn app.server:app --reload
```

| URL | Description |
|---|---|
| `http://127.0.0.1:8000` | Sign In / Sign Up page |
| `http://127.0.0.1:8000/app` | Chat interface (requires auth) |
| `http://127.0.0.1:8000/docs` | Interactive Swagger API docs |

### 6. Run tests

```bash
python -m pytest tests/ -v
```

### 7. CLI mode (no auth, local dev)

```bash
python -m app.cli
```

---

## API Reference

All `/chat` and `/threads` endpoints require a Supabase access token:

```
Authorization: Bearer <access_token>
```

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/` | GET | No | Sign In / Sign Up page |
| `/app` | GET | No | Chat page (JS redirects if no token) |
| `/auth/signup` | POST | No | Create account: `{ "email": "...", "password": "..." }` |
| `/auth/login` | POST | No | Login, receive access + refresh tokens |
| `/chat` | POST | Yes | `{ "question": "...", "thread_id": null }` — omit `thread_id` for new conversation |
| `/threads` | GET | Yes | List authenticated user's conversation threads |

---

## Project Structure

```
AgenticRag/
├── pyproject.toml                       # Project metadata, dependencies, tool config
├── requirements.txt                     # Pinned dependencies
├── .env.example                         # Environment variable template
├── migrations/
│   └── 001_create_threads.sql           # Supabase SQL — threads table with RLS
├── frontend/                            # Static frontend (served by FastAPI)
│   ├── index.html                       # Auth page
│   ├── chat.html                        # Chat interface with thread sidebar
│   ├── css/styles.css                   # Dark theme, glassmorphism, responsive
│   ├── js/auth.js                       # Auth logic, token storage
│   ├── js/chat.js                       # Chat API, thread management, rendering
│   └── assets/nexus-logo.svg            # App logo
├── app/                                 # Main Python package
│   ├── config.py                        # Pydantic-settings centralized config
│   ├── server.py                        # FastAPI app assembly + lifespan
│   ├── cli.py                           # CLI entry point (no auth)
│   ├── ingestion.py                     # Document loading + ChromaDB indexing
│   ├── api/                             # API route modules
│   │   ├── deps.py                      # Supabase clients, auth dependency
│   │   ├── auth.py                      # /auth/signup, /auth/login
│   │   ├── chat.py                      # /chat endpoint
│   │   ├── threads.py                   # /threads endpoint
│   │   └── pages.py                     # Static HTML page routes
│   └── graph/                           # LangGraph agent
│       ├── graph.py                     # Workflow: nodes, edges, conditional routing
│       ├── state.py                     # GraphState TypedDict
│       ├── consts.py                    # Node name constants
│       ├── chains/                      # LCEL chain definitions
│       │   ├── router.py               # Question → vectorstore / websearch
│       │   ├── retrieval_grader.py      # Document relevance scoring
│       │   ├── generation.py            # RAG answer generation
│       │   ├── hallucination_grader.py  # Hallucination detection
│       │   └── answer_grader.py         # Answer usefulness scoring
│       └── nodes/                       # Graph node functions
│           ├── retrieve.py              # Query ChromaDB
│           ├── grade_documents.py       # Filter irrelevant docs
│           ├── generate.py              # Produce answer + conversation messages
│           └── web_search.py            # Tavily fallback
└── tests/
    ├── conftest.py                      # Shared fixtures (env loading)
    └── test_chains.py                   # Integration tests for all chains
```

---

## Graph Flow Details

| Decision Point | Condition | Next Step |
|---|---|---|
| **Router** | Question about agents / prompts / LLMs | Retrieve from ChromaDB |
| **Router** | Any other question | Tavily web search |
| **Grade Documents** | All docs relevant | Generate answer |
| **Grade Documents** | Any doc irrelevant | Web search, then generate |
| **Hallucination Check** | Generation grounded in docs | Answer quality check |
| **Hallucination Check** | Generation not grounded | Re-generate (retry) |
| **Answer Check** | Answer resolves the question | Return to user |
| **Answer Check** | Answer doesn't resolve | Web search, then generate |

---

## Design Decisions & Architecture Rationale

This section explains the **why** behind the key technical choices — useful for understanding the thought process and trade-offs.

### Why LangGraph over a simple LangChain chain?

A basic RAG pipeline is a linear chain: retrieve → generate → return. But that approach has no self-correction — if the retrieved documents are irrelevant or the generated answer hallucinates, the user gets a bad response with no recourse.

LangGraph lets us model the pipeline as a **stateful directed graph with conditional edges**. This means the system can:
- **Route** questions to different retrieval strategies (vector store vs. web search)
- **Loop back** when documents are irrelevant (fall back to web search)
- **Retry** generation when hallucination is detected
- **Re-search** when the answer doesn't actually address the question

This self-correcting loop is the core value proposition — it dramatically improves answer quality compared to single-pass RAG.

### Why separate grader chains instead of one big prompt?

Each grader (retrieval relevance, hallucination detection, answer usefulness) is a small, focused LCEL chain with **structured output** (Pydantic models returning `"yes"` / `"no"`). This design choice offers several advantages:

1. **Testability** — Each chain can be unit-tested independently (see `tests/test_chains.py`)
2. **Composability** — Chains can be swapped, tuned, or replaced without touching the graph logic
3. **Reliability** — Structured output with function calling ensures consistent binary responses rather than parsing free-text
4. **Observability** — Each chain shows up as a separate step in LangSmith traces

### Why Supabase for auth + memory?

The project needed both authentication and persistent conversation memory. Supabase provides:
- **Auth** — Built-in email/password with JWT tokens, no custom auth code needed
- **Postgres** — LangGraph's `PostgresSaver` checkpointer stores full conversation state (including intermediate graph state) in Postgres, enabling seamless conversation resumption
- **Row Level Security** — Thread data is scoped to users at the database level via RLS policies
- **Single platform** — One service handles auth, database, and RLS instead of stitching together multiple providers

### Why the `app/` package structure?

The original codebase had all entry points (`server.py`, `main.py`, `ingestion.py`) at the project root with no proper Python package, and the server file mixed authentication, chat logic, thread management, and static file serving in a single 168-line file.

The restructured `app/` package provides:
- **Separation of concerns** — The monolithic server is split into focused route modules (`api/auth.py`, `api/chat.py`, etc.), each with a single responsibility
- **Centralized configuration** — `app/config.py` uses Pydantic Settings to validate all environment variables at startup with type checking, replacing scattered `os.environ` calls and `load_dotenv()` across multiple files
- **Clean imports** — All internal imports use the `app.` prefix, making dependencies explicit and avoiding relative import confusion
- **No side effects on import** — The old `graph.py` had `app = build_graph()` at module level, meaning importing the module triggered graph compilation. Now `build_graph()` is only called explicitly during server startup (lifespan) or CLI invocation
- **Proper test isolation** — Tests live in a top-level `tests/` directory with a `conftest.py` for shared fixtures, following pytest conventions

### Why `pydantic-settings` for configuration?

Instead of `os.environ.get()` scattered across files:
- **Validation at startup** — If a required key is missing, the app fails immediately with a clear error instead of crashing mid-request
- **Type coercion** — Boolean and string fields are automatically parsed from `.env`
- **Single source of truth** — One `Settings` class documents every config value the app needs
- **Cached singleton** — `@lru_cache` on `get_settings()` ensures the `.env` file is read exactly once

### Why ChromaDB over Pinecone / Weaviate / pgvector?

ChromaDB was chosen for **zero-infrastructure local development**. It persists embeddings to a local directory (`.chroma_db/`) with no external service needed. This means anyone cloning the repo can run the full pipeline immediately after `python -m app.ingestion` — no cloud vector DB account required. For production scale, the retriever could be swapped to a managed solution with minimal code changes (just replace the `retriever` in `app/ingestion.py`).

### Why Tavily for web search?

Tavily is purpose-built for LLM applications — it returns clean, parsed content (not raw HTML) optimized for context windows. It integrates directly with LangChain as a tool, making it a drop-in node in the LangGraph workflow. The web search fallback ensures the chatbot can answer questions outside its vector store's domain instead of returning "I don't know."
