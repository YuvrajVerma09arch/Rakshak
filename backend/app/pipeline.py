"""The offline path, end to end: raw event → capsule → Drishti → verdict.

Zero network, zero tokens, <50ms. This is the path that must never break —
everything agentic is an optional upgrade on top of it.
"""
from __future__ import annotations

import time
from typing import Optional

from .capsule import Channel, RiskCapsule, TraceEntry, build_capsule
from .reputation import get_cache
from .rules.engine import get_engine
from .scoring import build_verdict, is_ambiguous


def analyze_offline(
    raw_text: str,
    channel: Channel = "sms",
    language: str = "hi",
    known_contacts: Optional[set[str]] = None,
    vulnerability_mode: bool = False,
) -> RiskCapsule:
    t0 = time.perf_counter()
    capsule = build_capsule(raw_text, channel, language, known_contacts, vulnerability_mode)

    hits = get_engine().match(capsule.raw_text)
    rep = get_cache().lookup(capsule)

    capsule.evidence.matched_rules = [h.id for h in hits]
    capsule.evidence.reputation_hits = rep.hits
    capsule.evidence.community_reports_24h = rep.community_reports_24h
    capsule.verdict = build_verdict(capsule, hits, rep)

    capsule.panchayat_trace.append(
        TraceEntry(
            agent="drishti",
            ms=int((time.perf_counter() - t0) * 1000),
            cost_inr=0.0,
            notes=f"rules={capsule.evidence.matched_rules or 'none'}; "
                  f"reputation={rep.hits or 'clean'}; "
                  f"{'AMBIGUOUS — recommend convening Panchayat' if is_ambiguous(capsule.verdict) else 'confident'}",
        )
    )
    return capsule
