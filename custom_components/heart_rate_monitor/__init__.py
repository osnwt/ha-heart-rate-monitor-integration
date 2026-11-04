"""Heart Rate Monitor integration."""


async def async_setup_entry(hass, entry):
    from .ble import Monitor

    monitor = Monitor(hass, entry)
    entry.runtime_data = monitor
    await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor", "sensor"])
    entry.async_on_unload(monitor.start())
    return True


async def async_unload_entry(hass, entry):
    if not await hass.config_entries.async_unload_platforms(entry, ["binary_sensor", "sensor"]):
        return False
    await entry.runtime_data.stop()
    return True


async def async_remove_entry(hass, entry):
    from homeassistant.components.bluetooth import async_rediscover_address
    from homeassistant.const import CONF_ADDRESS

    async_rediscover_address(hass, entry.data[CONF_ADDRESS])
