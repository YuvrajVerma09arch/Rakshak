"""Jaal (जाल) — the honeypot agent. MVP = SIMULATED REPLAY, and every surface
that shows it must say so (architecture §2: never claim live engagement).

The replay demonstrates the loop: verified community report → Jaal engages →
extracted indicators (mule VPAs, backup phones) → back into Nigrani's
verification pipeline as evidence, not auto-blocks.

Roadmap (post-hackathon): live persona conversations over Groq (<100ms TTFT),
consent + legal review first. Precedent: O2's "Daisy" at telco scale in the UK.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

SESSIONS_DIR = Path(__file__).resolve().parents[3] / "data" / "jaal_sessions"


def load_session(session_id: str = "sample_session") -> dict:
    return json.loads((SESSIONS_DIR / f"{session_id}.json").read_text(encoding="utf-8"))


def replay(session: dict) -> Iterator[dict]:
    """Yields messages one by one — the frontend renders them with typing delays,
    clearly badged with session['label'] (SIMULATION)."""
    yield {"meta": {"label": session["label"], "persona": session["persona"],
                    "trigger": session["trigger"]}}
    for msg in session["messages"]:
        yield msg
    yield {"extracted_indicators": session["extracted_indicators"],
           "outcome": session["outcome"]}
