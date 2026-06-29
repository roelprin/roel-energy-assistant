from __future__ import annotations

from homeassistant.core import HomeAssistant


def make_decision(hass: HomeAssistant) -> dict:
    """Central decision object for REA.

    v0.4.0 introduces this as the single future entry point for decisions.
    It wraps the existing stable analyzer so all current behaviour stays intact.
    Future versions will move all logic here and keep sensors as thin views.
    """
    from .engine import analyze

    data = dict(analyze(hass))
    data["decision_engine_version"] = "0.4.0"
    data["decision_engine_mode"] = "foundation"
    data["primary_status"] = data.get("status")
    data["primary_advice"] = data.get("advice")
    data["primary_score"] = data.get("score")
    return data
