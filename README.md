# Agentic RAG with LangGraph

Implementation of Reflective RAG, Self-RAG & Adaptive RAG tailored towards developers and production-oriented applications using LangGraph.

Based on the original [LangChain Cookbook](https://github.com/mistralai/cookbook/tree/main/third_party/langchain) by [Sophia Young](https://x.com/sophiamyang) (Mistral) and [Lance Martin](https://x.com/RLanceMartin) (LangChain).

## Features

- **Adaptive RAG**: Routes questions intelligently between local vector store retrieval and live Tavily web search
- **Self-RAG**: Grades retrieved documents for relevance before generating answers
- **Reflective RAG**: Evaluates generated answers for hallucinations and usefulness, looping back to improve if needed
- **Production-Oriented**: Clean modular structure with typed state, LCEL chains, and separated nodes
- **Test Coverage**: Integration tests for all chains (retrieval grader, generation, hallucination grader, answer grader, router)

## Architecture

```
User Question
      │
      ▼
┌─────────────┐
│   Router    │──── vectorstore ──▶ Retrieve ──▶ Grade Documents
│             │                                        │
│             │──── websearch ──────────────────┐     │ (irrelevant docs found)
└─────────────┘                                 │     ▼
                                                │  Web Search
                                                │     │
                                                └──▶ Generate
                                                        │
                                              Hallucination Check
                                              ├── not grounded ──▶ Generate (retry)
                                              └── grounded ──▶ Answer Check
                                                              ├── not useful ──▶ Web Search
                                                              └── useful ──▶ Return Answer
```

## Tech Stack

- **Python** 3.12
- **LangGraph** — stateful graph-based agent orchestration
- **LangChain** + **LangChain-OpenAI** — LCEL chain composition, OpenAI models
- **ChromaDB** — local persistent vector store
- **Tavily** — real-time web search fallback
- **Supabase** — authentication (email/password) and Postgres-backed conversation memory
- **LangSmith** — tracing and observability (optional)

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) or pip

## Installation

```bash
git clone <repo-url>
cd AgenticRag

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
LANGCHAIN_API_KEY=ls__...        # Optional — required only if tracing is enabled
LANGCHAIN_TRACING_V2=true        # Optional
LANGCHAIN_PROJECT=AgenticRag     # Optional
PYTHON_PATH=.

# Supabase (required for server.py auth & per-user memory)
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_DB_URL=postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
```

| Variable | Purpose |
|---|---|
| `SUPABASE_URL` | Supabase project URL — used by the Python client for auth operations |
| `SUPABASE_ANON_KEY` | Supabase anonymous/public key — used by the Python client for auth operations |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service-role key — used for admin-level operations (thread listing) |
| `SUPABASE_DB_URL` | Direct Postgres connection string — used by the LangGraph `PostgresSaver` checkpointer for conversation memory |

> **Note**: If `LANGCHAIN_TRACING_V2=true`, a valid `LANGCHAIN_API_KEY` must be set or the app will error on startup.
>
> **Supabase setup**: Create a project at [supabase.com](https://supabase.com), enable email/password auth, and copy the connection details from the project dashboard into the variables above.

## Usage

### 1. Ingest documents into the vector store

Run once to load the source documents (three Lilian Weng blog posts on prompt engineering, adversarial attacks, and hallucination), chunk them, and persist embeddings to `.chroma_db/`:

```bash
python ingestion.py
```

### 2. Run the agent

```bash
python main.py
```

### 3. Run tests

```bash
pytest graph/chains/tests/ -v
```

## Project Structure

```
AgenticRag/
├── main.py                          # Entry point — invokes the compiled LangGraph app
├── ingestion.py                     # Document loading, splitting, and ChromaDB indexing
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (not committed)
├── graph/
│   ├── graph.py                     # LangGraph workflow: nodes, edges, conditional routing
│   ├── state.py                     # GraphState TypedDict schema
│   ├── consts.py                    # Node name constants
│   ├── chains/
│   │   ├── retrievel_grader.py      # Document relevance grader chain
│   │   ├── generation.py            # RAG answer generation chain (rlm/rag-prompt)
│   │   ├── hallucination_grader.py  # Hallucination detection grader chain
│   │   ├── answer_grader.py         # Answer usefulness grader chain
│   │   ├── router.py                # Question router chain (vectorstore vs websearch)
│   │   └── tests/
│   │       └── test_chains.py       # Integration tests for all chains
│   └── nodes/
│       ├── retrieve.py              # Retrieve node — queries ChromaDB
│       ├── grade_documents.py       # Grade documents node — filters irrelevant docs
│       ├── generate.py              # Generate node — produces final answer
│       └── web_search.py            # Web search node — Tavily fallback
└── .cursor/
    └── rules/
        └── readme-agent.mdc
```

## Graph Flow Details

| Decision Point | Condition | Next Step |
|---|---|---|
| Router | Question about agents/prompts/LLMs → vectorstore | Retrieve from ChromaDB |
| Router | Any other question → websearch | Tavily web search |
| Grade Documents | All docs relevant | Generate |
| Grade Documents | Any doc irrelevant | Web search then Generate |
| Hallucination Check | Generation grounded in docs | Answer Check |
| Hallucination Check | Generation not grounded | Re-generate |
| Answer Check | Answer resolves question | Return to user |
| Answer Check | Answer doesn't resolve question | Web search then Generate |
