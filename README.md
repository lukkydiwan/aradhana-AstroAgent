# Aradhana · AstroAgent

A conversational AI astrology companion that computes real birth charts from a Keplerian orbital mechanics engine, reasons over live planetary transits, and answers questions with warmth and spiritual care.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     React Frontend                      │
│  BirthDetailsForm → ChatInterface → MessageBubble       │
│                 SSE streaming / fetch                   │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP / SSE
┌───────────────────────▼─────────────────────────────────┐
│               FastAPI  (app/main.py)                    │
│   POST /chat  →  StreamingResponse (text/event-stream)  │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│            LangGraph Agent  (app/agent/graph.py)        │
│                                                         │
│   START                                                 │
│     │                                                   │
│     ▼                                                   │
│  ┌──────────┐  tool calls   ┌──────────────────────┐   │
│  │  agent   │ ────────────► │  ToolNode (4 tools)  │   │
│  │ (Mistral)│ ◄──────────── │  geocode_place       │   │
│  └──────────┘  results      │  compute_birth_chart │   │
│     │                       │  get_daily_transits  │   │
│     │ final answer          │  knowledge_lookup    │   │
│     ▼                       └──────────────────────┘   │
│    END                                                  │
│                                                         │
│  Checkpointing: MemorySaver (conversation persistence)  │
└─────────────────────────────────────────────────────────┘
```

**Agent state** (`AstroState`): messages, birth_details, chart_data (cached), session_id, step_count.

The graph follows the standard ReAct pattern: the LLM reasons and may call tools; if tool calls are emitted, the `ToolNode` executes them and the result loops back; when the LLM produces a plain message, the graph exits. A step-count guard (max 10) prevents runaway loops.

---

## Prerequisites

- Python 3.11+
- Node 18+
- A Mistral API key (free tier available at console.mistral.ai)

---

## Setup

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env → set MISTRAL_API_KEY=...

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### Evaluation

```bash
# Make sure the backend is running first
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

python ../eval/run_eval.py --api http://localhost:8000

# With LLM-as-judge scoring:
python ../eval/run_eval.py --api http://localhost:8000 --judge --verbose
```

---

## Tools

| Tool | Description | Library |
|------|-------------|---------|
| `geocode_place` | Resolves city name → lat/lon/timezone | geopy (Nominatim) + timezonefinder |
| `compute_birth_chart` | Full natal chart with planet positions + houses | Pure-Python Keplerian ephemeris (Schlyter algorithm, ~0.1° inner / ~1° outer) |
| `get_daily_transits` | Current planetary positions + aspects to natal chart | Same ephemeris; takes birth details directly, no pre-computed chart required |
| `knowledge_lookup` | BM25-style search over curated astrology notes | built-in |

All planetary positions are computed from real orbital mechanics — no positions are invented. The ephemeris is a pure-Python implementation of Schlyter's Keplerian algorithm (no C compiler required). Accuracy is ~0.1° for inner planets and ~1° for outer planets — sufficient for sign and house placement in a birth chart, though not at Swiss Ephemeris precision. `pyswisseph` is a drop-in upgrade if a C compiler is available.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MISTRAL_API_KEY` | — | Required. Get a free key at console.mistral.ai |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins. |
| `PORT` | `8000` | Backend port. |

---

## Known limitations

- **No authentication**: session IDs are generated client-side, stored in sessionStorage. Not suitable for production multi-user without auth.
- **MemorySaver**: conversation history lives in memory and resets on server restart. Switch to `SqliteSaver` for persistence.
- **Geocoding rate limit**: Nominatim has a 1 req/s limit. Add a delay or switch to a paid geocoder for load testing.
- **Birth time accuracy**: Unknown birth time defaults are not handled — the agent asks the user. Whole-sign or solar chart fallback is a stretch goal.
- **No caching of chart computations**: Each session recomputes the chart. Caching by (date+time+lat+lon) would cut latency ~30%.
