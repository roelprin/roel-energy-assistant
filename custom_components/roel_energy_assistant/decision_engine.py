from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant

from .const import (
    ESSENT_AVERAGE_TODAY,
    ESSENT_CHEAPEST_HOUR,
    ESSENT_CHEAP_HOUR,
    ESSENT_CURRENT_PRICE,
    ESSENT_EXPENSIVE_HOUR,
    ESSENT_HIGHEST_TODAY,
    ESSENT_HOURLY_PRICES,
    ESSENT_LOWEST_TODAY,
    ESSENT_MOST_EXPENSIVE_HOUR,
    ESSENT_NEGATIVE_PRICE,
    ESSENT_NEXT_PRICE,
    GOODWE_EXPORT_LIMIT,
    GOODWE_EXPORT_LIMIT_MIN,
    GOODWE_EXPORT_LIMIT_NORMAL,
    P1_POWER,
)

TZ = ZoneInfo("Europe/Amsterdam")


def _float_state(hass: HomeAssistant, entity_id: str):
    state = hass.states.get(entity_id)
    if state is None:
        return None

    try:
        return float(state.state)
    except (TypeError, ValueError):
        return None


def _state(hass: HomeAssistant, entity_id: str):
    state = hass.states.get(entity_id)
    return state.state if state is not None else None


def _attr(hass: HomeAssistant, entity_id: str, attribute: str):
    state = hass.states.get(entity_id)
    if state is None:
        return None
    return state.attributes.get(attribute)


def _safe_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _stars(score):
    if score is None:
        return "☆☆☆☆☆"
    if score >= 90:
        return "★★★★★"
    if score >= 75:
        return "★★★★☆"
    if score >= 60:
        return "★★★☆☆"
    if score >= 40:
        return "★★☆☆☆"
    return "★☆☆☆☆"


def _rating(score):
    if score is None:
        return "unknown"
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "very_good"
    if score >= 60:
        return "good"
    if score >= 45:
        return "average"
    if score >= 25:
        return "expensive"
    return "very_expensive"


def _cheap_block(summary):
    if not isinstance(summary, dict):
        return None
    return summary.get("cheapest_block_below_average")


def _market_status(current, market_price, average):
    if current is None:
        return {
            "status": "unknown",
            "label": "Geen prijsdata",
            "severity": "unknown",
            "message": "Geen actuele stroomprijs beschikbaar",
        }

    if current < 0:
        return {
            "status": "negative_total_price",
            "label": "Negatieve totaalprijs",
            "severity": "critical",
            "message": "De totale stroomprijs is negatief. Verbruiken is financieel gunstig.",
        }

    if market_price is not None and market_price < 0:
        return {
            "status": "negative_market_price",
            "label": "Negatieve beursprijs",
            "severity": "warning",
            "message": "De kale beursprijs is negatief, maar door belasting en toeslagen betaal je nog positief.",
        }

    if average is not None and current < average:
        return {
            "status": "cheap",
            "label": "Goedkoop",
            "severity": "good",
            "message": "De stroomprijs ligt onder het daggemiddelde.",
        }

    if average is not None and current > average:
        return {
            "status": "expensive",
            "label": "Duur",
            "severity": "expensive",
            "message": "De stroomprijs ligt boven het daggemiddelde.",
        }

    return {
        "status": "normal",
        "label": "Normaal",
        "severity": "normal",
        "message": "Geen bijzonder prijssignaal.",
    }


def _score(current, market_price, average, lowest, highest, next_price, cheap_hour, expensive_hour, feed_in_power, grid_import_power, negative_price):
    if current is None:
        return None, ["Essent prijsdata ontbreekt"]

    score = 50
    reasons = []

    if negative_price or current < 0:
        score = 100
        reasons.append("De totale stroomprijs is negatief")
    elif market_price is not None and market_price < 0:
        score += 15
        reasons.append("De kale beursprijs is negatief")

    if average is not None:
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

    if next_price is not None:
        if next_price > current:
            score += 5
            reasons.append("Volgend uur wordt duurder")
        elif next_price < current:
            score -= 8
            reasons.append("Volgend uur wordt goedkoper")

    if cheap_hour:
        score += 10
        reasons.append("Goedkoop stroomuur is actief")

    if expensive_hour:
        score -= 20
        reasons.append("Duur stroomuur is actief")

    if feed_in_power >= 2500:
        score += 10
        reasons.append("Er is veel teruglevering beschikbaar")
    elif grid_import_power >= 1500:
        score -= 8
        reasons.append("Je neemt relatief veel stroom af van het net")

    return max(0, min(100, score)), reasons


def _status(score):
    if score is None:
        return "Geen prijsdata beschikbaar"
    if score >= 85:
        return "Nu doen"
    if score >= 70:
        return "Goed moment"
    if score >= 45:
        return "Neutraal"
    if score >= 25:
        return "Liever wachten"
    return "Vermijden"


def _virtual_battery(feed_in_power):
    if feed_in_power >= 3500:
        return "Veel overschot", 100
    if feed_in_power >= 2500:
        return "Ruim overschot", 80
    if feed_in_power >= 1000:
        return "Overschot", 60
    if feed_in_power >= 250:
        return "Klein overschot", 35
    return "Geen overschot", 0


def _suggested_loads(feed_in_power):
    if feed_in_power >= 3500:
        return ["droger", "wasmachine", "vaatwasser", "airco"], "Veel zonnestroom over: droger, wasmachine of airco zijn nu logisch"
    if feed_in_power >= 2500:
        return ["wasmachine", "vaatwasser", "airco"], "Ruim zonnestroom over: wasmachine of airco zijn nu logisch"
    if feed_in_power >= 1000:
        return ["vaatwasser", "airco"], "Zonnestroom over: kleine tot middelgrote verbruikers kunnen nu"
    if feed_in_power >= 250:
        return ["airco laag vermogen"], "Klein overschot: lichte verbruikers of airco laag vermogen"
    return [], "Geen extra eigen zonnestroom beschikbaar"


def _daily_plan(score, cheapest_hour, lowest, most_expensive_hour, block):
    plan = []

    if score is not None and score >= 85:
        plan.append({
            "time": "Nu",
            "priority": "high",
            "task": "Energie-intensieve apparaten gebruiken",
            "reason": "REA-score is zeer hoog",
            "recommended": True,
        })
    elif score is not None and score <= 35:
        plan.append({
            "time": "Nu",
            "priority": "high",
            "task": "Groot verbruik uitstellen",
            "reason": "REA-score is laag",
            "recommended": False,
        })

    if block:
        plan.append({
            "time": f"{block.get('start')}–{block.get('end')}",
            "priority": "high",
            "task": "Wasmachine / vaatwasser / droger",
            "reason": f"Goedkoop blok met gemiddeld €{block.get('average')}/kWh",
            "recommended": True,
        })

    if cheapest_hour and lowest is not None:
        plan.append({
            "time": cheapest_hour,
            "priority": "high",
            "task": "Zware verbruikers plannen",
            "reason": f"Goedkoopste uur van vandaag: €{lowest:.3f}/kWh",
            "recommended": True,
        })

    if most_expensive_hour:
        plan.append({
            "time": most_expensive_hour,
            "priority": "avoid",
            "task": "Groot verbruik vermijden",
            "reason": "Duurste uur van vandaag",
            "recommended": False,
        })

    return plan


def make_decision(hass: HomeAssistant) -> dict:
    current = _float_state(hass, ESSENT_CURRENT_PRICE)
    market_price = _safe_float(_attr(hass, ESSENT_CURRENT_PRICE, "market_price"))
    next_price = _float_state(hass, ESSENT_NEXT_PRICE)
    average = _float_state(hass, ESSENT_AVERAGE_TODAY)
    lowest = _float_state(hass, ESSENT_LOWEST_TODAY)
    highest = _float_state(hass, ESSENT_HIGHEST_TODAY)
    cheapest_hour = _state(hass, ESSENT_CHEAPEST_HOUR)
    most_expensive_hour = _state(hass, ESSENT_MOST_EXPENSIVE_HOUR)
    today_summary = _attr(hass, ESSENT_HOURLY_PRICES, "today_summary")
    block = _cheap_block(today_summary)

    p1_power = _float_state(hass, P1_POWER)
    goodwe_export_limit = _float_state(hass, GOODWE_EXPORT_LIMIT)

    feed_in_power = abs(p1_power) if p1_power is not None and p1_power < 0 else 0
    grid_import_power = p1_power if p1_power is not None and p1_power > 0 else 0
    grid_status = "Teruglevering" if feed_in_power > 50 else ("Netafname" if grid_import_power > 50 else "Eigen verbruik")

    cheap_hour = _state(hass, ESSENT_CHEAP_HOUR) == "on"
    expensive_hour = _state(hass, ESSENT_EXPENSIVE_HOUR) == "on"
    negative_price = _state(hass, ESSENT_NEGATIVE_PRICE) == "on"

    market = _market_status(current, market_price, average)
    score, reasons = _score(
        current,
        market_price,
        average,
        lowest,
        highest,
        next_price,
        cheap_hour,
        expensive_hour,
        feed_in_power,
        grid_import_power,
        negative_price,
    )

    potential_saving = round(max(0, current - lowest), 5) if current is not None and lowest is not None else 0
    next_diff = round(next_price - current, 5) if current is not None and next_price is not None else None

    feed_in_kw = round(feed_in_power / 1000, 3) if feed_in_power else 0
    loss_per_hour = round(abs(current) * feed_in_kw, 4) if current is not None and current < 0 and feed_in_kw else 0

    virtual_status, virtual_score = _virtual_battery(feed_in_power)
    suggested_loads, self_consumption_advice = _suggested_loads(feed_in_power)

    anti_feed_in_active = current is not None and current < 0 and feed_in_power > 50
    goodwe_limit_recommended = anti_feed_in_active
    recommended_export_limit = GOODWE_EXPORT_LIMIT_MIN if goodwe_limit_recommended else GOODWE_EXPORT_LIMIT_NORMAL

    goodwe_advice = "Geen GoodWe-begrenzing nodig"
    if goodwe_limit_recommended:
        goodwe_advice = (
            f"Negatieve totaalprijs en {int(feed_in_power)} W teruglevering. "
            f"Advies: GoodWe exportlimiet tijdelijk naar {recommended_export_limit} W."
        )
    elif market_price is not None and market_price < 0 and feed_in_power > 500:
        goodwe_advice = (
            f"Negatieve beursprijs en {int(feed_in_power)} W teruglevering. "
            "Gebruik eerst eigen stroom; GoodWe begrenzen kan later als automatische stap."
        )

    if current is None:
        advice = "Geen prijsdata beschikbaar"
    elif goodwe_limit_recommended:
        advice = (
            f"ANTI FEED-IN: je levert {int(feed_in_power)} W terug bij negatieve totaalprijs. "
            f"Gebruik eigen stroom en begrens GoodWe tijdelijk naar {recommended_export_limit} W."
        )
    elif feed_in_power > 500 and current < 0:
        advice = f"Je levert {int(feed_in_power)} W terug terwijl de totaalprijs negatief is. Gebruik nu zoveel mogelijk eigen stroom."
    elif current < 0:
        advice = "Gebruik nu veel stroom: de totale stroomprijs is negatief."
    elif feed_in_power > 500 and market_price is not None and market_price < 0:
        advice = f"Je levert {int(feed_in_power)} W terug en de kale beursprijs is negatief. Gebruik bij voorkeur nu eigen stroom."
    elif market_price is not None and market_price < 0:
        advice = "De kale beursprijs is negatief. Gebruik bij voorkeur nu eigen stroom en voorkom onnodige teruglevering."
    elif score is not None and score >= 85:
        advice = "Goed moment om energie-intensieve apparaten te gebruiken."
    elif score is not None and score >= 70:
        advice = "Goed moment voor wasmachine, vaatwasser of airco voorkoelen."
    elif potential_saving and potential_saving >= 0.05 and cheapest_hour:
        advice = f"Wacht tot {cheapest_hour}; dat kan ongeveer €{potential_saving:.3f}/kWh schelen."
    elif next_diff is not None and next_diff < -0.03:
        advice = f"Wacht eventueel tot volgend uur; dat is €{abs(next_diff):.3f}/kWh goedkoper."
    elif score is not None and score <= 25:
        advice = "Duur moment: stel groot verbruik uit."
    else:
        advice = "Geen sterk advies; normaal verbruik is prima."

    if goodwe_limit_recommended:
        recommended, avoid = ["airco", "wasmachine", "vaatwasser", "droger", "goodwe begrenzen"], []
    elif current is not None and current < 0:
        recommended, avoid = ["airco", "boiler", "wasmachine", "vaatwasser", "droger"], []
    elif suggested_loads:
        recommended, avoid = suggested_loads, []
    elif score is not None and score >= 85:
        recommended, avoid = ["wasmachine", "vaatwasser", "droger", "airco voorkoelen"], []
    elif score is not None and score >= 70:
        recommended, avoid = ["wasmachine", "vaatwasser", "airco voorkoelen"], []
    elif score is not None and score >= 45:
        recommended, avoid = ["klein verbruik", "vaatwasser indien nodig"], []
    else:
        recommended, avoid = [], ["droger", "boiler", "airco extra koelen", "groot verbruik"]

    status = _status(score)

    if current is None:
        briefing = "Geen prijsdata beschikbaar."
    else:
        briefing = f"{status}. Huidige prijs: €{current:.3f}/kWh. {advice}"
        if feed_in_power > 50:
            briefing += f" Je levert momenteel {int(feed_in_power)} W terug."
        elif grid_import_power > 50:
            briefing += f" Je neemt momenteel {int(grid_import_power)} W af van het net."
        if recommended:
            briefing += " Aanbevolen: " + ", ".join(recommended) + "."

    data_quality = "ok"
    if current is None:
        data_quality = "missing_price"
    elif p1_power is None:
        data_quality = "missing_p1_power"
    elif goodwe_export_limit is None:
        data_quality = "missing_goodwe_export_limit"

    return {
        "status": status,
        "score": score,
        "rating": _rating(score),
        "stars": _stars(score),
        "advice": advice,
        "briefing": briefing,
        "current_price": current,
        "market_price": market_price,
        "market_status": market.get("status"),
        "market_label": market.get("label"),
        "market_severity": market.get("severity"),
        "market_message": market.get("message"),
        "next_price": next_price,
        "average_price": average,
        "lowest_price": lowest,
        "highest_price": highest,
        "cheapest_hour": cheapest_hour,
        "most_expensive_hour": most_expensive_hour,
        "wait_minutes": _minutes_until(cheapest_hour),
        "potential_saving": potential_saving,
        "next_hour_difference": next_diff,
        "p1_power": p1_power,
        "p1_entity": P1_POWER,
        "feed_in_power": feed_in_power,
        "feed_in_kw": feed_in_kw,
        "grid_import_power": grid_import_power,
        "grid_status": grid_status,
        "loss_per_hour": loss_per_hour,
        "solar_advice": self_consumption_advice,
        "available_solar_surplus": feed_in_power if feed_in_power > 50 else 0,
        "virtual_battery_status": virtual_status,
        "virtual_battery_score": virtual_score,
        "self_consumption_advice": self_consumption_advice,
        "suggested_loads": suggested_loads,
        "cheap_block": block,
        "reasons": reasons,
        "recommended_actions": recommended,
        "avoid_actions": avoid,
        "daily_plan": _daily_plan(score, cheapest_hour, lowest, most_expensive_hour, block),
        "data_quality": data_quality,
        "decision_engine_version": "0.4.2",
        "goodwe_export_limit_entity": GOODWE_EXPORT_LIMIT,
        "goodwe_export_limit": goodwe_export_limit,
        "goodwe_export_limit_normal": GOODWE_EXPORT_LIMIT_NORMAL,
        "recommended_export_limit": recommended_export_limit,
        "goodwe_limit_recommended": goodwe_limit_recommended,
        "anti_feed_in_active": anti_feed_in_active,
        "goodwe_advice": goodwe_advice,
    }
