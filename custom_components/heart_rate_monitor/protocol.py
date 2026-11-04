"""Decode standard Bluetooth Heart Rate Measurement notifications."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Measurement:
    heart_rate: int
    contact: bool | None
    energy: int | None
    rr_intervals: tuple[float, ...]


def parse_measurement(data: bytes) -> Measurement:
    if not data:
        raise ValueError("Missing flags")

    flags = data[0]
    offset = 1

    def read_uint(size: int) -> int:
        nonlocal offset
        end = offset + size
        if end > len(data):
            raise ValueError("Truncated measurement")
        value = int.from_bytes(data[offset:end], "little")
        offset = end
        return value

    heart_rate = read_uint(2 if flags & 0x01 else 1)
    contact = bool(flags & 0x02) if flags & 0x04 else None
    energy = read_uint(2) if flags & 0x08 else None
    intervals = []
    if flags & 0x10:
        intervals.append(read_uint(2) * 1000 / 1024)
        while offset < len(data):
            intervals.append(read_uint(2) * 1000 / 1024)

    return Measurement(heart_rate, contact, energy, tuple(intervals))
