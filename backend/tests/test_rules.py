from app.rules.engine import RuleEngine, get_engine


def test_packs_load_and_have_multilingual_reasons():
    engine = get_engine()
    assert len(engine.rules) >= 10
    for rule in engine.rules:
        assert rule.reasons.get("en"), f"{rule.id} missing English reason"
        assert rule.reasons.get("hi"), f"{rule.id} missing Hindi reason"


def test_prize_and_fee_rules_fire():
    hits = {h.id for h in get_engine().match(
        "Congratulations you won ₹50,000 lucky draw, pay ₹499 processing fee")}
    assert "prize_lure" in hits
    assert "processing_fee" in hits


def test_hindi_pattern_fires():
    hits = {h.id for h in get_engine().match("किसी को मत बताना, OTP बताओ")}
    assert "isolation" in hits
    assert "otp_request" in hits


def test_benign_text_matches_nothing():
    assert get_engine().match("Chai peene aa jao shaam ko, sab thik hai") == []


def test_rule_only_evidence_is_capped():
    hits = get_engine().match(
        "Congratulations winner! KYC expired, share OTP, install anydesk .apk, "
        "pay processing fee today only or account blocked, police case, don't tell anyone "
        "bit.ly/x electricity connection cut")
    assert len(hits) >= 6
    assert RuleEngine.evidence_contribution(hits) == 0.70  # rules alone can never hard-block
