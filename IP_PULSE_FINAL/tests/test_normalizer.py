"""
Unit tests for core/normalizer.py.
"""
import unittest
from core.normalizer import GeoResult, GeoStatus, detect_ip_version, normalize_geo_response


class TestResponseNormalizer(unittest.TestCase):
    """Tests for geolocation response normalization."""

    def test_complete_response_normalization(self):
        raw_json = {
            "ip": "8.8.8.8",
            "version": "IPv4",
            "city": "Mountain View",
            "region": "California",
            "country_name": "United States",
            "country_code": "US",
            "latitude": 37.386,
            "longitude": -122.0838,
            "timezone": "America/Los_Angeles",
            "asn": "AS15169",
            "org": "Google LLC",
            "isp": "Google LLC",
        }
        res = normalize_geo_response(raw_json, "8.8.8.8")
        self.assertEqual(res.ip, "8.8.8.8")
        self.assertEqual(res.ip_version, "IPv4")
        self.assertEqual(res.country, "United States")
        self.assertEqual(res.country_code, "US")
        self.assertEqual(res.region, "California")
        self.assertEqual(res.city, "Mountain View")
        self.assertEqual(res.latitude, 37.386)
        self.assertEqual(res.longitude, -122.0838)
        self.assertEqual(res.timezone, "America/Los_Angeles")
        self.assertEqual(res.organization, "Google LLC")
        self.assertEqual(res.isp, "Google LLC")
        self.assertEqual(res.asn, "AS15169")
        self.assertEqual(res.status, GeoStatus.SUCCESS)
        self.assertIsNone(res.error_message)

    def test_missing_optional_fields_fallback(self):
        raw_json = {
            "ip": "1.1.1.1",
            "country": "Australia",
            # city, region, lat/lon, org, asn missing
        }
        res = normalize_geo_response(raw_json, "1.1.1.1")
        self.assertEqual(res.ip, "1.1.1.1")
        self.assertEqual(res.country, "Australia")
        self.assertEqual(res.city, "N/A")
        self.assertEqual(res.region, "N/A")
        self.assertIsNone(res.latitude)
        self.assertIsNone(res.longitude)
        self.assertEqual(res.organization, "N/A")
        self.assertEqual(res.isp, "N/A")
        self.assertEqual(res.asn, "N/A")
        self.assertEqual(res.status, GeoStatus.SUCCESS)

    def test_provider_reported_error_response(self):
        raw_json = {"error": True, "reason": "Daily rate limit reached"}
        res = normalize_geo_response(raw_json, "8.8.8.8")
        self.assertEqual(res.status, GeoStatus.API_RATE_LIMIT)
        self.assertIn("Daily rate limit reached", res.error_message)

    def test_failed_status_handling(self):
        res = normalize_geo_response(
            None,
            "8.8.8.8",
            status=GeoStatus.API_TIMEOUT,
            error_message="Request timed out",
        )
        self.assertEqual(res.ip, "8.8.8.8")
        self.assertEqual(res.status, GeoStatus.API_TIMEOUT)
        self.assertEqual(res.error_message, "Request timed out")
        self.assertEqual(res.city, "N/A")
        self.assertIsNone(res.latitude)

    def test_ip_version_detection(self):
        self.assertEqual(detect_ip_version("8.8.8.8"), "IPv4")
        self.assertEqual(detect_ip_version("2001:4860:4860::8888"), "IPv6")
        self.assertEqual(detect_ip_version("invalid_ip"), "N/A")
        self.assertEqual(detect_ip_version(""), "N/A")


if __name__ == "__main__":
    unittest.main()
