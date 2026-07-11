from app.pipeline import analyze_offline


def test_prize_scam_gets_friction_offline():
    c = analyze_offline(
        "Congratulations! You won ₹50,000 in KBC lucky draw. Pay ₹499 processing fee now: unknown@upi")
    assert c.verdict.action == "friction"
    assert "prize_lure" in c.evidence.matched_rules
    assert c.panchayat_trace[0].agent == "drishti"
    assert c.panchayat_trace[0].cost_inr == 0.0


def test_blocklisted_vpa_blocks():
    c = analyze_offline("upi://pay?pa=fraudhelp@upi&am=1500", channel="qr", language="gu")
    assert c.verdict.action == "block"
    assert any("fraudhelp@upi" in h for h in c.evidence.reputation_hits)


def test_known_contact_allows():
    c = analyze_offline("Beta 500 bhej dena ravi@okhdfc par",
                        channel="whatsapp", known_contacts={"ravi@okhdfc"})
    assert c.verdict.action == "allow"


def test_vulnerable_high_harm_routes_to_guardian():
    c = analyze_offline(
        "Your electricity connection will be cut tonight. Pay ₹15,000 immediately or police case will be filed.",
        vulnerability_mode=True)
    assert c.verdict.action == "guardian"
