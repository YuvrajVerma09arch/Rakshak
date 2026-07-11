"""Local reputation cache — the client-side half of Community Immunity.

Reads the synced blocklist (data/blocklist.json). In production these arrive as
signed deltas pushed by Nigrani; for the MVP it's a file on disk, which also
means the lookup works fully offline — the whole point of the layer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .capsule import RiskCapsule

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
BLOCKLIST_PATH = DATA_DIR / "blocklist.json"

# Evidence contribution per promotion level (Nigrani's trust pipeline decides the level).
LEVEL_WEIGHT = {"personal": 0.05, "village": 0.10, "district": 0.20, "global": 0.60}


@dataclass
class ReputationResult:
    hits: list[str]                 # e.g. ["vpa:fraudhelp@upi (global, 23 reports)"]
    contribution: float             # evidence score contribution
    confirmed_bad: bool             # any hit at district level or above
    community_reports_24h: int


class ReputationCache:
    def __init__(self, path: Path = BLOCKLIST_PATH):
        self.path = path
        self.data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def lookup(self, capsule: RiskCapsule) -> ReputationResult:
        hits, contribution, confirmed, reports = [], 0.0, False, 0
        checks = [
            ("vpas", "vpa", capsule.actor.vpa),
            ("phones", "phone", capsule.actor.phone),
        ]
        for url_entry, ident in (self.data.get("urls") or {}).items():
            if url_entry.lower() in capsule.raw_text.lower():
                checks.append(("urls", "url", url_entry))

        for section, label, key in checks:
            if not key:
                continue
            entry = (self.data.get(section) or {}).get(key)
            if not entry:
                continue
            level = entry.get("level", "personal")
            count = int(entry.get("report_count", 1))
            hits.append(f"{label}:{key} ({level}, {count} reports)")
            contribution += LEVEL_WEIGHT.get(level, 0.05)
            confirmed = confirmed or level in ("district", "global")
            reports += count

        return ReputationResult(
            hits=hits,
            contribution=min(0.6, contribution) + min(0.15, 0.02 * reports),
            confirmed_bad=confirmed,
            community_reports_24h=reports,
        )


_cache: ReputationCache | None = None


def get_cache() -> ReputationCache:
    global _cache
    if _cache is None:
        _cache = ReputationCache()
    return _cache
