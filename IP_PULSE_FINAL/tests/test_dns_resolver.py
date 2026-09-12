"""
Unit and integration tests for core/dns_resolver.py.
"""
import unittest
from core.dns_resolver import DNSResult, DNSStatus, resolve_domain
from core.validator import is_valid_ipv4, is_valid_ipv6


class TestDNSResolver(unittest.TestCase):
    """Tests for the DNS resolution module."""

    def test_successful_domain_resolution(self):
        """Test DNS resolution for a known public domain (example.com)."""
        res = resolve_domain("example.com")
        self.assertEqual(res.status, DNSStatus.SUCCESS)
        self.assertIsNone(res.error_message)
        self.assertGreater(len(res.all_addresses), 0)
        self.assertGreaterEqual(res.resolution_time_ms, 0.0)
        self.assertIsNotNone(res.timestamp)

        # Verify all returned IP strings are valid IPv4 or IPv6 addresses
        for ip in res.all_addresses:
            self.assertTrue(
                is_valid_ipv4(ip) or is_valid_ipv6(ip),
                f"Returned IP {ip} is not a valid IPv4 or IPv6 address",
            )

    def test_multiple_ip_categorization_and_deduplication(self):
        """Test that IPv4 and IPv6 addresses are properly categorized without duplicates."""
        res = resolve_domain("google.com")
        self.assertEqual(res.status, DNSStatus.SUCCESS)

        # Check deduplication
        self.assertEqual(
            len(res.all_addresses),
            len(set(res.all_addresses)),
            "all_addresses contains duplicate IP entries",
        )
        self.assertEqual(
            len(res.ipv4_addresses),
            len(set(res.ipv4_addresses)),
            "ipv4_addresses contains duplicate IP entries",
        )
        self.assertEqual(
            len(res.ipv6_addresses),
            len(set(res.ipv6_addresses)),
            "ipv6_addresses contains duplicate IP entries",
        )

        # Verify element typing
        for ip in res.ipv4_addresses:
            self.assertTrue(is_valid_ipv4(ip))
        for ip in res.ipv6_addresses:
            self.assertTrue(is_valid_ipv6(ip))

    def test_nonexistent_domain_resolution(self):
        """Test that resolving a nonexistent domain fails gracefully."""
        res = resolve_domain("nonexistent-domain-test-xyz123987.invalid")
        self.assertEqual(res.status, DNSStatus.DNS_FAILED)
        self.assertIsNotNone(res.error_message)
        self.assertEqual(len(res.all_addresses), 0)
        self.assertEqual(len(res.ipv4_addresses), 0)
        self.assertEqual(len(res.ipv6_addresses), 0)
        self.assertGreaterEqual(res.resolution_time_ms, 0.0)

    def test_invalid_input_handling(self):
        """Test that invalid inputs return INVALID_DOMAIN status."""
        invalid_inputs = ["hello@123", "", "   ", None, "invalid_domain!"]
        for raw in invalid_inputs:
            with self.subTest(raw=raw):
                res = resolve_domain(raw)
                self.assertEqual(res.status, DNSStatus.INVALID_DOMAIN)
                self.assertIsNotNone(res.error_message)

    def test_direct_ip_input(self):
        """Test passing an IP address directly to the resolver."""
        res_v4 = resolve_domain("8.8.8.8")
        self.assertEqual(res_v4.status, DNSStatus.SUCCESS)
        self.assertEqual(res_v4.ipv4_addresses, ["8.8.8.8"])
        self.assertEqual(res_v4.all_addresses, ["8.8.8.8"])

        res_v6 = resolve_domain("2001:4860:4860::8888")
        self.assertEqual(res_v6.status, DNSStatus.SUCCESS)
        self.assertEqual(res_v6.ipv6_addresses, ["2001:4860:4860::8888"])
        self.assertEqual(res_v6.all_addresses, ["2001:4860:4860::8888"])


if __name__ == "__main__":
    unittest.main()
