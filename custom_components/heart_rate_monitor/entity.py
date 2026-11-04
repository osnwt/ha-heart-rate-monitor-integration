"""Shared device identity and update subscription."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN


class MonitorEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, monitor, key):
        self.monitor = monitor
        self._attr_unique_id = f"{monitor.address}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, monitor.address)}, name=monitor.name
        )

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, self.monitor.signal, self.async_write_ha_state
            )
        )
