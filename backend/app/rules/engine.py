"""Drishti's ScamDSL rule engine.

Rules live in YAML packs (rules/packs/*.yaml) so new patterns ship as data, not
code — the same mechanism Nigrani's district pre-arming (Scam Nowcast) uses to
push pack updates. Every rule is tagged with its kill-chain stage and carries
its own multilingual explanation, which is what makes offline voice warnings
possible with zero API calls.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PACKS_DIR = Path(__file__).resolve().parent / "packs"


@dataclass
class Rule:
    id: str
    stage: str
    weight: float
    patterns: list[re.Pattern] = field(default_factory=list)
    reasons: dict[str, str] = field(default_factory=dict)  # lang -> human explanation

    def reason(self, lang: str) -> str:
        return self.reasons.get(lang) or self.reasons.get("hi") or self.reasons.get("en", self.id)


@dataclass
class RuleHit:
    rule: Rule

    @property
    def id(self) -> str:
        return self.rule.id


class RuleEngine:
    def __init__(self, packs_dir: Path = PACKS_DIR):
        self.rules: list[Rule] = []
        for pack_file in sorted(packs_dir.glob("*.yaml")):
            self._load_pack(pack_file)

    def _load_pack(self, path: Path) -> None:
        pack = yaml.safe_load(path.read_text(encoding="utf-8"))
        for raw in pack.get("rules", []):
            self.rules.append(
                Rule(
                    id=raw["id"],
                    stage=raw.get("stage", "unknown"),
                    weight=float(raw.get("weight", 0.2)),
                    patterns=[re.compile(p, re.I | re.U) for p in raw.get("patterns", [])],
                    reasons={k.removeprefix("reason_"): v for k, v in raw.items() if k.startswith("reason_")},
                )
            )

    def match(self, text: str) -> list[RuleHit]:
        return [RuleHit(rule) for rule in self.rules if any(p.search(text) for p in rule.patterns)]

    @staticmethod
    def evidence_contribution(hits: list[RuleHit], cap: float = 0.70) -> float:
        """Summed rule weights, capped — rules alone can never hard-block; reputation
        and structural signals must corroborate. That asymmetry is a stated safety property."""
        return min(cap, sum(h.rule.weight for h in hits))


_engine: RuleEngine | None = None


def get_engine() -> RuleEngine:
    global _engine
    if _engine is None:
        _engine = RuleEngine()
    return _engine
