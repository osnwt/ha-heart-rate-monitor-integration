"""Manage a single monitor's GATT subscription."""

import asyncio
import logging
from contextlib import suppress

from bleak import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import MEASUREMENT_UUID, SIGNAL_UPDATED
from .protocol import parse_measurement

_LOGGER = logging.getLogger(__name__)


class Monitor:
    def __init__(self, hass, entry):
        self.hass = hass
        self.address = entry.data[CONF_ADDRESS]
        self.name = entry.title
        self.signal = SIGNAL_UPDATED.format(entry.entry_id)
        self.connected = False
        self.measurement = None
        self.session_last = None
        self.session_min = None
        self.session_max = None
        self.session_start = None
        self.session_end = None
        self._task = None
        self._stopped = False

    @callback
    def start(self):
        return bluetooth.async_register_callback(
            self.hass,
            self._advertisement,
            {"address": self.address, "connectable": True},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )

    @callback
    def _advertisement(self, _info, _change):
        if not self._stopped and (self._task is None or self._task.done()):
            self._task = self.hass.async_create_background_task(
                self._run(), f"Heart Rate Monitor {self.address}"
            )

    async def stop(self):
        self._stopped = True
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run(self):
        while device := bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        ):
            await self._subscribe(device)
            await asyncio.sleep(5)

    async def _subscribe(self, device):
        disconnected = asyncio.Event()
        client = None

        def on_disconnect(_client):
            disconnected.set()
            self._set_disconnected()

        def on_measurement(_characteristic, payload):
            if disconnected.is_set():
                return
            try:
                measurement = parse_measurement(payload)
            except ValueError as err:
                _LOGGER.debug("Invalid measurement from %s: %s", self.address, err)
                return
            rate = measurement.heart_rate
            if self.measurement is None:
                self.session_min = self.session_max = rate
            else:
                self.session_min = min(self.session_min, rate)
                self.session_max = max(self.session_max, rate)
            self.measurement = measurement
            self._publish()

        try:
            client = await establish_connection(
                BleakClientWithServiceCache,
                device,
                self.name,
                disconnected_callback=on_disconnect,
            )
            await client.start_notify(MEASUREMENT_UUID, on_measurement)
            if not disconnected.is_set() and client.is_connected:
                self.session_start = dt_util.utcnow()
                self.session_end = None
                self.session_last = None
                self.connected = True
                self._publish()
                await disconnected.wait()
        except (BleakError, TimeoutError, OSError) as err:
            _LOGGER.debug("BLE session failed for %s: %s", self.address, err)
        finally:
            disconnected.set()
            self._set_disconnected()
            if client is not None and client.is_connected:
                with suppress(BleakError, TimeoutError, OSError):
                    await client.disconnect()

    @callback
    def _set_disconnected(self):
        if self.connected:
            self.session_end = dt_util.utcnow()
            if self.measurement is not None:
                self.session_last = self.measurement.heart_rate
        if self.connected or self.measurement is not None:
            self.connected = False
            self.measurement = None
            self._publish()

    @callback
    def _publish(self):
        async_dispatcher_send(self.hass, self.signal)
