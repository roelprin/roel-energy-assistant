from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

from .engine import analyze
from .entity import RoelEnergyAssistantEntity

TRACKED_ENTITIES = [
    "sensor.essent_dynamic_prices_stroomprijs_nu",
    "sensor.essent_dynamic_prices_gemiddelde_stroomprijs_vandaag",
    "binary_sensor.essent_dynamic_prices_negatieve_stroomprijs",
    "binary_sensor.essent_dynamic_prices_goedkoop_stroomuur",
    "binary_sensor.essent_dynamic_prices_duur_stroomuur",
    "sensor.p1_meter_vermogen",
]


class ReaBinarySensor(RoelEnergyAssistantEntity, BinarySensorEntity):
    def __init__(self, hass: HomeAssistant, key: str, name: str, icon: str | None = None):
        self.hass = hass
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"roel_energy_assistant_{key}"
        self._attr_icon = icon
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

    @property
    def is_on(self):
        data = analyze(self.hass)

        if self._key == "good_moment":
            return (data.get("score") or 0) >= 70

        if self._key == "avoid_large_usage":
            return (data.get("score") or 0) <= 35

        if self._key == "cheap_block_active":
            block = data.get("cheap_block")
            return data.get("status") in ["Nu doen", "Goed moment"] and block is not None

        if self._key == "negative_market_price":
            return data.get("market_status") == "negative_market_price"

        if self._key == "negative_total_price":
            return data.get("market_status") == "negative_total_price"

        if self._key == "feed_in_active":
            return (data.get("feed_in_power") or 0) > 50

        if self._key == "large_solar_surplus":
            return (data.get("available_solar_surplus") or 0) >= 2500

        return False


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([
        ReaBinarySensor(hass, "good_moment", "Goed moment", "mdi:thumb-up"),
        ReaBinarySensor(hass, "avoid_large_usage", "Groot verbruik vermijden", "mdi:alert-circle"),
        ReaBinarySensor(hass, "cheap_block_active", "Goedkoop blok actief", "mdi:clock-check"),
        ReaBinarySensor(hass, "negative_market_price", "Negatieve beursprijs", "mdi:chart-line-variant"),
        ReaBinarySensor(hass, "negative_total_price", "Negatieve totaalprijs", "mdi:cash-minus"),
        ReaBinarySensor(hass, "feed_in_active", "Teruglevering actief", "mdi:transmission-tower-export"),
        ReaBinarySensor(hass, "large_solar_surplus", "Veel zonnestroom over", "mdi:solar-power-variant"),
    ])
