import struct
import sys
import types
import unittest
from unittest.mock import patch


class _Response:
    status = 200
    reason = "OK"

    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload


class _Connection:
    def __init__(self, payload):
        self._response = _Response(payload)

    def request(self, method, path, headers):
        self.request_args = (method, path, headers)

    def getresponse(self):
        return self._response


class WindowCaptureProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fake_bpy = types.ModuleType("bpy")
        with patch.dict(sys.modules, {"bpy": fake_bpy}):
            sys.modules.pop("window_capture", None)
            import window_capture
        cls.window_capture = window_capture

    def _module(self):
        return self.window_capture

    def test_uses_canvas_bridge_dimensions_above_1024(self):
        width, height, sequence = 2048, 1536, 42
        pixels = bytes(width * height * 4)
        payload = b"CBRG" + struct.pack("<IIQ", width, height, sequence) + pixels

        window_capture = self._module()

        actual = window_capture._fetch_frame(_Connection(payload), "/frame/main/rgba")

        self.assertEqual(actual[:3], (width, height, sequence))
        self.assertEqual(len(actual[3]), width * height * 4)

    def test_parses_tile_delta_and_sends_last_applied_sequence(self):
        width, height, sequence = 4, 3, 43
        tile_pixels = bytes([10, 20, 30, 255, 40, 50, 60, 255])
        payload = (
            b"CBT1"
            + struct.pack("<IIQHI", width, height, sequence, 64, 1)
            + struct.pack("<HHHH", 1, 1, 2, 1)
            + tile_pixels
        )
        connection = _Connection(payload)
        window_capture = self._module()

        actual = window_capture._fetch_frame(
            connection, "/frame/main/rgba", since=42
        )

        self.assertEqual(actual[:3], (width, height, sequence))
        self.assertIsNone(actual[3])
        self.assertEqual(connection.request_args[1], "/frame/main/rgba?since=42")
        self.assertEqual(len(actual[4]), 1)
        self.assertEqual(tuple(actual[4][0][:4]), (1, 1, 2, 1))
        self.assertEqual(bytes(actual[4][0][4]), tile_pixels)

    def test_applies_tile_into_reusable_float_buffer(self):
        window_capture = self._module()
        if window_capture.np is None:
            self.skipTest("NumPy is not available")
        output = window_capture.np.zeros(4 * 3 * 4, dtype=window_capture.np.float32)
        raw = memoryview(bytes([255, 0, 128, 255, 0, 255, 64, 255]))

        actual = window_capture._apply_tile_pixels(
            output, 4, 3, [(1, 1, 2, 1, raw)]
        ).reshape(3, 4, 4)

        self.assertIs(actual.base, output)
        self.assertAlmostEqual(float(actual[1, 1, 0]), 1.0)
        self.assertAlmostEqual(float(actual[1, 1, 2]), 128.0 / 255.0)
        self.assertAlmostEqual(float(actual[1, 2, 1]), 1.0)
        self.assertEqual(float(actual[0, 0, 0]), 0.0)

    def test_consumer_refresh_does_not_scan_materials_or_force_view_layer(self):
        window_capture = self._module()

        class Image:
            def __init__(self):
                self.tagged = 0

            def update_tag(self):
                self.tagged += 1

        image = Image()
        window_capture._refresh_material_consumers(image)
        self.assertEqual(image.tagged, 1)


if __name__ == "__main__":
    unittest.main()
