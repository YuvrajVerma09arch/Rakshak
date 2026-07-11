"""The five demo scenarios, end to end. Run: python demo.py

Everything here is the OFFLINE path (Drishti + local fallbacks) — no API keys,
no network. With keys in ../.env, scenario 2 escalates to the live Panchayat.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from app.agents.bhasha import format_warning
from app.agents.jaal import load_session, replay
from app.agents.orchestrator import convene
from app.capsule import RiskCapsule
from app.pipeline import analyze_offline
from app.scoring import is_ambiguous

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

LINE = "─" * 78


def show(title: str, capsule: RiskCapsule, note: str = "") -> None:
    v = capsule.verdict
    print(f"\n{LINE}\n{title}\n{LINE}")
    print(f"  text     : {capsule.raw_text[:70]}")
    print(f"  verdict  : {v.action.upper()}   evidence={v.evidence_score}  harm={v.harm_score}"
          + ("   [VAKEEL VETO]" if v.vakeel_veto else ""))
    for t in capsule.panchayat_trace:
        print(f"  trace    : {t.agent:<8} {t.ms:>5}ms  ₹{t.cost_inr:<6} {t.notes}")
    warning = format_warning(capsule)
    if warning:
        print("  bhasha   :")
        for line in warning.splitlines():
            print(f"     {line}")
    if note:
        print(f"  ▸ {note}")


async def main() -> None:
    print("\nRAKSHAK — Agent Panchayat demo (offline path, zero API keys needed)")

    # 1. Offline catch — airplane mode
    c1 = analyze_offline(
        "Congratulations! You won ₹50,000 in KBC lucky draw. Pay ₹499 processing fee now: unknown@upi",
        channel="sms", language="hi")
    show("DEMO 1 — Prize scam, airplane mode (Drishti only)", c1,
         "Caught offline, ₹0.00, in milliseconds. Works with no internet.")

    # 2. Ambiguous case — the Panchayat convenes (LLM if keys present, local fallback otherwise)
    c2 = analyze_offline(
        "Dear consumer your electricity bill was not updated. Pay ₹200 today or connection will be cut tonight. Contact officer 9812345670",
        channel="sms", language="hi")
    if is_ambiguous(c2.verdict):
        c2 = await convene(c2)
    show("DEMO 2 — Ambiguous utility threat (Jasoos ∥ Vakeel deliberate)", c2,
         "AI argues, deterministic policy decides. Full provenance trace above.")

    # 3. False-positive protection — a genuine payment sails through
    c3 = analyze_offline(
        "Beta, main hoon. 500 bhej dena ravi@okhdfc par, sabzi ke liye.",
        channel="whatsapp", language="hi", known_contacts={"ravi@okhdfc"})
    show("DEMO 3 — Legit payment to a known contact", c3,
         "ALLOW, silently. The defence side of the Panchayat exists so this never gets blocked.")

    # 4. Community immunity — blocklisted VPA via QR
    c4 = analyze_offline("upi://pay?pa=fraudhelp@upi&am=1500", channel="qr", language="gu")
    show("DEMO 4 — QR to community-blocklisted VPA (Gujarati warning)", c4,
         "User A's verified report now protects User B, from the local cache, offline.")

    # 5. Guardian mode — vulnerable user, critical harm
    c5 = analyze_offline(
        "Your electricity connection will be cut tonight. Pay ₹15,000 immediately or police case will be filed.",
        channel="sms", language="hi", vulnerability_mode=True)
    show("DEMO 5 — Elderly user, high amount → guardian approval", c5,
         "Sahara sends the guardian a risk card. Consent-based assisted safety.")

    # 6. Jaal — the honeypot replay (clearly labeled simulation)
    print(f"\n{LINE}\nDEMO 6 — Rakshak Jaal (जाल): honeypot session replay\n{LINE}")
    session = load_session()
    for event in replay(session):
        if "meta" in event:
            print(f"  [{event['meta']['label']}]")
            print(f"  persona: {event['meta']['persona']}")
        elif "extracted_indicators" in event:
            ind = event["extracted_indicators"]
            print(f"  ▸ extracted: VPAs={ind['vpas']} phones={ind['phones']}")
            print(f"  ▸ {event['outcome']}")
        else:
            speaker = "🕸 jaal   " if event["from"] == "jaal" else "☠ scammer"
            print(f"  {speaker}: {event['text'][:88]}")

    print(f"\n{LINE}\nAll six demos ran. Scam bots attack alone — Rakshak defends as a council.\n")


if __name__ == "__main__":
    asyncio.run(main())
