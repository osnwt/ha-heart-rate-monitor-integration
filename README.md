# Heart Rate Monitor Integration

English · [Русский](README.ru.md)

A Home Assistant integration for Bluetooth Low Energy heart rate monitors. Home Assistant discovers devices advertising the standard Heart Rate Service (`0x180D`) through a local Bluetooth adapter or Bluetooth Proxy. You can add or ignore each device under **Settings → Devices & services → Discovered**.

**Compatibility.** This integration has been tested only with the **Amazfit Active 2 (Square)** in heart rate broadcast mode. Compatibility with other devices that advertise the standard BLE Heart Rate Service has yet to be verified.

## Installation

1. In Home Assistant 2026.11 or later, open **Settings → Marketplace** and add [osnwt/ha-heart-rate-monitor-integration](https://github.com/osnwt/ha-heart-rate-monitor-integration) as a custom integration repository. On earlier versions with HACS, use **Custom repositories → Integration**.
2. Install **Heart Rate Monitor** and restart Home Assistant.
3. Enable heart rate broadcasting on the device and add it under **Settings → Devices & services → Discovered**.

For manual installation, copy `custom_components/heart_rate_monitor` from this repository into the `custom_components/` folder in your Home Assistant configuration directory. Then restart Home Assistant and follow step 3.

## Local development

1. From the repository root, run `./scripts/start.sh`.
2. Open [Home Assistant](http://localhost:8123) and complete onboarding.
3. Add your Bluetooth proxies through the ESPHome integration. If discovery in Docker fails, enter the proxy's IP address manually when adding ESPHome. The proxy must support active BLE connections. If the watch is missing while the proxy is scanning passively, set its scanning mode to **Auto** or **Active**.
4. Enable heart rate broadcasting on the device and add the discovered **Heart Rate Monitor**.

Copy `.env.example` to `.env` to change the port or container name. The container loads the integration from `custom_components/`. Home Assistant configuration, history, and proxy settings are stored locally in `data/` and excluded from Git.

- `./scripts/logs.sh` follows the Home Assistant log.
- `./scripts/status.sh` shows container status.
- `./scripts/restart.sh` restarts the container after code changes.
- `./scripts/stop.sh` stops the container.

## Measurements and sessions

When an added device is discovered, the integration connects and subscribes to the Heart Rate Measurement characteristic (`0x2A37`). Each device has its own configuration entry and in-memory state.

| Entity | Meaning |
| --- | --- |
| Connected | A BLE connection with an active measurement subscription |
| Heart Rate | Beats per minute. The packet flag indicates whether the value is an 8-bit or 16-bit integer |
| Skin Contact | Whether the sensor detects skin contact, when the device reports support for this feature |
| Energy Expended | Accumulated energy in kilojoules |
| RR Interval | The latest interval in milliseconds. The `intervals_ms` attribute contains all intervals in the packet |
| Session Min Heart Rate | Lowest heart rate recorded in the session, in beats per minute |
| Session Max Heart Rate | Highest heart rate recorded in the session, in beats per minute |
| Session Start | Time when the integration successfully subscribed to measurements |
| Session End | Time when the connection ended |
| Session Duration | Elapsed time in seconds between session start and end |

Measurement entities appear when the integration first receives their corresponding fields. The parser discards incomplete packets and ignores reserved flags. See the [Bluetooth Heart Rate Service specification](https://www.bluetooth.com/wp-content/uploads/Files/Specification/HTML/HRS_v1.0/out/en/index-en.html).

On disconnect, `Connected` turns off and the `connected` attribute of `Heart Rate` becomes `false`. The last heart rate and session minimum and maximum remain available and are restored after a Home Assistant restart. The minimum and maximum are also available as `session_min` and `session_max` attributes on `Heart Rate`. The first measurement of the next session resets both values. Skin contact, energy, and RR intervals become `unavailable` on disconnect. The integration reconnects when the device becomes available again.

Session timestamps are restored after a restart and kept until the next connection. `Session End` and `Session Duration` remain `unavailable` while a session is active or if the disconnect time was never recorded.

To view earlier readings, open **History** and select the device's `Heart Rate` entity. The standard Home Assistant Recorder stores entity history according to its configured retention period.

## Parser tests

```sh
python3 -m unittest discover -s tests
```

## License

[MIT](LICENSE)
