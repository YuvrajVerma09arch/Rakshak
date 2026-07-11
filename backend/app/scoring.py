"""Evidence + Harm scoring and the intervention policy ladder.

The design rule that wins the technical-credibility question: LLM agents
contribute *arguments and evidence deltas*; this module — deterministic,
reviewable, ~60 lines — always makes the final call. Vakeel's veto can move a
verdict DOWN the ladder (block → friction), never up.
"""
from __future__ import annotations

from .capsule import Action, RiskCapsule, Verdict
from .reputation import ReputationResult
from .rules.engine import RuleEngine, RuleHit

DEFAULT_BASELINE_INR = 2000.0  # typical transaction range; per-user in production


def evidence_score(capsule: RiskCapsule, hits: list[RuleHit], rep: ReputationResult) -> float:
    score = RuleEngine.evidence_contribution(hits)          # capped at 0.70
    score += rep.contribution                               # blocklist + report velocity
    if not capsule.actor.known_to_user and capsule.ask.type in ("pay_money", "accept_collect", "share_otp"):
        score += 0.10                                        # unknown actor asking for money/credentials
    if capsule.payment_rail.recipient_first_seen and capsule.ask.type == "pay_money":
        score += 0.05
    return min(1.0, round(score, 3))


def harm_score(capsule: RiskCapsule, baseline_inr: float = DEFAULT_BASELINE_INR) -> float:
    score = 0.0
    amount = capsule.ask.amount_inr
    if amount is None:
        score += 0.05
    elif amount >= baseline_inr:
        score += 0.30
    elif amount >= 0.25 * baseline_inr:
        score += 0.20
    else:
        score += 0.10
    if not capsule.actor.known_to_user:
        score += 0.25
    if capsule.payment_rail.rail in ("upi_push", "qr", "upi_collect"):
        score += 0.15                                        # irreversible rail (~6% chargeback recovery)
    score += {"high": 0.15, "medium": 0.05, "low": 0.0}[capsule.ask.urgency]
    if capsule.vulnerability_mode:
        score += 0.20
    return min(1.0, round(score, 3))


def decide(evidence: float, harm: float, rep: ReputationResult, vulnerability_mode: bool) -> Action:
    if rep.confirmed_bad and evidence >= 0.85:
        return "guardian" if vulnerability_mode else "block"
    if harm >= 0.90 and evidence >= 0.60:
        return "guardian"
    if evidence >= 0.70 or harm >= 0.75:
        return "friction"
    if evidence >= 0.45:
        return "warn"
    return "allow"


def build_verdict(capsule: RiskCapsule, hits: list[RuleHit], rep: ReputationResult) -> Verdict:
    ev, hm = evidence_score(capsule, hits, rep), harm_score(capsule)
    reasons = [h.rule.reason(capsule.language) for h in hits]
    reasons += [f"Reported by the community: {h}" for h in rep.hits]
    return Verdict(
        evidence_score=ev,
        harm_score=hm,
        action=decide(ev, hm, rep, capsule.vulnerability_mode),
        reasons=reasons,
    )


def apply_vakeel(verdict: Verdict, veto: bool, argument: str) -> Verdict:
    """Defence can downgrade a block to friction — never escalate. See §6 of the architecture."""
    if veto and verdict.action == "block":
        verdict.action = "friction"
        verdict.vakeel_veto = True
        verdict.reasons.append(f"Vakeel (defence): {argument}")
    return verdict


def is_ambiguous(verdict: Verdict) -> bool:
    """The band where convening the Panchayat is worth tokens: not obviously safe,
    not already confirmed-bad."""
    return 0.40 <= verdict.evidence_score < 0.85
