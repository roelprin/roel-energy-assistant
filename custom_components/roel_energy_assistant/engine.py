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
    P1_POWER,
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


def _rating(score: int | None) -> str:
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


def _stars(score: int | None) -> str:
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


def _market_status(current: float | None, market_price: float | None, average: float | None) -> dict:
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


def _build_daily_plan(
    score: int,
    lowest: float | None,
    cheapest_hour: str | None,
    expensive_hour: str | None,
    cheap_block: dict | None,
):
    plan = []

    if cheap_block:
        start = cheap_block.get("start")
        end = cheap_block.get("end")
        avg = cheap_block.get("average")

        plan.append({
            "time": f"{start}–{end}",
            "priority": "high",
            "task": "Wasmachine / vaatwasser / droger",
            "reason": f"Goedkoop blok met gemiddeld €{avg}/kWh",
            "recommended": True,
        })

        plan.append({
            "time": start,
            "priority": "medium",
            "task": "Airco voorkoelen",
            "reason": "Start aan het begin van het goedkope blok",
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

    if score >= 85:
        plan.insert(0, {
            "time": "Nu",
            "priority": "high",
            "task": "Energie-intensieve apparaten gebruiken",
            "reason": "REA-score is zeer hoog",
            "recommended": True,
        })
    elif score <= 35:
        plan.insert(0, {
            "time": "Nu",
            "priority": "high",
            "task": "Groot verbruik uitstellen",
            "reason": "REA-score is laag",
            "recommended": False,
        })

    if expensive_hour:
        plan.append({
            "time": expensive_hour,
            "priority": "avoid",
            "task": "Groot verbruik vermijden",
            "reason": "Duurste uur van vandaag",
            "recommended": False,
        })

    return plan


def analyze(hass: HomeAssistant) -> dict:
    current = _float_state(hass, ESSENT_CURRENT_PRICE)
    market_price = _attr(hass, ESSENT_CURRENT_PRICE, "market_price")
    p1_power = _float_state(hass, P1_POWER)
    feed_in_power = abs(p1_power) if p1_power is not None and p1_power < 0 else 0
    grid_import_power = p1_power if p1_power is not None and p1_power > 0 else 0
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

    market = _market_status(current, market_price, average)
    score = 50
    reasons = []

    if current is None:
        return {
            "status": "Geen prijsdata beschikbaar",
            "score": None,
            "rating": "unknown",
            "stars": "☆☆☆☆☆",
            "advice": "Geen prijsdata beschikbaar",
            "briefing": "Geen Essent-prijsdata beschikbaar.",
            "daily_plan": [],
            "market_status": "unknown",
            "market_label": "Geen prijsdata",
            "market_severity": "unknown",
            "market_message": "Geen actuele stroomprijs beschikbaar",
            "reasons": ["Essent prijsdata ontbreekt"],
            "recommended_actions": [],
            "avoid_actions": [],
        }

    if negative_price or current < 0:
        score = 100
        reasons.append("De totale stroomprijs is negatief")
    elif market_price is not None and market_price < 0:
        score += 15
        reasons.append("De kale beursprijs is negatief")
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
    rating = _rating(score)

    if score >= 85:
        status = "Nu doen"
    elif score >= 70:
        status = "Goed moment"
    elif score >= 45:
        status = "Neutraal"
    elif score >= 25:
        status = "Liever wachten"
    else:
        status = "Vermijden"

    wait_minutes = _minutes_until(cheapest_hour)
    potential_saving = round(max(0, current - lowest), 5) if lowest is not None else None

    feed_in_kw = round(feed_in_power / 1000, 3) if feed_in_power is not None else 0
    loss_per_hour = 0
    if current is not None and current < 0 and feed_in_kw:
        loss_per_hour = round(abs(current) * feed_in_kw, 4)

    if feed_in_power > 50:
        grid_status = "Teruglevering"
    elif grid_import_power > 50:
        grid_status = "Netafname"
    else:
        grid_status = "Eigen verbruik"

    solar_advice = "Geen bijzonder zonne-advies"
    if feed_in_power > 500 and current < 0:
        solar_advice = "Voorkom teruglevering: de totale stroomprijs is negatief"
    elif feed_in_power > 500 and market_price is not None and market_price < 0:
        solar_advice = "Gebruik nu eigen zonnestroom: de kale beursprijs is negatief"
    elif feed_in_power > 500:
        solar_advice = "Je levert terug; goed moment om eigen zonnestroom te gebruiken"
    elif grid_import_power > 500 and average is not None and current < average:
        solar_advice = "Je neemt stroom af, maar de prijs is gunstig"

    # Solar Utilization Engine v0.3.2
    available_solar_surplus = feed_in_power if feed_in_power > 50 else 0

    if available_solar_surplus >= 3500:
        virtual_battery_status = "Veel overschot"
        virtual_battery_score = 100
    elif available_solar_surplus >= 2500:
        virtual_battery_status = "Ruim overschot"
        virtual_battery_score = 80
    elif available_solar_surplus >= 1000:
        virtual_battery_status = "Overschot"
        virtual_battery_score = 60
    elif available_solar_surplus >= 250:
        virtual_battery_status = "Klein overschot"
        virtual_battery_score = 35
    else:
        virtual_battery_status = "Geen overschot"
        virtual_battery_score = 0

    self_consumption_advice = "Geen extra eigen zonnestroom beschikbaar"
    suggested_loads = []

    if available_solar_surplus >= 3500:
        self_consumption_advice = "Veel zonnestroom over: droger, wasmachine of airco zijn nu logisch"
        suggested_loads = ["droger", "wasmachine", "vaatwasser", "airco"]
    elif available_solar_surplus >= 2500:
        self_consumption_advice = "Ruim zonnestroom over: wasmachine of airco zijn nu logisch"
        suggested_loads = ["wasmachine", "vaatwasser", "airco"]
    elif available_solar_surplus >= 1000:
        self_consumption_advice = "Zonnestroom over: kleine tot middelgrote verbruikers kunnen nu"
        suggested_loads = ["vaatwasser", "airco"]
    elif available_solar_surplus >= 250:
        self_consumption_advice = "Klein overschot: lichte verbruikers of airco laag vermogen"
        suggested_loads = ["airco laag vermogen"]

    recommended = []
    avoid = []

    if current < 0:
        recommended = ["airco", "boiler", "wasmachine", "vaatwasser", "droger"]
    elif market_price is not None and market_price < 0:
        recommended = ["airco voorkoelen", "wasmachine", "vaatwasser"]
    elif score >= 85:
        recommended = ["wasmachine", "vaatwasser", "droger", "airco voorkoelen"]
    elif score >= 70:
        recommended = ["wasmachine", "vaatwasser", "airco voorkoelen"]
    elif score >= 45:
        recommended = ["klein verbruik", "vaatwasser indien nodig"]
    else:
        avoid = ["droger", "boiler", "airco extra koelen", "groot verbruik"]

    if feed_in_power > 500 and current < 0:
        advice = f"Je levert {int(feed_in_power)} W terug terwijl de totaalprijs negatief is. Gebruik nu zoveel mogelijk eigen stroom."
    elif current < 0:
        advice = "Gebruik nu veel stroom: de totale stroomprijs is negatief."
    elif feed_in_power > 500 and market_price is not None and market_price < 0:
        advice = f"Je levert {int(feed_in_power)} W terug en de kale beursprijs is negatief. Gebruik bij voorkeur nu eigen stroom."
    elif market_price is not None and market_price < 0:
        advice = "De kale beursprijs is negatief. Gebruik bij voorkeur nu eigen stroom en voorkom onnodige teruglevering."
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

    daily_plan = _build_daily_plan(score, lowest, cheapest_hour, expensive_hour, block)

    if market.get("status") == "negative_total_price":
        briefing_intro = "Let op: de totale stroomprijs is negatief."
    elif market.get("status") == "negative_market_price":
        briefing_intro = "Let op: de kale beursprijs is negatief."
    elif score >= 70:
        briefing_intro = "Vandaag is een goed moment om energie slim te gebruiken."
    elif score <= 35:
        briefing_intro = "De stroom is nu relatief duur. Stel groot verbruik liever uit."
    else:
        briefing_intro = "Vandaag is er geen extreem prijsvoordeel op dit moment."

    if average is not None:
        briefing = f"{briefing_intro} Huidige prijs: €{current:.3f}/kWh. Gemiddelde vandaag: €{average:.3f}/kWh. "
    else:
        briefing = f"{briefing_intro} Huidige prijs: €{current:.3f}/kWh. "

    if market_price is not None:
        briefing += f"Kale beursprijs: €{market_price:.3f}/kWh. "

    if feed_in_power > 50:
        briefing += f"Je levert momenteel {int(feed_in_power)} W terug. "
        briefing += f"{self_consumption_advice}. "
    elif grid_import_power > 50:
        briefing += f"Je neemt momenteel {int(grid_import_power)} W af van het net. "

    if cheapest_hour and lowest is not None:
        briefing += f"Goedkoopste uur: {cheapest_hour} (€{lowest:.3f}/kWh). "

    if expensive_hour:
        briefing += f"Vermijd groot verbruik rond {expensive_hour}. "

    if recommended:
        briefing += "Aanbevolen: " + ", ".join(recommended) + "."

    return {
        "status": status,
        "score": score,
        "rating": rating,
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
        "p1_power": p1_power,
        "feed_in_power": feed_in_power,
        "feed_in_kw": feed_in_kw,
        "grid_import_power": grid_import_power,
        "grid_status": grid_status,
        "loss_per_hour": loss_per_hour,
        "solar_advice": solar_advice,
        "available_solar_surplus": available_solar_surplus,
        "virtual_battery_status": virtual_battery_status,
        "virtual_battery_score": virtual_battery_score,
        "self_consumption_advice": self_consumption_advice,
        "suggested_loads": suggested_loads,
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
