# Release history

## v0.1.2 — Wait for a new heart rate advertisement

- After a BLE session ends, wait for a fresh Heart Rate Service advertisement before reconnecting. This avoids repeated connection attempts based on cached device data after broadcasting is turned off.
- Log BLE disconnect errors at debug level.

## v0.1.1 — Separate live and final session heart rate

- Added **Session Last Heart Rate**. It captures the final reading when the device disconnects and stays available until the next session starts.
- **Heart Rate** now becomes unavailable on disconnect, leaving a gap in the history between sessions.

## v0.1.0 — Initial release

Heart Rate Monitor brings live heart rate readings from Bluetooth Low Energy devices into Home Assistant. It discovers devices that advertise the standard Bluetooth Heart Rate Service through a local Bluetooth adapter or an ESPHome Bluetooth proxy.

- Live heart rate and connection status.
- Session minimum and maximum heart rate, start and end times, and duration.
- The last heart rate and session summary remain available after disconnect and are restored after a Home Assistant restart.
- Optional skin contact, energy expended, and RR interval sensors appear when the device reports those fields.
- Historical readings are available through Home Assistant Recorder.

**Tested device** — Amazfit Active 2 (Square) in heart rate broadcast mode. Compatibility with other devices has yet to be verified.
