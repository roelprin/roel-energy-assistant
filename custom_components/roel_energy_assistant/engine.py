from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant

from .const import (
    ESSENT_AVERAGE_TODAY,
    ESSENT_CHEAP_HOUR,
    ESSENT_CHEAPEST_HOUR,
    ESSENT_CURRENT_PRICE,
    ESSENT_EXPENSIVE_HOUR,
    ESSENT_HIGHEST_TODAY,
    ESSENT_HOURLY_PRICES,
    ESSENT_LOWEST_TODAY,
    ESSENT_MOST_EXPENSIVE_HOUR,
    ESSENT_NEGATIVE_PRICE,
    ESSENT_NEXT_PRICE,
)

TZ = ZoneInfo("Europe/Amsterdam")


def _float_state(hass: HomeAssistant, entity_id: str):
    value = hass.states.get(entity_id)
    if value is None:
        return None
    try:
        return float(value.state)
    except (TypeError, ValueError):
        return None


def _state(hass: HomeAssistant, entity_id: str):
    value = hass.states.get(entity_id)
    return value.state if value is not None else None


def _attr(hass: HomeAssistant, entity_id: str, attribute: str):
    value = hass.states.get(entity_id)
    if value is None:
        return None
    return value.attributes.get(attribute)


def _minutes_until(hour_label: str | None):
    if not hour_label or ":" not in hour_label:
        return None
    try:
        hour, minute = [int(part) for part in hour_label.split(":")]
    except ValueError:
        return None

    now = datetime.now(TZ)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target < now:
        return 0
    return int((target - now).total_seconds() // 60)


def _cheap_block(summary: dict | None):
    if not isinstance(summary, dict):
        return None
    return summary.get("cheapest_block_below_average")


def analyze(hass: HomeAssistant) -> dict:
    current = _float_state(hass, ESSENT_CURRENT_PRICE)
    next_price = _float_state(hass, ESSENT_NEXT_PRICE)
    average = _float_state(hass, ESSENT_AVERAGE_TODAY)
    lowest = _float_state(hass, ESSENT_LOWEST_TODAY)
    highest = _float_state(hass, ESSENT_HIGHEST_TODAY)
    cheapest_hour = _state(hass, ESSENT_CHEAPEST_HOUR)
    expensive_hour = _state(hass, ESSENT_MOST_EXPENSIVE_HOUR)

    today_summary = _attr(hass, ESSENT_HOURLY_PRICES, "today_summary")
    block = _cheap_block(today_summary)

    negative_price = _state(hass, ESSENT_NEGATIVE_PRICE) == "on"
    cheap_hour = _state(hass, ESSENT_CHEAP_HOUR) == "on"
    expensive_hour_active = _state(hass, ESSENT_EXPENSIVE_HOUR) == "on"

    score = 50
    reasons = []

    if current is None:
        return {
            "status": "Geen prijsdata beschikbaar",
            "score": None,
            "rating": "unknown",
            "advice": "Geen prijsdata beschikbaar",
            "daily_plan": [],
            "reasons": ["Essent prijsdata ontbreekt"],
            "recommended_actions": [],
            "avoid_actions": [],
        }

    if negative_price:
        score = 100
        reasons.append("De stroomprijs is negatief")
    elif average is not None:
        if current < average:
            score += 20
            reasons.append("De huidige prijs ligt onder het daggemiddelde")
        else:
            score -= 15
            reasons.append("De huidige prijs ligt boven het daggemiddelde")

    if lowest is not None and highest is not None and highest != lowest:
        position = (current - lowest) / (highest - lowest)
        score += int((1 - position) * 30) - 15
        if position <= 0.2:
            reasons.append("Dit uur behoort tot de goedkoopste uren van vandaag")
        elif position >= 0.8:
            reasons.append("Dit uur behoort tot de duurste uren van vandaag")

    next_diff = None
    if next_price is not None:
        next_diff = round(next_price - current, 5)
        if next_price > current:
            score += 5
            reasons.append("Volgend uur wordt duurder")
        elif next_price < current:
            score -= 8
            reasons.append("Volgend uur wordt goedkoper")

    if cheap_hour:
        score += 10
        reasons.append("Goedkoop stroomuur is actief")

    if expensive_hour_active:
        score -= 20
        reasons.append("Duur stroomuur is actief")

    score = max(0, min(100, score))

    if score >= 85:
        rating = "excellent"
        status = "Nu doen"
    elif score >= 70:
        rating = "good"
        status = "Goed moment"
    elif score >= 45:
        rating = "average"
        status = "Neutraal"
    elif score >= 25:
        rating = "expensive"
        status = "Liever wachten"
    else:
        rating = "very_expensive"
        status = "Vermijden"

    wait_minutes = _minutes_until(cheapest_hour)
    potential_saving = round(max(0, current - lowest), 5) if lowest is not None else None

    recommended = []
    avoid = []

    if score >= 85:
        recommended = ["wasmachine", "vaatwasser", "droger", "airco voorkoelen"]
    elif score >= 70:
        recommended = ["wasmachine", "vaatwasser", "airco voorkoelen"]
    elif score >= 45:
        recommended = ["klein verbruik", "vaatwasser indien nodig"]
    else:
        avoid = ["droger", "boiler", "airco extra koelen", "groot verbruik"]

    daily_plan = []
    if cheapest_hour and lowest is not None:
        daily_plan.append({
            "time": cheapest_hour,
            "task": "Energie-intensieve taken",
            "reason": f"Goedkoopste uur van vandaag: €{lowest:.3f}/kWh",
        })

    if block:
        daily_plan.append({
            "time": f"{block.get('start')}–{block.get('end')}",
            "task": "Wasmachine / vaatwasser / droger",
            "reason": f"Goedkoop blok met gemiddeld €{block.get('average')}/kWh",
        })

    if expensive_hour:
        daily_plan.append({
            "time": expensive_hour,
            "task": "Groot verbruik vermijden",
            "reason": "Duurste uur van vandaag",
        })

    if negative_price:
        advice = "Gebruik nu veel stroom: de stroomprijs is negatief."
    elif score >= 85:
        advice = "Goed moment om energie-intensieve apparaten te gebruiken."
    elif score >= 70:
        advice = "Goed moment voor wasmachine, vaatwasser of airco voorkoelen."
    elif potential_saving and potential_saving >= 0.05 and cheapest_hour:
        advice = f"Wacht tot {cheapest_hour}; dat kan ongeveer €{potential_saving:.3f}/kWh schelen."
    elif next_diff is not None and next_diff < -0.03:
        advice = f"Wacht eventueel tot volgend uur; dat is €{abs(next_diff):.3f}/kWh goedkoper."
    elif score <= 25:
        advice = "Duur moment: stel groot verbruik uit."
    else:
        advice = "Geen sterk advies; normaal verbruik is prima."

    return {
        "status": status,
        "score": score,
        "rating": rating,
        "advice": advice,
        "current_price": current,
        "next_price": next_price,
        "average_price": average,
        "lowest_price": lowest,
        "highest_price": highest,
        "cheapest_hour": cheapest_hour,
        "most_expensive_hour": expensive_hour,
        "wait_minutes": wait_minutes,
        "potential_saving": potential_saving,
        "next_hour_difference": next_diff,
        "cheap_block": block,
        "reasons": reasons,
        "recommended_actions": recommended,
        "avoid_actions": avoid,
        "daily_plan": daily_plan,
    }
