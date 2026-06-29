from __future__ import annotations

from homeassistant.core import HomeAssistant

from .decision_engine import make_decision


def analyze(hass: HomeAssistant) -> dict:
    return make_decision(hass)
