"""Bhasha (भाषा) — the voice of the council.

Two layers, by design:
  1. format_warning(): template-based, offline, free — reasons come from the rule
     pack's own reason_hi/reason_gu/reason_en fields. This is why airplane-mode
     demos still speak the user's language (as text; pre-render audio for demos).
  2. speak(): Sarvam Bulbul v3 TTS for actual audio (needs SARVAM_API_KEY).

ROADMAP: add the inbound voice-query path (Saaras ASR → pipeline → speak)
as a /voice-query endpoint for demo #3.
"""
from __future__ import annotations

from ..capsule import RiskCapsule
from ..providers import sarvam

HEADLINES = {
    "warn":     {"hi": "रुकिए। यह धोखा हो सकता है।", "gu": "થોભો. આ છેતરપિંડી હોઈ શકે છે.", "en": "Wait. This may be a scam."},
    "friction": {"hi": "सावधान! यह बहुत हद तक धोखा है।", "gu": "સાવધાન! આ મોટા ભાગે છેતરપિંડી છે.", "en": "Careful! This is very likely a scam."},
    "block":    {"hi": "यह पक्का धोखा है। पैसे मत भेजिए।", "gu": "આ પાકી છેતરપિંડી છે. પૈસા મોકલશો નહીં.", "en": "This is a confirmed scam. Do not pay."},
    "guardian": {"hi": "बड़ा खतरा! आपके अभिभावक से पूछा जा रहा है।", "gu": "મોટું જોખમ! તમારા વાલીને પૂછવામાં આવી રહ્યું છે.", "en": "High risk! Your guardian is being asked."},
}
SAFE_STEP = {
    "hi": "सुरक्षित कदम: पैसे न भेजें। अपने बैंक से पूछें या 1930 पर साइबर धोखाधड़ी की शिकायत करें।",
    "gu": "સુરક્ષિત પગલું: પૈસા ન મોકલો. તમારી બેંકને પૂછો અથવા 1930 પર ફરિયાદ કરો.",
    "en": "Safe step: do not pay. Ask your bank, or report financial cyber fraud at 1930.",
}
REASON_LABEL = {"hi": "कारण", "gu": "કારણ", "en": "Reason"}


def format_warning(capsule: RiskCapsule, max_reasons: int = 3) -> str:
    """Spoken-style warning text in the capsule's language. Offline, free."""
    lang = capsule.language if capsule.language in ("hi", "gu", "en") else "hi"
    action = capsule.verdict.action
    if action == "allow":
        return ""
    lines = [HEADLINES[action][lang]]
    for i, reason in enumerate(capsule.verdict.reasons[:max_reasons], 1):
        lines.append(f"{REASON_LABEL[lang]} {i}: {reason}")
    lines.append(SAFE_STEP[lang])
    return "\n".join(lines)


async def speak(capsule: RiskCapsule) -> bytes:
    """Render the warning as audio via Bulbul v3. Raises ProviderNotConfigured without a key."""
    return await sarvam.text_to_speech(format_warning(capsule), language=capsule.language)
