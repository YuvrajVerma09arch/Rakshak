"""Nigrani (निगरानी) — the community-immunity pipeline, MVP slice.

Users report a scam once; Nigrani stores the report and promotes an identifier
up the trust ladder when independent reports corroborate it:

    personal (1 report) → village (3+ reporters) → district / global (human-verified)

Promotion to village level happens automatically here. District/global promotion
stays a human/ops decision by design — auto-blocking the whole network off
unverified reports is the exact failure mode the architecture forbids (poisoning
via fake reports). Reports land in data/reports.jsonl; promotions write back to
data/blocklist.json and hot-reload the reputation cache.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import reputation
from .reputation import DATA_DIR

REPORTS_PATH = DATA_DIR / "reports.jsonl"
VILLAGE_THRESHOLD = 3  # distinct reporters before an identifier is community-visible


def _identifier_key(identifier: str) -> tuple[str, str]:
    """Classify a reported identifier into its blocklist section."""
    if identifier.startswith(("http://", "https://")) or "/" in identifier:
        return "urls", identifier
    if "@" in identifier:
        return "vpas", identifier
    return "phones", identifier


def submit_report(identifier: str, reporter_id: str, reason: str = "") -> dict:
    """Store one community report; promote to village level at the threshold.
    Returns {level, report_count, promoted}."""
    identifier = identifier.strip()
    record = {"identifier": identifier, "reporter": reporter_id, "reason": reason,
              "ts": int(time.time())}
    REPORTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    reporters = {
        json.loads(line)["reporter"]
        for line in REPORTS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line)["identifier"] == identifier
    }

    cache = reputation.get_cache()
    section, key = _identifier_key(identifier)
    entry = (cache.data.get(section) or {}).get(key, {})
    current_level = entry.get("level")
    promoted = False

    if len(reporters) >= VILLAGE_THRESHOLD and current_level in (None, "personal"):
        cache.data.setdefault(section, {})[key] = {
            "level": "village",
            "report_count": len(reporters),
            "first_reported": entry.get("first_reported", record["ts"]),
        }
        cache.path.write_text(json.dumps(cache.data, indent=2, ensure_ascii=False),
                              encoding="utf-8")
        promoted = True
    elif current_level:  # already listed — just bump the count
        cache.data[section][key]["report_count"] = max(
            int(entry.get("report_count", 0)), len(reporters))
        cache.path.write_text(json.dumps(cache.data, indent=2, ensure_ascii=False),
                              encoding="utf-8")

    return {
        "identifier": identifier,
        "level": cache.data.get(section, {}).get(key, {}).get("level", "personal"),
        "report_count": len(reporters),
        "promoted": promoted,
    }
