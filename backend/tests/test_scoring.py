from app.capsule import Verdict
from app.reputation import ReputationResult
from app.scoring import apply_vakeel, decide, is_ambiguous


def _rep(confirmed=False):
    return ReputationResult(hits=[], contribution=0.0, confirmed_bad=confirmed,
                            community_reports_24h=0)


def test_ladder_thresholds():
    assert decide(0.30, 0.30, _rep(), False) == "allow"
    assert decide(0.50, 0.30, _rep(), False) == "warn"
    assert decide(0.75, 0.50, _rep(), False) == "friction"
    assert decide(0.90, 0.50, _rep(confirmed=True), False) == "block"


def test_vulnerable_user_gets_guardian_not_block():
    assert decide(0.90, 0.50, _rep(confirmed=True), True) == "guardian"
    assert decide(0.65, 0.95, _rep(), True) == "guardian"


def test_vakeel_veto_downgrades_block_but_never_escalates():
    v = Verdict(evidence_score=0.9, harm_score=0.5, action="block")
    v = apply_vakeel(v, veto=True, argument="known biller")
    assert v.action == "friction" and v.vakeel_veto

    w = Verdict(evidence_score=0.5, harm_score=0.3, action="warn")
    w = apply_vakeel(w, veto=True, argument="whatever")
    assert w.action == "warn"  # veto only ever moves block → friction


def test_ambiguity_band():
    assert is_ambiguous(Verdict(evidence_score=0.55))
    assert not is_ambiguous(Verdict(evidence_score=0.20))
    assert not is_ambiguous(Verdict(evidence_score=0.90))
