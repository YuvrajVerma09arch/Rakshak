"""DeepInfra — the Panchayat's workhorse brain (OpenAI-compatible).

Llama 3.3 70B Turbo at $0.10/$0.32 per M tokens (verified Jul 2026). One
escalated case (Jasoos + Vakeel) costs ≈ ₹0.15 — that number goes on a slide.
"""
from __future__ import annotations

import os

import httpx

from . import ProviderNotConfigured

BASE_URL = "https://api.deepinfra.com/v1/openai"
DEFAULT_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

# $/M tokens for the default model — used to stamp cost_inr into the provenance trace.
USD_IN, USD_OUT, USD_TO_INR = 0.10, 0.32, 84.0


async def chat(messages: list[dict], model: str = DEFAULT_MODEL, temperature: float = 0.2,
               max_tokens: int = 700) -> tuple[str, float]:
    """Returns (content, cost_inr)."""
    key = os.getenv("DEEPINFRA_API_KEY")
    if not key:
        raise ProviderNotConfigured("DEEPINFRA_API_KEY not set")
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "messages": messages, "temperature": temperature,
                  "max_tokens": max_tokens},
        )
        r.raise_for_status()
        data = r.json()
    usage = data.get("usage", {})
    cost_inr = ((usage.get("prompt_tokens", 0) * USD_IN
                 + usage.get("completion_tokens", 0) * USD_OUT) / 1_000_000) * USD_TO_INR
    return data["choices"][0]["message"]["content"], round(cost_inr, 4)
