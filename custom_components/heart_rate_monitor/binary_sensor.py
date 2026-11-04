"""Connection and skin contact entities."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .entity import MonitorEntity


async def async_setup_entry(hass, entry, async_add_entities):
    monitor = entry.runtime_data
    async_add_entities([Connected(monitor, "connected")])
    registry = er.async_get(hass)
    contact = SkinContact(monitor, "contact")
    added = False

    @callback
    def add_contact():
        nonlocal added
        measurement = monitor.measurement
        if not added and (
            (measurement is not None and measurement.contact is not None)
            or registry.async_get_entity_id("binary_sensor", DOMAIN, contact.unique_id)
        ):
            added = True
            async_add_entities([contact])

    entry.async_on_unload(async_dispatcher_connect(hass, monitor.signal, add_contact))
    add_contact()


class Connected(MonitorEntity, BinarySensorEntity):
    _attr_name = "Connected"
    _attr_icon = "mdi:bluetooth"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self):
        return self.monitor.connected


class SkinContact(MonitorEntity, BinarySensorEntity):
    _attr_name = "Skin Contact"

    @property
    def available(self):
        return self.monitor.connected and self.is_on is not None

    @property
    def is_on(self):
        measurement = self.monitor.measurement
        return measurement.contact if measurement is not None else None
