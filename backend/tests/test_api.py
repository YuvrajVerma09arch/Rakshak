import json

import pytest
from fastapi.testclient import TestClient

from app import nigrani, reputation
from app.main import app

client = TestClient(app)


@pytest.fixture()
def isolated_stores(tmp_path, monkeypatch):
    """Point Nigrani + reputation at throwaway files so tests never touch real data."""
    blocklist = tmp_path / "blocklist.json"
    blocklist.write_text(json.dumps({"vpas": {}, "phones": {}, "urls": {}}))
    cache = reputation.ReputationCache(blocklist)
    monkeypatch.setattr(reputation, "_cache", cache)
    monkeypatch.setattr(nigrani, "REPORTS_PATH", tmp_path / "reports.jsonl")
    yield
    monkeypatch.setattr(reputation, "_cache", None)


def test_health():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert "vakeel" in body["council"]


def test_analyze_offline_mode_never_convenes():
    r = client.post("/analyze", json={
        "text": "Congratulations! You won ₹50,000. Pay ₹499 processing fee now: unknown@upi",
        "online": False,
    }).json()
    assert r["capsule"]["verdict"]["action"] == "friction"
    assert r["panchayat_convened"] is False
    assert "रुक" in r["warning_text"] or "सावधान" in r["warning_text"]


def test_scenarios_are_served_and_analyzable():
    scenarios = client.get("/scenarios").json()
    assert len(scenarios) == 5
    for s in scenarios:
        r = client.post("/analyze", json={
            "text": s["text"], "channel": s["channel"], "language": s["language"],
            "online": False, "vulnerability_mode": s["vulnerability_mode"],
            "known_contacts": s["known_contacts"],
        })
        assert r.status_code == 200


def test_jaal_replay_is_labeled_simulation():
    events = client.get("/jaal/replay").json()
    assert "SIMULATION" in events[0]["meta"]["label"]
    assert "extracted_indicators" in events[-1]


def test_report_promotes_at_three_distinct_reporters(isolated_stores):
    for i, reporter in enumerate(["user_a", "user_b", "user_c"]):
        r = client.post("/report", json={
            "identifier": "newscam@upi", "reporter_id": reporter, "reason": "fake prize",
        }).json()
        assert r["promoted"] is (i == 2)
    assert r["level"] == "village"
    # And the promoted VPA now contributes evidence on the next analyze
    r2 = client.post("/analyze", json={"text": "pay to newscam@upi", "online": False}).json()
    assert any("newscam@upi" in h for h in r2["capsule"]["evidence"]["reputation_hits"])


def test_speak_degrades_gracefully_without_key(monkeypatch):
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    r = client.post("/speak", json={"text": "test", "language": "hi"})
    assert r.status_code == 503
