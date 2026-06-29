from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo

from .const import DEVICE_NAME, DOMAIN, MANUFACTURER


class RoelEnergyAssistantEntity:
    _attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, "roel_energy_assistant")},
            name=DEVICE_NAME,
            manufacturer=MANUFACTURER,
            model="Personal Energy Assistant",
        )
