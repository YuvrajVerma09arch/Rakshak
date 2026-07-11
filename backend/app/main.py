"""Rakshak API.

POST /analyze       one decision-moment event → scored Risk Capsule (+ Panchayat if ambiguous)
POST /report        community scam report → Nigrani trust pipeline (village promotion at 3 reporters)
GET  /scenarios     the demo preset scenarios the frontend renders as one-tap chips
GET  /jaal/replay   the simulated honeypot session for the demo
POST /speak         Bhasha warning as WAV audio (503 without SARVAM_API_KEY — text path never breaks)
GET  /health

ROADMAP: /voice-query (Saaras ASR in → pipeline → Bulbul out) and WebSocket
streaming of the Panchayat trace for a live Command-Deck-style view.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import nigrani
from .agents import bhasha, jaal
from .agents.orchestrator import convene
from .capsule import Channel, RiskCapsule
from .pipeline import analyze_offline
from .providers import ProviderNotConfigured
from .scoring import is_ambiguous

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

app = FastAPI(title="Rakshak — Agentic Trust Firewall", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo deployment; pin to the frontend origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str
    channel: Channel = "sms"
    language: str = "hi"
    online: bool = True                      # False simulates airplane mode: Drishti only
    vulnerability_mode: bool = False
    known_contacts: Optional[list[str]] = None


class AnalyzeResponse(BaseModel):
    capsule: RiskCapsule
    warning_text: str
    panchayat_convened: bool


class ReportRequest(BaseModel):
    identifier: str = Field(..., description="VPA, phone number, or URL to report")
    reporter_id: str = "anonymous"
    reason: str = ""


class SpeakRequest(BaseModel):
    text: str
    language: str = "hi"


# The five stage-demo scenarios — served to the frontend so the UI and demo.py
# can never drift apart.
SCENARIOS = [
    {"id": "prize", "title": "Prize / KBC lottery", "channel": "sms", "language": "hi",
     "online": False, "vulnerability_mode": False, "known_contacts": [],
     "text": "Congratulations! You won ₹50,000 in KBC lucky draw. Pay ₹499 processing fee now: unknown@upi",
     "note": "Airplane mode — caught offline by Drishti alone, ₹0.00"},
    {"id": "electricity", "title": "Electricity cut threat", "channel": "sms", "language": "hi",
     "online": True, "vulnerability_mode": False, "known_contacts": [],
     "text": "Dear consumer your electricity bill was not updated. Pay ₹200 today or connection will be cut tonight. Contact officer 9812345670",
     "note": "Ambiguous — the Panchayat convenes: Jasoos vs Vakeel"},
    {"id": "legit", "title": "Legit payment to family", "channel": "whatsapp", "language": "hi",
     "online": True, "vulnerability_mode": False, "known_contacts": ["ravi@okhdfc"],
     "text": "Beta, main hoon. 500 bhej dena ravi@okhdfc par, sabzi ke liye.",
     "note": "Known contact — must sail through silently (false-positive protection)"},
    {"id": "qr", "title": "QR to blocklisted VPA", "channel": "qr", "language": "gu",
     "online": False, "vulnerability_mode": False, "known_contacts": [],
     "text": "upi://pay?pa=fraudhelp@upi&am=1500",
     "note": "Community immunity — User A's report protects User B, offline, in Gujarati"},
    {"id": "guardian", "title": "Digital-arrest pressure on elder", "channel": "sms", "language": "hi",
     "online": False, "vulnerability_mode": True, "known_contacts": [],
     "text": "Your electricity connection will be cut tonight. Pay ₹15,000 immediately or police case will be filed.",
     "note": "Vulnerable-user profile — routes to guardian approval (Sahara)"},
]


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    capsule = analyze_offline(
        req.text, req.channel, req.language,
        known_contacts=set(req.known_contacts or []),
        vulnerability_mode=req.vulnerability_mode,
    )
    convened = False
    if req.online and is_ambiguous(capsule.verdict):
        capsule = await convene(capsule)
        convened = True
    return AnalyzeResponse(capsule=capsule, warning_text=bhasha.format_warning(capsule),
                           panchayat_convened=convened)


@app.post("/report")
def report(req: ReportRequest) -> dict:
    if not req.identifier.strip():
        raise HTTPException(422, "identifier must not be empty")
    return nigrani.submit_report(req.identifier, req.reporter_id, req.reason)


@app.get("/scenarios")
def scenarios() -> list[dict]:
    return SCENARIOS


@app.get("/jaal/replay")
def jaal_replay() -> list[dict]:
    return list(jaal.replay(jaal.load_session()))


@app.post("/speak")
async def speak(req: SpeakRequest) -> Response:
    try:
        audio = await bhasha.sarvam.text_to_speech(req.text, language=req.language)
    except ProviderNotConfigured:
        raise HTTPException(503, "SARVAM_API_KEY not configured — text warnings still work")
    return Response(content=audio, media_type="audio/wav")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": app.version,
            "council": ["drishti", "jasoos", "vakeel", "bhasha", "sahara", "nigrani", "jaal"]}
