"""Coordinates independent analysis, challenge, and synthesis."""

from __future__ import annotations

from typing import Any

from .agents import AuditAgent, MacroAgent, PositioningAgent, PriceAgent, VolatilityAgent
from .models import CouncilReport, Evidence, Scenario


class ResearchCouncil:
    def __init__(self) -> None:
        self.research_agents = (PriceAgent(), VolatilityAgent(), PositioningAgent(), MacroAgent())
        self.auditor = AuditAgent()

    def run(self, snapshot: dict[str, Any]) -> CouncilReport:
        self._validate(snapshot)
        evidence = [agent.analyze(snapshot) for agent in self.research_agents]
        audit = self.auditor.review(snapshot, evidence)

        critical_agents = {
            agent
            for finding in audit
            if finding.severity == "critical"
            for agent in finding.affected_agents
        }
        usable = [item for item in evidence if item.agent not in critical_agents]
        net_score = sum(item.score for item in usable)

        if net_score >= 1.2:
            regime, base_name = "constructive", "Upside continuation"
        elif net_score <= -1.2:
            regime, base_name = "defensive", "Downside repricing"
        else:
            regime, base_name = "mixed", "Range with conflicting evidence"

        high_count = sum(item.confidence == "high" for item in usable)
        conflict = len({item.direction for item in usable if item.direction != "neutral"}) > 1
        if high_count >= 3 and not conflict:
            conviction = "high"
        elif high_count >= 1 and not any(item.confidence == "low" for item in usable):
            conviction = "medium"
        else:
            conviction = "low"

        base_probability = 60 if conviction == "high" else 55 if conviction == "medium" else 50
        alternate_probability = 100 - base_probability
        price = snapshot["price"]
        midpoint = (price["high"] + price["low"]) / 2

        scenarios = (
            Scenario(
                name=base_name,
                probability=base_probability,
                trigger=f"Price holds above {midpoint:.2f} with supporting evidence quality.",
                invalidation=f"Close below {price['low']:.2f} or a material reversal in confirmed positioning.",
            ),
            Scenario(
                name="Evidence reversal",
                probability=alternate_probability,
                trigger=f"Price loses {midpoint:.2f} while volatility or positioning turns defensive.",
                invalidation=f"Close above {price['high']:.2f} with broad confirmation.",
            ),
        )

        directional = [item for item in usable if item.direction != "neutral"]
        if directional:
            strongest = max(directional, key=lambda item: abs(item.score))
            summary = f"{strongest.claim} Council regime: {regime}; conviction: {conviction}."
        else:
            summary = f"No agent produced confirmed directional evidence. Council regime: {regime}."

        return CouncilReport(
            symbol=snapshot["symbol"],
            as_of=snapshot["as_of"],
            regime=regime,
            conviction=conviction,
            summary=summary,
            evidence=tuple(evidence),
            audit=tuple(audit),
            scenarios=scenarios,
        )

    @staticmethod
    def _validate(snapshot: dict[str, Any]) -> None:
        required = {"symbol", "as_of", "price", "volatility", "positioning", "macro"}
        missing = required - snapshot.keys()
        if missing:
            raise ValueError(f"Missing snapshot sections: {', '.join(sorted(missing))}")
