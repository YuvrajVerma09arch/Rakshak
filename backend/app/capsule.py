"""Risk Capsule — the single normalized object every channel feeds into.

Deterministic by design: no model call happens before a capsule exists, so the
offline path is complete and the provenance trace starts at t=0.
"""
from __future__ import annotations

import re
import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field

Channel = Literal["sms", "call", "upi", "qr", "whatsapp", "link"]
AskType = Literal["pay_money", "share_otp", "install_app", "click_link", "accept_collect", "unknown"]
Urgency = Literal["low", "medium", "high"]
Action = Literal["allow", "warn", "friction", "block", "guardian"]


class Actor(BaseModel):
    phone: Optional[str] = None
    vpa: Optional[str] = None
    known_to_user: bool = False
    reputation_score: float = 0.5  # 0 = confirmed bad, 1 = trusted


class Ask(BaseModel):
    type: AskType = "unknown"
    amount_inr: Optional[float] = None
    urgency: Urgency = "low"
    claimed_reason: Optional[str] = None


class PaymentRail(BaseModel):
    rail: Optional[str] = None  # upi_push | upi_collect | qr | link
    recipient_first_seen: bool = True
    qr_hash: Optional[str] = None


class Evidence(BaseModel):
    matched_rules: list[str] = Field(default_factory=list)
    reputation_hits: list[str] = Field(default_factory=list)
    similar_cases: list[str] = Field(default_factory=list)
    community_reports_24h: int = 0


class TraceEntry(BaseModel):
    agent: str
    ms: int = 0
    cost_inr: float = 0.0
    notes: str = ""


class Verdict(BaseModel):
    evidence_score: float = 0.0
    harm_score: float = 0.0
    action: Action = "allow"
    reasons: list[str] = Field(default_factory=list)
    vakeel_veto: bool = False


class RiskCapsule(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    channel: Channel = "sms"
    language: str = "hi"
    raw_text: str = ""
    actor: Actor = Field(default_factory=Actor)
    ask: Ask = Field(default_factory=Ask)
    payment_rail: PaymentRail = Field(default_factory=PaymentRail)
    evidence: Evidence = Field(default_factory=Evidence)
    verdict: Verdict = Field(default_factory=Verdict)
    panchayat_trace: list[TraceEntry] = Field(default_factory=list)
    vulnerability_mode: bool = False  # elderly / first-time-UPI / low-literacy profile


# --- deterministic extraction -------------------------------------------------

AMOUNT_RE = re.compile(r"(?:₹|rs\.?\s*|inr\s*)([\d,]+(?:\.\d+)?)|([\d,]+(?:\.\d+)?)\s*(?:rupees?|rupaye|रुपये)", re.I)
VPA_RE = re.compile(r"\b[\w.\-]{2,}@[a-z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+91[\s\-]?)?\b([6-9]\d{4}[\s\-]?\d{5})\b")
URL_RE = re.compile(r"https?://\S+|\b(?:bit\.ly|tinyurl\.com|cutt\.ly|is\.gd|t\.co|rb\.gy)/\S+", re.I)

HIGH_URGENCY = ["today", "aaj", "आज", "turant", "तुरंत", "abhi", "अभी", "immediately", "urgent",
                "24 hour", "last chance", "warna", "वरना", "tonight", "raat"]
MED_URGENCY = ["soon", "jaldi", "जल्दी", "this week", "pending"]

ASK_HINTS: list[tuple[AskType, list[str]]] = [
    ("share_otp", ["otp", "one time password", "pin batao", "pin share", "cvv"]),
    ("install_app", [".apk", "install", "anydesk", "teamviewer", "quick support", "screen shar"]),
    ("accept_collect", ["collect request", "payment request", "request accept", "approve request"]),
    ("pay_money", ["pay", "bhejo", "भेजो", "send", "transfer", "fee", "shulk", "शुल्क", "bharo", "भरो", "recharge"]),
    ("click_link", ["click", "link", "http", "bit.ly", "tinyurl"]),
]


def _first(pattern: re.Pattern, text: str) -> Optional[str]:
    m = pattern.search(text)
    return m.group(0) if m else None


def build_capsule(
    raw_text: str,
    channel: Channel = "sms",
    language: str = "hi",
    known_contacts: Optional[set[str]] = None,
    vulnerability_mode: bool = False,
) -> RiskCapsule:
    """Normalize one decision-moment event into a Risk Capsule. Pure function, no I/O."""
    text = raw_text.strip()
    known_contacts = known_contacts or set()

    vpa = _first(VPA_RE, text)
    phone = _first(PHONE_RE, text)
    url = _first(URL_RE, text)

    # Scams often quote two amounts (the prize and the fee) — the amount the user is
    # asked to MOVE is reliably the smaller one.
    amounts = [float(a.replace(",", "")) for pair in AMOUNT_RE.findall(text) for a in pair if a]
    amount = min(amounts) if amounts else None

    lower = text.lower()
    urgency: Urgency = "low"
    if any(k in lower for k in MED_URGENCY):
        urgency = "medium"
    if any(k in lower for k in HIGH_URGENCY):
        urgency = "high"

    ask_type: AskType = "unknown"
    for candidate, hints in ASK_HINTS:
        if any(h in lower for h in hints):
            ask_type = candidate
            break

    identity = vpa or phone
    known = bool(identity and identity in known_contacts)

    rail = None
    if channel == "qr":
        rail = "qr"
    elif ask_type == "accept_collect":
        rail = "upi_collect"
    elif vpa or ask_type == "pay_money":
        rail = "upi_push"
    elif url:
        rail = "link"

    return RiskCapsule(
        channel=channel,
        language=language,
        raw_text=text,
        actor=Actor(phone=phone, vpa=vpa, known_to_user=known),
        ask=Ask(type=ask_type, amount_inr=amount, urgency=urgency),
        payment_rail=PaymentRail(rail=rail, recipient_first_seen=not known),
        vulnerability_mode=vulnerability_mode,
    )
