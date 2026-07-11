# RAKSHAK (रक्षक) — The Agentic Trust Firewall

An **Agent Panchayat** for rural digital payments: a council of specialist AI agents that
convenes in the three seconds before money moves — offline when it can be, sovereign-AI-powered
when it must be, community-fed so every verified report protects the next user.

*Scam bots attack alone. Rakshak defends as a council.*

**Architecture:** `RAKSHAK_Architecture_v3_Agentic.md` (v3, supersedes v2).

## Run it

### One command (Docker)

```bash
docker compose up --build
# UI  → http://localhost:8080        (try http://localhost:8080/?scenario=prize)
# API → http://localhost:8000/docs
```

### Local dev (zero API keys needed)

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python demo.py                      # 6 demo scenarios, fully offline
uvicorn app.main:app --reload       # API at http://127.0.0.1:8000/docs
python -m pytest tests/ -q          # 24 tests

# frontend (second terminal)
cd frontend
npm install && npm run dev          # http://localhost:5173 (proxies /api → :8000)
```

The deterministic spine (Capsule Builder → Drishti rules → reputation → Evidence/Harm scoring →
intervention ladder) works **completely offline and free**. API keys only make the Panchayat
smarter (Jasoos/Vakeel LLM deliberation, Bhasha voice) — every agent has a deterministic local
fallback, so the demo can never die on stage.

## Stage demo (deep links)

| URL | What it shows |
|---|---|
| `/?scenario=prize` | KBC prize scam caught in airplane mode — ₹0, milliseconds |
| `/?scenario=electricity` | Ambiguous threat — the Panchayat convenes, Jasoos vs Vakeel |
| `/?scenario=legit` | Payment to a known contact sails through — false-positive protection |
| `/?scenario=qr` | QR to a community-blocklisted VPA — blocked offline, warning in Gujarati |
| `/?scenario=guardian` | Elder profile + ₹15,000 pressure — routed to guardian approval |

Plus the **Jaal — Honeypot** tab: a replay of the decoy persona wasting a scammer's time and
extracting mule VPAs (clearly badged SIMULATION — live engagement is a roadmap item).

## The council

| Agent | Job | Needs a key? |
|---|---|---|
| Capsule Builder | raw text/QR/transcript → normalized Risk Capsule | no |
| Drishti (दृष्टि) | offline rule packs + local blocklist, decides ~80% of events | no |
| Jasoos (जासूस) | detective — retrieves scam precedents, argues SCAM | DeepInfra (falls back to local retrieval) |
| Vakeel (वकील) | defence lawyer — argues LEGIT, can veto a block down to friction | DeepInfra (falls back to heuristics) |
| Bhasha (भाषा) | voice-first explanation, hi/gu/en | Sarvam for audio (text templates work offline) |
| Sahara (सहारा) | guardian approval card | no |
| Nigrani (निगरानी) | community reports → blocklist promotion (3 reporters = village level) | no |
| Jaal (जाल) | honeypot — **simulated replay in MVP** | no (replay) |

The design rule that holds it together: **LLM agents contribute arguments and evidence deltas;
the deterministic policy in `scoring.py` always makes the final call.** Vakeel's veto can move a
verdict down the ladder (block → friction), never up.

## API

| Endpoint | What it does |
|---|---|
| `POST /analyze` | decision-moment event → scored Risk Capsule (+ Panchayat when ambiguous) |
| `POST /report` | community scam report → Nigrani promotion pipeline |
| `GET /scenarios` | the 5 demo presets the UI renders as chips |
| `GET /jaal/replay` | the simulated honeypot session |
| `POST /speak` | Bhasha warning as WAV via Sarvam Bulbul (503 without key — text never breaks) |
| `GET /health` | liveness + council roster |

## Keys (`cp .env.example .env` — all optional)

- `DEEPINFRA_API_KEY` — https://deepinfra.com ($1 free, no card) — Jasoos/Vakeel deliberation
- `SARVAM_API_KEY` — https://dashboard.sarvam.ai (free signup credits) — voice in/out
- `GROQ_API_KEY` — https://console.groq.com (free tier) — low-latency path
- `CEREBRAS_API_KEY` — https://cloud.cerebras.ai (1M tokens/day free) — fallback

Unit economics: Drishti path ₹0.00 · escalated Panchayat case ≈ ₹0.15 (Llama 3.3 70B on DeepInfra).

## Layout

```
backend/app/capsule.py        Risk Capsule models + deterministic extractor
backend/app/rules/            ScamDSL engine + core_v1.yaml pack (en/hi/gu/Hinglish)
backend/app/reputation.py     local blocklist cache (community immunity, offline)
backend/app/scoring.py        Evidence + Harm + policy ladder + Vakeel veto merge
backend/app/pipeline.py       the offline path, end to end
backend/app/nigrani.py        report store + village-level promotion
backend/app/agents/           Sarpanch orchestrator + the council
backend/app/providers/        DeepInfra / Sarvam / Groq thin clients
backend/tests/                24 tests (capsule, rules, scoring, pipeline, API)
backend/demo.py               the 6 demo scenarios end to end
frontend/                     React + TS decision screen, trace timeline, Jaal replay
data/                         blocklist, scam-pattern corpus, honeypot transcript
.github/workflows/ci.yml     backend tests + offline demo + frontend build + compose build
docker-compose.yml            one-command deploy (nginx + uvicorn)
```
