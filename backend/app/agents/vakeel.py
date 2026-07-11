"""Vakeel (वकील) — the defence lawyer. The USP agent.

Argues the transaction is LEGITIMATE. Runs with a separate context from Jasoos
so the two lines of reasoning are genuinely independent. Its veto can only
downgrade a block to friction (scoring.apply_vakeel enforces the asymmetry).

ROADMAP: deepen with user history ("has paid this biller 6 times"),
contact-graph signals, and merchant-VPA allowlists — the innocent-explanation
sources that make the veto genuinely smart.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass

from ..capsule import RiskCapsule, TraceEntry
from ..providers import ProviderNotConfigured
from ..providers import deepinfra

SYSTEM = """You are Vakeel, the defence-lawyer agent of Rakshak's Agent Panchayat.
Your ONLY job is to argue this transaction might be LEGITIMATE. Look for innocent
explanations: a real biller, a known merchant handle, a plausible personal payment,
a genuine reminder. Be honest — if there is no credible innocent explanation, say so.
Respond ONLY with JSON: {"veto": true|false, "confidence": float 0..1,
"argument": "one plain-language paragraph"}
veto=true means: a hard block would likely hurt a legitimate user here."""


@dataclass
class VakeelOpinion:
    veto: bool = False
    confidence: float = 0.0
    argument: str = ""
    trace: TraceEntry | None = None


def _local_defence(capsule: RiskCapsule) -> VakeelOpinion:
    """Deterministic fallback heuristics — conservative on purpose."""
    if capsule.actor.known_to_user:
        return VakeelOpinion(True, 0.8, "Recipient is a known contact of the user.")
    small = (capsule.ask.amount_inr or 0) < 100
    weak_rules = len(capsule.evidence.matched_rules) <= 1
    if small and weak_rules and not capsule.evidence.reputation_hits:
        return VakeelOpinion(True, 0.5, "Small amount, weak rule evidence, clean reputation — could be a genuine small payment.")
    return VakeelOpinion(False, 0.6, "No credible innocent explanation found by local heuristics.")


async def defend(capsule: RiskCapsule) -> VakeelOpinion:
    t0 = time.perf_counter()
    try:
        content, cost = await deepinfra.chat([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": capsule.model_dump_json(
                include={"raw_text", "channel", "language", "actor", "ask", "payment_rail", "evidence"})},
        ])
        raw = json.loads(re.search(r"\{.*\}", content, re.S).group(0))
        opinion = VakeelOpinion(bool(raw.get("veto")), float(raw.get("confidence", 0)),
                                raw.get("argument", ""))
        notes = "LLM opinion"
    except (ProviderNotConfigured, Exception) as exc:
        cost = 0.0
        opinion = _local_defence(capsule)
        notes = f"local fallback ({type(exc).__name__})"

    opinion.trace = TraceEntry(agent="vakeel", ms=int((time.perf_counter() - t0) * 1000),
                               cost_inr=cost, notes=f"{notes}; veto={opinion.veto}")
    return opinion
