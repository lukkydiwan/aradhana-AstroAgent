"""
RAG tool over the curated astrology knowledge base.
Uses BM25-style keyword scoring to find relevant chunks.
"""

import re
from pathlib import Path
from langchain_core.tools import tool

_KNOWLEDGE_PATH = Path(__file__).parent.parent.parent / "data" / "astrology_knowledge.md"


def _load_chunks() -> list[tuple[str, str]]:
    """Split the knowledge file into (heading, body) chunks."""
    text = _KNOWLEDGE_PATH.read_text(encoding="utf-8")
    sections = re.split(r"\n(?=#{1,3} )", text)
    chunks: list[tuple[str, str]] = []
    for section in sections:
        lines = section.strip().splitlines()
        if not lines:
            continue
        heading = lines[0].lstrip("#").strip()
        body = "\n".join(lines[1:]).strip()
        if body:
            chunks.append((heading, body))
    return chunks


_CHUNKS: list[tuple[str, str]] = _load_chunks()


def _score(query: str, heading: str, body: str) -> float:
    """Simple overlap-based relevance score (no heavy dependencies)."""
    query_tokens = set(re.findall(r"\w+", query.lower()))
    target = (heading + " " + body).lower()
    target_tokens = set(re.findall(r"\w+", target))
    overlap = query_tokens & target_tokens
    if not query_tokens:
        return 0.0
    # Boost heading matches
    heading_tokens = set(re.findall(r"\w+", heading.lower()))
    heading_bonus = len(query_tokens & heading_tokens) * 2
    return (len(overlap) + heading_bonus) / len(query_tokens)


@tool
def knowledge_lookup(query: str, top_k: int = 3) -> list[dict]:
    """
    Search the Aradhana astrology reference notes for information relevant to
    the query. Use this to ground interpretations in curated knowledge.

    Args:
        query: Natural-language question or topic, e.g. "Saturn in 7th house meaning"
        top_k: Number of top-matching sections to return (1–5).

    Returns:
        List of dicts with 'heading' and 'content' keys, sorted by relevance.
    """
    top_k = max(1, min(5, top_k))
    scored = [
        (_score(query, h, b), h, b)
        for h, b in _CHUNKS
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"heading": h, "content": b, "relevance_score": round(s, 3)}
        for s, h, b in scored[:top_k]
        if s > 0
    ] or [{"heading": "General", "content": _CHUNKS[0][1], "relevance_score": 0.0}]
