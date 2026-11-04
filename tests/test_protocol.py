import unittest

from custom_components.heart_rate_monitor.protocol import Measurement, parse_measurement


class TestMeasurement(unittest.TestCase):
    def test_heart_rate_only(self):
        self.assertEqual(parse_measurement(bytes([0, 72])), Measurement(72, None, None, ()))

    def test_all_fields(self):
        packet = bytes.fromhex("1f 2c01 0000 0004 0002")
        self.assertEqual(parse_measurement(packet), Measurement(300, True, 0, (1000, 500)))

    def test_contact_without_contact_detected(self):
        self.assertIs(parse_measurement(bytes([4, 72])).contact, False)

    def test_reserved_flags_and_trailing_bytes(self):
        self.assertEqual(parse_measurement(bytes([0xE2, 72, 255])), Measurement(72, None, None, ()))

    def test_truncated_packets(self):
        for packet in ("", "00", "01 48", "08 48 01", "10 48", "10 48 0004 01"):
            with self.subTest(packet=packet), self.assertRaises(ValueError):
                parse_measurement(bytes.fromhex(packet))
