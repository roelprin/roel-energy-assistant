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
    "sensor.p1_meter_vermogen",
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




class ReaMarketStatusSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("market_label")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {
            "status": data.get("market_status"),
            "severity": data.get("market_severity"),
            "message": data.get("market_message"),
            "current_price": data.get("current_price"),
            "market_price": data.get("market_price"),
            "average_price": data.get("average_price"),
            "advice": data.get("advice"),
        }



class ReaFeedInPowerSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("feed_in_power")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {"p1_power": data.get("p1_power"), "grid_status": data.get("grid_status"), "solar_advice": data.get("solar_advice")}


class ReaGridStatusSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("grid_status")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {"p1_power": data.get("p1_power"), "feed_in_power": data.get("feed_in_power"), "grid_import_power": data.get("grid_import_power"), "solar_advice": data.get("solar_advice")}


class ReaLossPerHourSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("loss_per_hour")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {"feed_in_power": data.get("feed_in_power"), "feed_in_kw": data.get("feed_in_kw"), "current_price": data.get("current_price"), "market_price": data.get("market_price"), "grid_status": data.get("grid_status")}


class ReaSolarAdvisorSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("solar_advice")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {"feed_in_power": data.get("feed_in_power"), "grid_import_power": data.get("grid_import_power"), "loss_per_hour": data.get("loss_per_hour"), "market_status": data.get("market_status"), "advice": data.get("advice")}




class ReaSolarSurplusSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("available_solar_surplus")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {
            "grid_status": data.get("grid_status"),
            "feed_in_power": data.get("feed_in_power"),
            "self_consumption_advice": data.get("self_consumption_advice"),
            "suggested_loads": data.get("suggested_loads"),
        }


class ReaVirtualBatterySensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("virtual_battery_score")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {
            "status": data.get("virtual_battery_status"),
            "available_solar_surplus": data.get("available_solar_surplus"),
            "suggested_loads": data.get("suggested_loads"),
            "self_consumption_advice": data.get("self_consumption_advice"),
        }


class ReaSelfConsumptionAdviceSensor(RoelAssistantBaseSensor):
    @property
    def native_value(self):
        return analyze(self.hass).get("self_consumption_advice")

    @property
    def extra_state_attributes(self):
        data = analyze(self.hass)
        return {
            "available_solar_surplus": data.get("available_solar_surplus"),
            "virtual_battery_status": data.get("virtual_battery_status"),
            "virtual_battery_score": data.get("virtual_battery_score"),
            "suggested_loads": data.get("suggested_loads"),
            "solar_advice": data.get("solar_advice"),
        }


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        ReaAdvisorSensor(hass, "advisor", "Advisor", "mdi:brain"),
        ReaScoreSensor(hass, "score", "Score", "mdi:trophy", "%"),
        ReaStatusSensor(hass, "status", "Status", "mdi:traffic-light"),
        ReaDailyPlanSensor(hass, "daily_plan", "Dagplanning", "mdi:calendar-clock"),
        ReaBriefingSensor(hass, "briefing", "Briefing", "mdi:message-text-clock"),
        ReaMarketStatusSensor(hass, "market_status", "Marktstatus", "mdi:chart-bell-curve"),
        ReaFeedInPowerSensor(hass, "feed_in_power", "Teruglevering", "mdi:transmission-tower-export", "W"),
        ReaGridStatusSensor(hass, "grid_status", "Netstatus", "mdi:transmission-tower"),
        ReaLossPerHourSensor(hass, "loss_per_hour", "Verlies per uur", "mdi:cash-minus", "€/u"),
        ReaSolarAdvisorSensor(hass, "solar_advisor", "Solar advisor", "mdi:solar-power-variant"),
        ReaSolarSurplusSensor(hass, "solar_surplus", "Zonnestroom overschot", "mdi:solar-power", "W"),
        ReaVirtualBatterySensor(hass, "virtual_battery", "Virtuele batterij", "mdi:battery-charging-high", "%"),
        ReaSelfConsumptionAdviceSensor(hass, "self_consumption_advice", "Eigen verbruik advies", "mdi:home-lightning-bolt"),
    ])
