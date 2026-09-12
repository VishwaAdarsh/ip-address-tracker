"""
Unit tests for core/geo_service.py geolocation service module.
"""
import io
import json
import socket
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from core.geo_service import get_geolocation
from core.normalizer import GeoStatus


class TestGeoService(unittest.TestCase):
    """Tests for the geolocation service."""

    def test_invalid_ip_handling(self):
        """Test that invalid IP strings are rejected prior to network requests."""
        invalid_ips = ["not_an_ip", "256.0.0.1", "hello@123", "", None]
        for ip in invalid_ips:
            with self.subTest(ip=ip):
                res = get_geolocation(ip)
                self.assertEqual(res.status, GeoStatus.INVALID_IP)
                self.assertIsNotNone(res.error_message)

    @patch("urllib.request.urlopen")
    def test_successful_geolocation_lookup(self, mock_urlopen):
        """Test successful HTTPS geolocation response handling."""
        mock_data = {
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
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_response.__enter__.return_value = mock_response

        mock_urlopen.return_value = mock_response

        res = get_geolocation("8.8.8.8")
        self.assertEqual(res.status, GeoStatus.SUCCESS)
        self.assertEqual(res.ip, "8.8.8.8")
        self.assertEqual(res.country, "United States")
        self.assertEqual(res.city, "Mountain View")
        self.assertEqual(res.latitude, 37.386)
        self.assertEqual(res.longitude, -122.0838)
        self.assertEqual(res.organization, "Google LLC")

    @patch("urllib.request.urlopen")
    def test_timeout_handling(self, mock_urlopen):
        """Test handling of request timeout."""
        mock_urlopen.side_effect = urllib.error.URLError(socket.timeout("timed out"))

        res = get_geolocation("8.8.8.8", timeout=1.0)
        self.assertEqual(res.status, GeoStatus.API_TIMEOUT)
        self.assertIn("timed out", res.error_message.lower())

    @patch("urllib.request.urlopen")
    def test_rate_limit_429_handling(self, mock_urlopen):
        """Test HTTP 429 Rate Limit response handling."""
        fp = io.BytesIO(b"Rate limit exceeded")
        err = urllib.error.HTTPError(
            "https://ipapi.co/8.8.8.8/json/", 429, "Too Many Requests", {}, fp
        )
        mock_urlopen.side_effect = err

        res = get_geolocation("8.8.8.8")
        self.assertEqual(res.status, GeoStatus.API_RATE_LIMIT)
        self.assertIn("rate limit", res.error_message.lower())

    @patch("urllib.request.urlopen")
    def test_auth_error_401_handling(self, mock_urlopen):
        """Test HTTP 401 Authentication error response handling."""
        fp = io.BytesIO(b"Unauthorized")
        err = urllib.error.HTTPError(
            "https://ipapi.co/8.8.8.8/json/", 401, "Unauthorized", {}, fp
        )
        mock_urlopen.side_effect = err

        res = get_geolocation("8.8.8.8")
        self.assertEqual(res.status, GeoStatus.API_AUTH_ERROR)
        self.assertIn("authentication", res.error_message.lower())

    @patch("urllib.request.urlopen")
    def test_http_500_error_handling(self, mock_urlopen):
        """Test HTTP 500 Server error response handling."""
        fp = io.BytesIO(b"Internal Server Error")
        err = urllib.error.HTTPError(
            "https://ipapi.co/8.8.8.8/json/", 500, "Server Error", {}, fp
        )
        mock_urlopen.side_effect = err

        res = get_geolocation("8.8.8.8")
        self.assertEqual(res.status, GeoStatus.API_HTTP_ERROR)
        self.assertIn("500", res.error_message)


if __name__ == "__main__":
    unittest.main()
