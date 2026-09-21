"""Typed data contracts shared by the research agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Direction = Literal["bullish", "bearish", "neutral"]
Confidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class Evidence:
    agent: str
    claim: str
    direction: Direction
    confidence: Confidence
    metrics: dict[str, float | str] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()

    @property
    def score(self) -> float:
        direction_weight = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}
        confidence_weight = {"high": 1.0, "medium": 0.65, "low": 0.3}
        return direction_weight[self.direction] * confidence_weight[self.confidence]


@dataclass(frozen=True)
class AuditFinding:
    severity: Literal["info", "warning", "critical"]
    message: str
    affected_agents: tuple[str, ...] = ()


@dataclass(frozen=True)
class Scenario:
    name: str
    probability: int
    trigger: str
    invalidation: str


@dataclass(frozen=True)
class CouncilReport:
    symbol: str
    as_of: str
    regime: str
    conviction: Confidence
    summary: str
    evidence: tuple[Evidence, ...]
    audit: tuple[AuditFinding, ...]
    scenarios: tuple[Scenario, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "as_of": self.as_of,
            "regime": self.regime,
            "conviction": self.conviction,
            "summary": self.summary,
            "evidence": [
                {
                    "agent": item.agent,
                    "claim": item.claim,
                    "direction": item.direction,
                    "confidence": item.confidence,
                    "metrics": item.metrics,
                    "limitations": list(item.limitations),
                }
                for item in self.evidence
            ],
            "audit": [
                {
                    "severity": item.severity,
                    "message": item.message,
                    "affected_agents": list(item.affected_agents),
                }
                for item in self.audit
            ],
            "scenarios": [
                {
                    "name": item.name,
                    "probability": item.probability,
                    "trigger": item.trigger,
                    "invalidation": item.invalidation,
                }
                for item in self.scenarios
            ],
        }
