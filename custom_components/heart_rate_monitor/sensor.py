"""Measurement entities created when their fields are first observed."""

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .entity import MonitorEntity

DESCRIPTIONS = (
    SensorEntityDescription(
        key="heart_rate",
        name="Heart Rate",
        native_unit_of_measurement="bpm",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(key="rr_intervals", name="RR Interval", native_unit_of_measurement="ms"),
    SensorEntityDescription(key="energy", name="Energy Expended", native_unit_of_measurement="kJ"),
)


async def async_setup_entry(hass, entry, async_add_entities):
    monitor = entry.runtime_data
    registry = er.async_get(hass)
    heart_rate, rr_interval, energy = DESCRIPTIONS
    async_add_entities([
        SessionLastSensor(monitor, SensorEntityDescription(
            key="session_last",
            name="Session Last Heart Rate",
            native_unit_of_measurement="bpm",
            icon="mdi:heart-pulse",
        )),
        SessionStartSensor(monitor, SensorEntityDescription(
            key="session_start", name="Session Start", device_class=SensorDeviceClass.TIMESTAMP
        )),
        SessionValueSensor(monitor, SensorEntityDescription(
            key="session_end", name="Session End", device_class=SensorDeviceClass.TIMESTAMP
        )),
        SessionDurationSensor(monitor, SensorEntityDescription(
            key="session_duration",
            name="Session Duration",
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS,
        )),
    ])
    pending = [
        HeartRateSensor(monitor, heart_rate),
        RRIntervalSensor(monitor, rr_interval),
        MeasurementSensor(monitor, energy),
        SessionExtremumSensor(monitor, SensorEntityDescription(
            key="session_min",
            name="Session Min Heart Rate",
            native_unit_of_measurement="bpm",
            icon="mdi:arrow-collapse-down",
        )),
        SessionExtremumSensor(monitor, SensorEntityDescription(
            key="session_max",
            name="Session Max Heart Rate",
            native_unit_of_measurement="bpm",
            icon="mdi:arrow-collapse-up",
        )),
    ]

    @callback
    def add_measurements():
        ready = [
            entity for entity in pending
            if entity.native_value is not None
            or registry.async_get_entity_id("sensor", DOMAIN, entity.unique_id)
        ]
        if ready:
            for entity in ready:
                pending.remove(entity)
            async_add_entities(ready)

    entry.async_on_unload(async_dispatcher_connect(hass, monitor.signal, add_measurements))
    add_measurements()


class MeasurementSensor(MonitorEntity, SensorEntity):
    def __init__(self, monitor, description):
        super().__init__(monitor, description.key)
        self.entity_description = description

    @property
    def available(self):
        return self.monitor.connected and self.native_value is not None

    @property
    def native_value(self):
        measurement = self.monitor.measurement
        return getattr(measurement, self.entity_description.key) if measurement is not None else None


class HeartRateSensor(MeasurementSensor, RestoreSensor):
    @property
    def extra_state_attributes(self):
        return {
            "connected": self.monitor.connected,
            "session_min": self.monitor.session_min,
            "session_max": self.monitor.session_max,
        }

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_data = await self.async_get_last_sensor_data()
        last_state = await self.async_get_last_state()
        if self.native_value is not None or last_data is None or last_state is None:
            return
        rate = last_data.native_value
        if not isinstance(rate, int):
            return
        if self.monitor.session_min is None:
            self.monitor.session_min = last_state.attributes.get("session_min", rate)
        if self.monitor.session_max is None:
            self.monitor.session_max = last_state.attributes.get("session_max", rate)
        async_dispatcher_send(self.hass, self.monitor.signal)


class SessionValueSensor(MeasurementSensor):
    @property
    def available(self):
        return self.native_value is not None

    @property
    def native_value(self):
        return getattr(self.monitor, self.entity_description.key)


class SessionExtremumSensor(SessionValueSensor, RestoreSensor):
    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_data = await self.async_get_last_sensor_data()
        if self.native_value is None and last_data is not None:
            setattr(self.monitor, self.entity_description.key, last_data.native_value)


class SessionLastSensor(SessionValueSensor, RestoreSensor):
    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_data = await self.async_get_last_sensor_data()
        if not self.monitor.connected and self.native_value is None and last_data is not None:
            self.monitor.session_last = last_data.native_value


class SessionDurationSensor(SessionValueSensor):
    @property
    def native_value(self):
        start = self.monitor.session_start
        end = self.monitor.session_end
        if start is None or end is None:
            return None
        return (end - start).total_seconds()


class SessionStartSensor(SessionValueSensor, RestoreEntity):
    @property
    def extra_state_attributes(self):
        end = self.monitor.session_end
        return {"session_end": end.isoformat()} if end is not None else None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if self.native_value is not None or last_state is None:
            return
        start = dt_util.parse_datetime(last_state.state)
        if start is None:
            return
        end = last_state.attributes.get("session_end")
        self.monitor.session_start = start
        self.monitor.session_end = dt_util.parse_datetime(end) if end else None
        async_dispatcher_send(self.hass, self.monitor.signal)


class RRIntervalSensor(MeasurementSensor):
    @property
    def native_value(self):
        intervals = super().native_value
        return intervals[-1] if intervals else None

    @property
    def extra_state_attributes(self):
        intervals = self.monitor.measurement
        if intervals is None or not intervals.rr_intervals:
            return None
        return {"intervals_ms": list(intervals.rr_intervals)}
