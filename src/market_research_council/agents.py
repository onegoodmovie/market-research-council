"""Independent evidence agents and a deliberately skeptical audit agent."""

from __future__ import annotations

from typing import Any

from .models import AuditFinding, Evidence


def _confidence(quality: float) -> str:
    if quality >= 0.8:
        return "high"
    if quality >= 0.55:
        return "medium"
    return "low"


class PriceAgent:
    name = "price_structure"

    def analyze(self, snapshot: dict[str, Any]) -> Evidence:
        price = snapshot["price"]
        session_range = max(price["high"] - price["low"], 1e-9)
        close_location = (price["close"] - price["low"]) / session_range
        daily_return = price["close"] / price["previous_close"] - 1

        if close_location >= 0.75 and daily_return > 0:
            direction, claim = "bullish", "Price closed near the session high after a positive session."
        elif close_location <= 0.25 and daily_return < 0:
            direction, claim = "bearish", "Price closed near the session low after a negative session."
        else:
            direction, claim = "neutral", "Price finished inside the session range without directional acceptance."

        return Evidence(
            agent=self.name,
            claim=claim,
            direction=direction,
            confidence=_confidence(float(price.get("quality", 1.0))),
            metrics={
                "daily_return_pct": round(daily_return * 100, 2),
                "close_location": round(close_location, 2),
            },
        )


class VolatilityAgent:
    name = "volatility_surface"

    def analyze(self, snapshot: dict[str, Any]) -> Evidence:
        vol = snapshot["volatility"]
        atm_change = float(vol["atm_change"])
        rr_change = float(vol["risk_reversal_change"])
        limitations: list[str] = []

        if vol.get("strike_migration", False):
            limitations.append("Wing comparison includes strike migration; exact magnitude is down-weighted.")

        if atm_change > 0.4 and rr_change < -0.25:
            direction = "bearish"
            claim = "Uncertainty rebuilt while relative downside protection became richer."
        elif atm_change < -0.4 and rr_change > 0.25:
            direction = "bullish"
            claim = "Broad volatility compressed while downside skew normalized."
        else:
            direction = "neutral"
            claim = "The volatility surface changed without a clean directional confirmation."

        quality = float(vol.get("quality", 1.0)) * (0.7 if limitations else 1.0)
        return Evidence(
            agent=self.name,
            claim=claim,
            direction=direction,
            confidence=_confidence(quality),
            metrics={
                "atm_level": float(vol["atm_level"]),
                "atm_change": atm_change,
                "risk_reversal_change": rr_change,
            },
            limitations=tuple(limitations),
        )


class PositioningAgent:
    name = "positioning"

    def analyze(self, snapshot: dict[str, Any]) -> Evidence:
        flow = snapshot["positioning"]
        call_put_ratio = float(flow["eight_plus_dte_call_put_ratio"])
        confirmation = float(flow["t_minus_one_oi_confirmation"])
        limitations: list[str] = []

        if not flow.get("oi_is_lagged", True):
            limitations.append("The open-interest timestamp is not verified as lagged.")

        if call_put_ratio >= 1.35 and confirmation > 0.1:
            direction = "bullish"
            claim = "Longer-dated call activity received positive next-day open-interest confirmation."
        elif call_put_ratio <= 0.75 and confirmation < -0.1:
            direction = "bearish"
            claim = "Put-heavy activity received negative next-day open-interest confirmation."
        else:
            direction = "neutral"
            claim = "Activity was notable, but positioning evidence did not confirm a directional build."

        return Evidence(
            agent=self.name,
            claim=claim,
            direction=direction,
            confidence=_confidence(float(flow.get("quality", 1.0)) * (0.5 if limitations else 1.0)),
            metrics={
                "eight_plus_dte_call_put_ratio": call_put_ratio,
                "t_minus_one_oi_confirmation": confirmation,
                "short_dated_share": float(flow["short_dated_share"]),
            },
            limitations=tuple(limitations),
        )


class MacroAgent:
    name = "macro_regime"

    def analyze(self, snapshot: dict[str, Any]) -> Evidence:
        macro = snapshot["macro"]
        impulse = macro["risk_impulse"]
        direction = {"positive": "bullish", "negative": "bearish", "mixed": "neutral"}[impulse]
        event = macro.get("event", "No named event")
        claim = f"Macro risk impulse was {impulse} around {event}."
        return Evidence(
            agent=self.name,
            claim=claim,
            direction=direction,
            confidence=_confidence(float(macro.get("quality", 1.0))),
            metrics={"event": event, "risk_impulse": impulse},
        )


class AuditAgent:
    name = "evidence_auditor"

    def review(self, snapshot: dict[str, Any], evidence: list[Evidence]) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        positioning = snapshot["positioning"]
        volatility = snapshot["volatility"]

        if not positioning.get("oi_is_lagged", True):
            findings.append(
                AuditFinding(
                    severity="critical",
                    message="Same-day volume cannot be treated as confirmed new positioning without a lagged OI observation.",
                    affected_agents=("positioning",),
                )
            )

        if volatility.get("strike_migration", False):
            findings.append(
                AuditFinding(
                    severity="warning",
                    message="Wing changes are directionally useful, but exact magnitudes are not comparable after strike migration.",
                    affected_agents=("volatility_surface",),
                )
            )

        active_directions = {item.direction for item in evidence if item.direction != "neutral"}
        if len(active_directions) > 1:
            findings.append(
                AuditFinding(
                    severity="info",
                    message="The council contains conflicting directional evidence; synthesis should preserve scenario uncertainty.",
                    affected_agents=tuple(item.agent for item in evidence if item.direction != "neutral"),
                )
            )

        if not findings:
            findings.append(AuditFinding(severity="info", message="No material evidence-timing or quality conflicts detected."))
        return findings
