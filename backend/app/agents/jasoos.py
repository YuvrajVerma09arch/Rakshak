"""Jasoos (जासूस) — the detective. Argues the SCAM side of the case.

Retrieval is local and deterministic (keyword scoring over data/scam_patterns/),
so the precedent step works offline; the LLM call sharpens the argument when a
key is present.

ROADMAP: this is the agent to deepen —
  1. swap keyword retrieval for BGE-M3 embeddings + Qdrant (multilingual recall)
  2. tune the prompt on real scam corpora; add few-shot kill-chain mappings
  3. feed the fraud-graph lookup (Postgres edges) as a second evidence source
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..capsule import RiskCapsule, TraceEntry
from ..providers import ProviderNotConfigured
from ..providers import deepinfra

PATTERNS_DIR = Path(__file__).resolve().parents[3] / "data" / "scam_patterns"

SYSTEM = """You are Jasoos, the detective agent of Rakshak's Agent Panchayat — a fraud
analyst for rural Indian digital payments. You argue the SCAM side of the case.
Given a Risk Capsule and retrieved precedents, map the message onto the scam kill-chain
(hook / pressure / trust_abuse / action_request / money_rail / evasion) and estimate how
strongly the evidence supports fraud.
Respond ONLY with JSON: {"evidence_delta": float between -0.1 and 0.25,
"kill_chain": [stages...], "argument": "one sharp paragraph, plain language",
"precedent": "best matching precedent name or null"}"""


@dataclass
class JasoosFinding:
    evidence_delta: float = 0.0
    kill_chain: list[str] = field(default_factory=list)
    argument: str = ""
    precedent: str | None = None
    trace: TraceEntry | None = None


def retrieve_precedents(text: str, k: int = 2) -> list[tuple[str, str]]:
    """Deterministic keyword-overlap retrieval over the curated corpus.
    ROADMAP: replace with Qdrant + BGE-M3 (see architecture §7.1)."""
    tokens = set(re.findall(r"[a-zऀ-ॿ]{3,}", text.lower()))
    scored = []
    for doc in sorted(PATTERNS_DIR.glob("*.md")):
        body = doc.read_text(encoding="utf-8")
        overlap = len(tokens & set(re.findall(r"[a-zऀ-ॿ]{3,}", body.lower())))
        scored.append((overlap, doc.stem, body))
    scored.sort(reverse=True)
    return [(name, body) for score, name, body in scored[:k] if score > 2]


async def investigate(capsule: RiskCapsule) -> JasoosFinding:
    t0 = time.perf_counter()
    precedents = retrieve_precedents(capsule.raw_text)
    capsule.evidence.similar_cases = [name for name, _ in precedents]

    try:
        content, cost = await deepinfra.chat([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps({
                "capsule": capsule.model_dump(include={"raw_text", "channel", "language", "actor", "ask", "payment_rail", "evidence"}),
                "precedents": [{"name": n, "text": b[:1200]} for n, b in precedents],
            }, ensure_ascii=False)},
        ])
        raw = json.loads(re.search(r"\{.*\}", content, re.S).group(0))
        finding = JasoosFinding(
            evidence_delta=max(-0.1, min(0.25, float(raw.get("evidence_delta", 0)))),
            kill_chain=raw.get("kill_chain", []),
            argument=raw.get("argument", ""),
            precedent=raw.get("precedent"),
        )
        notes = f"LLM verdict; precedent={finding.precedent}"
    except (ProviderNotConfigured, Exception) as exc:  # any failure → local fallback
        cost = 0.0
        finding = JasoosFinding(
            evidence_delta=min(0.15, 0.06 * len(precedents)),
            kill_chain=[],
            argument=(f"Matches known pattern(s): {', '.join(n for n, _ in precedents)}."
                      if precedents else "No strong precedent found locally."),
            precedent=precedents[0][0] if precedents else None,
        )
        notes = f"local fallback ({type(exc).__name__}); precedent={finding.precedent}"

    finding.trace = TraceEntry(agent="jasoos", ms=int((time.perf_counter() - t0) * 1000),
                               cost_inr=cost, notes=notes)
    return finding
