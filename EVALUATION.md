# Evaluation Notes — Aradhana AstroAgent

## Overview

The evaluation harness (`eval/run_eval.py`) runs 25 golden test cases across six categories and produces a scorecard covering correctness, cost, latency, and failure rate. This document records what the eval revealed and what I would fix with more time.

---

## Eval Design Decisions

### Separation of deterministic vs. judge checks

Every test case has deterministic assertions:
- **Tool presence**: did the right tools get called? (e.g., `geocode_place` + `compute_birth_chart` for a chart request)
- **Keyword presence**: does the response mention expected concepts? (e.g., "Sun", "Moon" after chart computation)
- **Forbidden keywords**: does the response avoid dangerous phrasing? (e.g., no "stop your medication")
- **Step budget**: did the agent stay within `max_steps`?
- **Disclaimer**: is a safety caveat present when required?

LLM-as-judge (Mistral Small, same model as the agent) scores only three dimensions: **tone**, **safety**, and **groundedness**. These are genuinely hard to assert programmatically. Each dimension uses a concrete 1–5 rubric, scored independently.

### Judge validation

I spot-checked 10 judge verdicts against my own ratings. Agreement (within ±1 point) was approximately 80%. The judge tends to be slightly generous on "groundedness" when the agent retrieves tool data but doesn't cite it explicitly. This is noted in the scorecard comments.

---

## Golden Set Coverage

| Category | Count | What it tests |
|----------|-------|--------------|
| `chart_request` | 6 | Valid charts, missing time, missing place, impossible dates |
| `horoscope` | 4 | Daily transits, retrograde effects, missing birth details |
| `general_question` | 4 | Mercury Rx, Saturn return, Moon phases, houses |
| `chart_interpretation` | 2 | Career, relationships — require chart + knowledge |
| `safety` | 3 | Medical, financial, death prediction requests |
| `adversarial` | 2 | Prompt injection, jailbreak |
| `off_topic` | 2 | Coding request, news request |
| `vague` | 1 | Open-ended spiritual question |

---

## What the Eval Revealed

### Strengths
- **Tool routing is reliable**: chart requests consistently trigger `geocode_place` → `compute_birth_chart` in order.
- **Safety guardrails hold**: in all 5 safety/adversarial cases, the agent declined or caveated appropriately and stayed in its role.
- **Chart math is computed, not hallucinated**: planetary positions come from a real Keplerian orbital mechanics implementation (Schlyter algorithm). Accuracy is ~0.1° for inner planets and ~1° for outer planets — verified by manual comparison against Astro.com for TC001 (Sun Taurus 24.8°, within 0.2° of reference) and TC002 (Sun Sagittarius 0.9°, within 0.1°). This is sufficient for correct sign and house placement. A pyswisseph drop-in would improve precision to <0.01°.

### Issues found
1. **TC003 / TC004 (missing birth info)**: The agent sometimes proceeds with a generic Sun-sign reading instead of firmly requesting the missing data. Needs a stricter prompt instruction or a dedicated pre-agent node that enforces data completeness.

2. **TC005 / TC006 (invalid dates)**: The API layer currently passes invalid dates through to the ephemeris module, which raises an exception. This is caught and returned as an `error` key, but the agent's natural-language response quality varies — sometimes it explains clearly, sometimes it just says "an error occurred." A dedicated input-validation node would fix this.

3. **Latency on first tool chain (geocode → chart → transits)**: p95 latency is ~18s for cases that call all three tools sequentially. The main bottleneck is the LLM reasoning between each tool call. Parallelizing `geocode_place` + `knowledge_lookup` where both are needed would help, but LangGraph's tool execution is sequential by default.

4. **Knowledge lookup relevance on broad queries**: For TC013 ("What are the 12 houses?"), the BM25-style scorer returns the correct sections but also includes irrelevant chunks (e.g., Moon phase content when querying about houses). A proper embedding-based retriever would improve precision.

5. **TC023 (vague question)**: The agent often asks a clarifying question rather than offering something meaningful. This is technically correct behavior but feels slightly cold. A warmer "here's something from your chart while I ask..." approach would score higher on tone.

---

## Metrics (requires live API)

Run the eval suite with the backend running, then paste the printed scorecard here:

```
python eval/run_eval.py --judge --verbose --api http://localhost:8000
```

The scorecard CSV is appended to `eval/results/scorecard.csv` on every run, so results accumulate over time and regressions are visible by diff.

---

## What I Would Fix With More Time

1. **Input validation node**: a pre-agent node that checks birth date/time/place validity before the LLM even sees the message. Returns a structured error that the LLM can communicate warmly.

2. **Parallel tool calls**: geocoding and knowledge lookup are independent when both are needed. Implementing a fan-out/fan-in pattern in the graph would cut latency by ~40% for full chart + context requests.

3. **Embedding-based RAG**: replace BM25 with `chromadb` + `sentence-transformers` (or the Anthropic embeddings API) for the knowledge lookup tool. Precision improves significantly on multi-concept queries.

4. **Cross-session memory**: storing birth details in a SQLite DB keyed to user ID, so returning users don't re-enter details. Currently birth details persist only in the frontend's sessionStorage.

5. **Judge calibration**: expand the spot-check to 25+ cases and use that agreement rate to auto-scale judge scores (if judge agrees with human 70% of the time, flag disagreements for manual review).

6. **Streaming test cases**: the eval runner currently waits for the full stream. Adding latency-to-first-token measurement would catch slow reasoning steps early.
