from app.capsule import build_capsule


def test_extracts_vpa_phone_and_fee_amount():
    c = build_capsule(
        "Congratulations! You won ₹50,000. Pay ₹499 processing fee to prize@upi or call 9812345670")
    assert c.actor.vpa == "prize@upi"
    assert c.actor.phone == "9812345670"
    # Two amounts quoted — the ask is always the smaller (the fee, not the prize)
    assert c.ask.amount_inr == 499.0
    assert c.ask.type == "pay_money"


def test_hindi_devanagari_amount_and_urgency():
    c = build_capsule("तुरंत 500 रुपये भेजो वरना खाता बंद हो जाएगा")
    assert c.ask.amount_inr == 500.0
    assert c.ask.urgency == "high"


def test_otp_ask_detected_before_pay():
    c = build_capsule("Sir please share OTP to receive your refund of Rs 2000")
    assert c.ask.type == "share_otp"


def test_known_contact_marked():
    c = build_capsule("bhej dena ravi@okhdfc par", known_contacts={"ravi@okhdfc"})
    assert c.actor.known_to_user
    assert not c.payment_rail.recipient_first_seen


def test_qr_channel_sets_rail():
    c = build_capsule("upi://pay?pa=x@upi&am=100", channel="qr")
    assert c.payment_rail.rail == "qr"
