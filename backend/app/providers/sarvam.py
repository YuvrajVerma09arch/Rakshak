"""Sarvam AI — the council's ears (Saaras v3 ASR), mouth (Bulbul v3 TTS), and
Indic phrasing brain (Sarvam-30B; Sarvam-M is deprecated, do not use it).

ROADMAP: verify request/response shapes against https://docs.sarvam.ai before
the voice demo — endpoint payloads below follow the docs as of Jul 2026 but Sarvam
iterates fast (Bulbul v3 caps at 2,500 chars/request; Saaras supports codemix mode).
"""
from __future__ import annotations

import base64
import os

import httpx

from . import ProviderNotConfigured

BASE_URL = "https://api.sarvam.ai"
CHAT_MODEL = "sarvam-30b"
TTS_MODEL = "bulbul:v3"
ASR_MODEL = "saaras:v3"

LANG_CODES = {"hi": "hi-IN", "gu": "gu-IN", "en": "en-IN"}


def _headers() -> dict:
    key = os.getenv("SARVAM_API_KEY")
    if not key:
        raise ProviderNotConfigured("SARVAM_API_KEY not set")
    return {"api-subscription-key": key}


async def chat(messages: list[dict], model: str = CHAT_MODEL, temperature: float = 0.3) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={**_headers(), "Authorization": f"Bearer {os.getenv('SARVAM_API_KEY')}"},
            json={"model": model, "messages": messages, "temperature": temperature},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


async def text_to_speech(text: str, language: str = "hi", speaker: str | None = None) -> bytes:
    """Returns WAV bytes. Bulbul v3: 35+ voices, sub-250ms first byte on the
    WebSocket API — REST is fine for pre-rendered demo warnings."""
    payload = {
        "text": text[:2400],  # Bulbul v3 request cap is 2,500 chars
        "target_language_code": LANG_CODES.get(language, "hi-IN"),
        "model": TTS_MODEL,
    }
    if speaker:
        payload["speaker"] = speaker
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{BASE_URL}/text-to-speech", headers=_headers(), json=payload)
        r.raise_for_status()
        return base64.b64decode(r.json()["audios"][0])


async def speech_to_text(audio_wav: bytes, mode: str = "transcribe") -> str:
    """Saaras v3 — 22 Indian languages + English; modes: transcribe / translate /
    verbatim / translit / codemix."""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{BASE_URL}/speech-to-text",
            headers=_headers(),
            data={"model": ASR_MODEL, "mode": mode},
            files={"file": ("query.wav", audio_wav, "audio/wav")},
        )
        r.raise_for_status()
        return r.json()["transcript"]
