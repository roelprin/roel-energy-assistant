from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN
from .engine import analyze
from .entity import RoelEnergyAssistantEntity

TRACKED_ENTITIES = [
    "sensor.essent_dynamic_prices_stroomprijs_nu",
    "sensor.essent_dynamic_prices_stroomprijs_volgend_uur",
    "sensor.essent_dynamic_prices_gemiddelde_stroomprijs_vandaag",
    "sensor.essent_dynamic_prices_laagste_stroomprijs_vandaag",
    "sensor.essent_dynamic_prices_hoogste_stroomprijs_vandaag",
    "sensor.essent_dynamic_prices_goedkoopste_uur_vandaag",
    "sensor.essent_dynamic_prices_duurste_uur_vandaag",
    "sensor.essent_dynamic_prices_uurprijzen_2",
    "binary_sensor.essent_dynamic_prices_negatieve_stroomprijs",
    "binary_sensor.essent_dynamic_prices_goedkoop_stroomuur",
    "binary_sensor.essent_dynamic_prices_duur_stroomuur",
]


class RoelAssistantBaseSensor(RoelEnergyAssistantEntity, SensorEntity):
    def __init__(self, hass: HomeAssistant, key: str, name: str, icon: str | None = None, unit: str | None = None):
        self.hass = hass
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"roel_energy_assistant_{key}"
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._unsub = None

    async def async_added_to_hass(self):
        self._unsub = async_track_state_change_event(
            self.hass,
            TRACKED_ENTITIES,
            self._handle_tracked_state_change,
        )

    async def async_will_remove_from_hass(self):
        if self._unsub:
            self._unsub()
            self._unsub = None

    async def _handle_tracked_state_change(self, event):
        self.async_write_ha_state()


class ReaAdvisorSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("advice")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {key: value for key, value in data.items() if key != "advice"}


class ReaScoreSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("score")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {
            "rating": data.get("rating"),
            "status": data.get("status"),
            "reasons": data.get("reasons"),
        }


class ReaStatusSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("status")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {
            "score": data.get("score"),
            "rating": data.get("rating"),
            "advice": data.get("advice"),
        }


class ReaDailyPlanSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        plan = analyze(self.hass).get("daily_plan", [])
        return len(plan)

    @property
    def extra_state_attributes(self):
        return {
            "plan": analyze(self.hass).get("daily_plan", []),
        }


class ReaBriefingSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("briefing")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {
            "status": data.get("status"),
            "score": data.get("score"),
            "stars": data.get("stars"),
            "recommended_actions": data.get("recommended_actions"),
            "avoid_actions": data.get("avoid_actions"),
            "daily_plan": data.get("daily_plan"),
            "reasons": data.get("reasons"),
        }


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        ReaAdvisorSensor(hass, "advisor", "Advisor", "mdi:brain"),
        ReaScoreSensor(hass, "score", "Score", "mdi:trophy", "%"),
        ReaStatusSensor(hass, "status", "Status", "mdi:traffic-light"),
        ReaDailyPlanSensor(hass, "daily_plan", "Dagplanning", "mdi:calendar-clock"),
        ReaBriefingSensor(hass, "briefing", "Briefing", "mdi:message-text-clock"),
    ])
