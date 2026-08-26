"""
Unit tests for gui/map_view.py coordinate validation logic.
"""
import unittest
from gui.map_view import validate_coordinates


class TestMapView(unittest.TestCase):
    """Tests for coordinate validation logic used in map rendering."""

    def test_valid_coordinates(self):
        """Test that valid latitude and longitude pairs pass validation."""
        valid_cases = [
            (19.0760, 72.8777),
            (37.3860, -122.0838),
            (0.0, 0.0),
            (90.0, 180.0),
            (-90.0, -180.0),
            ("19.0760", "72.8777"),
        ]
        for lat, lon in valid_cases:
            with self.subTest(lat=lat, lon=lon):
                is_valid, lat_f, lon_f, err = validate_coordinates(lat, lon)
                self.assertTrue(is_valid, f"Expected ({lat}, {lon}) to be valid")
                self.assertIsNotNone(lat_f)
                self.assertIsNotNone(lon_f)
                self.assertIsNone(err)

    def test_invalid_latitude(self):
        """Test out-of-range latitude values."""
        invalid_lats = [90.1, -90.1, 100.0, -120.0]
        for lat in invalid_lats:
            with self.subTest(lat=lat):
                is_valid, _, _, err = validate_coordinates(lat, 0.0)
                self.assertFalse(is_valid)
                self.assertIn("Latitude", err)

    def test_invalid_longitude(self):
        """Test out-of-range longitude values."""
        invalid_lons = [180.1, -180.1, 200.0, -360.0]
        for lon in invalid_lons:
            with self.subTest(lon=lon):
                is_valid, _, _, err = validate_coordinates(0.0, lon)
                self.assertFalse(is_valid)
                self.assertIn("Longitude", err)

    def test_missing_and_none_coordinates(self):
        """Test missing, None, or empty string coordinate values."""
        missing_cases = [
            (None, 72.8777),
            (19.0760, None),
            (None, None),
            ("", ""),
            (19.0760, ""),
        ]
        for lat, lon in missing_cases:
            with self.subTest(lat=lat, lon=lon):
                is_valid, lat_f, lon_f, err = validate_coordinates(lat, lon)
                self.assertFalse(is_valid)
                self.assertIsNone(lat_f)
                self.assertIsNone(lon_f)
                self.assertIsNotNone(err)

    def test_non_numeric_coordinates(self):
        """Test non-numeric text coordinates."""
        is_valid, _, _, err = validate_coordinates("invalid_lat", "invalid_lon")
        self.assertFalse(is_valid)
        self.assertIn("non-numeric", err.lower())


if __name__ == "__main__":
    unittest.main()
