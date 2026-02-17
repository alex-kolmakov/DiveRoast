# DiveRoast 🌊

**A conversational agent that roasts your SCUBA diving — backed by real safety data.**

[![CI](https://github.com/alex-kolmakov/diveroast/actions/workflows/ci.yaml/badge.svg)](https://github.com/alex-kolmakov/diveroast/actions/workflows/ci.yaml)
![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/docker-blue?logo=docker&logoColor=white)
![dlt](https://img.shields.io/badge/dlt-data%20pipeline-teal)

![MCP](https://img.shields.io/badge/MCP-tool%20server-purple)
![LanceDB](https://img.shields.io/badge/LanceDB-vector%20store-white)
![Arize Phoenix](https://img.shields.io/badge/Arize%20Phoenix-observability-orange)


![Node](https://img.shields.io/badge/node-20-green?logo=node.js&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-06B6D4?logo=tailwindcss&logoColor=white)

## What is this?

DiveRoast analyzes your SCUBA dive logs, identifies safety issues, and delivers personalized safety critiques grounded in real incident reports from [Divers Alert Network (DAN)](https://www.diversalertnetwork.org/). Upload a dive log, get a full safety analysis, learn something.

- **Agentic analysis** — Gemini with function-calling tools reviews your dives and delivers personalized safety commentary with dry humor
- **RAG over DAN content** — hybrid search (semantic + full-text) over DAN incident reports and guidelines via LanceDB
- **Interactive dashboard** — per-dive gauges for ascent rate, SAC rate, NDL, depth; top 3 worst dives with LLM-generated explanations; diver profile with water types, regions, experience level; mini maps for dive sites
- **MCP server** — all diving tools exposed via the Model Context Protocol for use in Claude Desktop, Cursor, or any MCP client
- **Observability** — full LLM/tool/RAG tracing with Arize Phoenix

![Screen Recording 2026-02-17 at 5 14 59 PM](https://github.com/user-attachments/assets/c81ba2e6-4cf5-4e92-8f8e-9ef496a26aa6)


## Quick Start (Docker)

```bash
git clone https://github.com/alex-kolmakov/diveroast.git
cd diveroast
cp .env.sample .env   # add your GEMINI_API_KEY
docker compose up --build
```

Open http://localhost:3000 in your browser.

## Local Development

### Backend

```bash
uv pip install -e ".[dev]"
uvicorn src.api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Services

| Service  | URL                    | Description            |
| -------- | ---------------------- | ---------------------- |
| Frontend | http://localhost:5173   | React dev server       |
| Backend  | http://localhost:8000   | FastAPI + SSE          |
| Phoenix  | http://localhost:6006   | Tracing UI             |

## MCP Server

DiveRoast exposes its diving tools as an MCP server (stdio transport). Add to your Claude Desktop or Cursor config:

```json
{
  "mcpServers": {
    "diveroast": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "cwd": "/path/to/diveroast"
    }
  }
}
```

Available tools: `search_dan_incidents`, `search_dan_guidelines`, `parse_dive_log`, `analyze_dive_profile`, `get_dive_summary`, `list_dives`, `refresh_dan_data`.

## Environment Variables

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `GEMINI_API_KEY` | — | **Required.** Google Gemini API key |
| `GEMINI_MODEL` | `gemini-3.0-flash` | Gemini model to use |
| `PROMPT_VERSION` | `3` | Active prompt version (1=roast-master, 2=polite-analyst, 3=dry-humor-analyst) |
| `LANCEDB_URI` | `.lancedb` | Path to LanceDB storage |
| `DESTINATION__LANCEDB__EMBEDDING_MODEL_PROVIDER` | `sentence-transformers` | Embedding provider |
| `DESTINATION__LANCEDB__EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `DESTINATION__LANCEDB__CREDENTIALS__URI` | `.lancedb` | LanceDB credentials URI |
| `RAG_TOP_K` | `10` | Number of RAG results to retrieve |
| `CHUNK_SIZE` | `2000` | Document chunk size for RAG |
| `CHUNK_OVERLAP` | `100` | Chunk overlap for RAG |
| `PHOENIX_COLLECTOR_ENDPOINT` | `http://localhost:6006/v1/traces` | Phoenix trace collector |
| `PHOENIX_PROJECT_NAME` | `diveroast` | Phoenix project name |

## Project Structure

```
src/
├── agent/         # Gemini client, system prompts, function-calling tools
├── analysis/      # Feature engineering (ascent speed, NDL, SAC rate)
├── api/           # FastAPI gateway with SSE streaming
├── mcp/           # MCP server (7 tools via FastMCP)
├── parsers/       # Dive log parsing (ABC + Subsurface XML)
├── pipelines/     # CLI scripts for DAN ingestion & dive processing
├── rag/           # dlt pipeline + LanceDB hybrid search
├── config.py
└── observability.py

frontend/src/
├── components/    # React UI components
├── hooks/         # Custom React hooks
├── services/      # API client
├── types/         # TypeScript types
└── App.tsx
```

## Testing

```bash
# Backend
pytest tests/ -x --tb=short

# Frontend type-check
cd frontend && npx tsc --noEmit
```

## Contributing

Install pre-commit hooks before pushing:

```bash
pre-commit install
pre-commit run --all-files
```

The pre-commit pipeline runs **ruff** (lint + format), **pyrefly** (type check), and **pytest**.

## License

MIT

## Acknowledgements

Thanks to [#DataTalksClub](https://datatalks.club/) for mentoring and providing a platform to learn during the 2024 Cohort.
