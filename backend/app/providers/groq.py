"""Groq — lowest time-to-first-token (<100ms). Used where latency IS the product:
the live voice-query demo and (roadmap) Jaal's real-time scammer conversations.
Free tier, no card. OpenAI-compatible, so this file is deliberately tiny."""
from __future__ import annotations

import os

import httpx

from . import ProviderNotConfigured

BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"


async def chat(messages: list[dict], model: str = DEFAULT_MODEL, temperature: float = 0.4,
               max_tokens: int = 500) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ProviderNotConfigured("GROQ_API_KEY not set")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "messages": messages, "temperature": temperature,
                  "max_tokens": max_tokens},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
