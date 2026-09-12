"""
Unit and integration tests for services/lookup_service.py.
"""
import unittest
from unittest.mock import patch

from core.dns_resolver import DNSResult, DNSStatus
from core.normalizer import GeoResult, GeoStatus
from services.lookup_service import (
    LookupResult,
    LookupStatus,
    perform_lookup,
    select_primary_ip,
)


class TestLookupService(unittest.TestCase):
    """Tests for the integrated lookup service."""

    def test_ip_selection_rule(self):
        """Test deterministic IP selection logic."""
        ipv4_list = ["192.168.1.1", "192.168.1.2"]
        ipv6_list = ["2001:db8::1", "2001:db8::2"]

        # 1. Prefer IPv4 over IPv6
        self.assertEqual(select_primary_ip(ipv4_list, ipv6_list), "192.168.1.1")

        # 2. Fallback to IPv6 if IPv4 list is empty
        self.assertEqual(select_primary_ip([], ipv6_list), "2001:db8::1")

        # 3. Return None if both are empty
        self.assertIsNone(select_primary_ip([], []))

    def test_invalid_input(self):
        """Test invalid input returns INVALID_INPUT status without triggering DNS or Geo."""
        invalid_inputs = ["hello@123", "", "   ", None, "invalid_domain!"]
        for raw in invalid_inputs:
            with self.subTest(raw=raw):
                res = perform_lookup(raw)
                self.assertEqual(res.overall_status, LookupStatus.INVALID_INPUT)
                self.assertEqual(res.dns_status, "NOT_ATTEMPTED")
                self.assertEqual(res.geolocation_status, "NOT_ATTEMPTED")
                self.assertIsNotNone(res.error_message)

    @patch("services.lookup_service.get_geolocation")
    def test_direct_ipv4_lookup(self, mock_geo):
        """Test direct IPv4 lookup skips DNS resolution."""
        mock_geo.return_value = GeoResult(
            ip="8.8.8.8",
            ip_version="IPv4",
            country="United States",
            city="Mountain View",
            status=GeoStatus.SUCCESS,
        )

        res = perform_lookup("8.8.8.8")
        self.assertEqual(res.overall_status, LookupStatus.SUCCESS)
        self.assertEqual(res.dns_status, "SKIPPED")
        self.assertEqual(res.geolocation_status, "SUCCESS")
        self.assertEqual(res.selected_ip, "8.8.8.8")
        self.assertEqual(res.ipv4_addresses, ["8.8.8.8"])
        self.assertEqual(res.dns_response_time_ms, 0.0)
        self.assertGreaterEqual(res.total_response_time_ms, 0.0)

    @patch("services.lookup_service.get_geolocation")
    def test_direct_ipv6_lookup(self, mock_geo):
        """Test direct IPv6 lookup skips DNS resolution."""
        mock_geo.return_value = GeoResult(
            ip="2001:4860:4860::8888",
            ip_version="IPv6",
            country="United States",
            status=GeoStatus.SUCCESS,
        )

        res = perform_lookup("2001:4860:4860::8888")
        self.assertEqual(res.overall_status, LookupStatus.SUCCESS)
        self.assertEqual(res.dns_status, "SKIPPED")
        self.assertEqual(res.selected_ip, "2001:4860:4860::8888")
        self.assertEqual(res.ipv6_addresses, ["2001:4860:4860::8888"])

    @patch("services.lookup_service.get_geolocation")
    @patch("services.lookup_service.resolve_domain")
    def test_domain_successful_lookup(self, mock_dns, mock_geo):
        """Test successful end-to-end domain lookup workflow."""
        mock_dns.return_value = DNSResult(
            domain="example.com",
            ipv4_addresses=["93.184.216.34"],
            ipv6_addresses=["2606:2800:220:1:248:1893:25c8:1946"],
            all_addresses=["93.184.216.34", "2606:2800:220:1:248:1893:25c8:1946"],
            resolution_time_ms=15.5,
            status=DNSStatus.SUCCESS,
        )

        mock_geo.return_value = GeoResult(
            ip="93.184.216.34",
            ip_version="IPv4",
            country="United States",
            city="Los Angeles",
            status=GeoStatus.SUCCESS,
        )

        res = perform_lookup("example.com")
        self.assertEqual(res.overall_status, LookupStatus.SUCCESS)
        self.assertEqual(res.dns_status, "SUCCESS")
        self.assertEqual(res.geolocation_status, "SUCCESS")
        self.assertEqual(res.selected_ip, "93.184.216.34")
        self.assertEqual(res.ipv4_addresses, ["93.184.216.34"])
        self.assertEqual(
            res.ipv6_addresses, ["2606:2800:220:1:248:1893:25c8:1946"]
        )
        self.assertEqual(res.dns_response_time_ms, 15.5)

    @patch("services.lookup_service.get_geolocation")
    @patch("services.lookup_service.resolve_domain")
    def test_dns_failure_handling(self, mock_dns, mock_geo):
        """Test DNS failure prevents calling geolocation service."""
        mock_dns.return_value = DNSResult(
            domain="nonexistent.invalid",
            resolution_time_ms=10.0,
            status=DNSStatus.DNS_FAILED,
            error_message="Name resolution failed",
        )

        res = perform_lookup("nonexistent.invalid")
        self.assertEqual(res.overall_status, LookupStatus.DNS_FAILED)
        self.assertEqual(res.dns_status, "DNS_FAILED")
        self.assertEqual(res.geolocation_status, "NOT_ATTEMPTED")
        self.assertIsNone(res.selected_ip)
        self.assertIn("Name resolution failed", res.error_message)
        mock_geo.assert_not_called()

    @patch("services.lookup_service.get_geolocation")
    @patch("services.lookup_service.resolve_domain")
    def test_geolocation_failure_handling(self, mock_dns, mock_geo):
        """Test geolocation failure retains DNS resolution results."""
        mock_dns.return_value = DNSResult(
            domain="example.com",
            ipv4_addresses=["93.184.216.34"],
            all_addresses=["93.184.216.34"],
            resolution_time_ms=12.0,
            status=DNSStatus.SUCCESS,
        )

        mock_geo.return_value = GeoResult(
            ip="93.184.216.34",
            ip_version="IPv4",
            status=GeoStatus.API_TIMEOUT,
            error_message="Request timed out",
        )

        res = perform_lookup("example.com")
        self.assertEqual(res.overall_status, LookupStatus.GEO_FAILED)
        self.assertEqual(res.dns_status, "SUCCESS")
        self.assertEqual(res.geolocation_status, "API_TIMEOUT")
        self.assertEqual(res.selected_ip, "93.184.216.34")
        self.assertEqual(res.ipv4_addresses, ["93.184.216.34"])
        self.assertEqual(res.country, "N/A")
        self.assertEqual(res.error_message, "Request timed out")


if __name__ == "__main__":
    unittest.main()
