"""Sarpanch (सरपंच) — chairs the Agent Panchayat.

Protocol: Drishti has already scored (pipeline.analyze_offline). If the verdict
is ambiguous, Sarpanch convenes Jasoos and Vakeel IN PARALLEL, merges their
findings through the deterministic policy (scoring.py — the LLMs argue, the
policy decides), and appends everything to the provenance trace.

convene() below is the reliable plain-asyncio implementation. build_langgraph()
exposes the same protocol as a LangGraph graph for checkpointing/visualization —
ROADMAP: extend the graph with Bhasha and Sahara nodes and wire
checkpointing for the replay UI.
"""
from __future__ import annotations

import asyncio

from ..capsule import RiskCapsule
from ..reputation import get_cache
from ..scoring import apply_vakeel, decide
from . import jasoos, vakeel


async def convene(capsule: RiskCapsule) -> RiskCapsule:
    """Jasoos ∥ Vakeel → deterministic verdict merge. Mutates and returns the capsule."""
    finding, opinion = await asyncio.gather(jasoos.investigate(capsule), vakeel.defend(capsule))

    v = capsule.verdict
    v.evidence_score = round(min(1.0, max(0.0, v.evidence_score + finding.evidence_delta)), 3)
    if finding.argument:
        v.reasons.append(f"Jasoos (detective): {finding.argument}")

    rep = get_cache().lookup(capsule)
    v.action = decide(v.evidence_score, v.harm_score, rep, capsule.vulnerability_mode)
    capsule.verdict = apply_vakeel(v, opinion.veto, opinion.argument)
    if not opinion.veto and opinion.argument:
        v.reasons.append(f"Vakeel (defence): {opinion.argument}")

    for trace in (finding.trace, opinion.trace):
        if trace:
            capsule.panchayat_trace.append(trace)
    return capsule


def build_langgraph():
    """Optional LangGraph wrapper around the same protocol (safe to ignore if
    langgraph isn't installed — convene() is the source of truth)."""
    from langgraph.graph import END, START, StateGraph

    async def panchayat_node(state: dict) -> dict:
        state["capsule"] = await convene(state["capsule"])
        return state

    graph = StateGraph(dict)
    graph.add_node("panchayat", panchayat_node)
    graph.add_edge(START, "panchayat")
    graph.add_edge("panchayat", END)
    return graph.compile()
