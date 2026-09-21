"""
Automated Unit Tests for IP Intelligence & Infrastructure Analysis (Phase 16).
"""
import unittest

from backend.intelligence.ip_intel import (
    IPIntelligenceProvider,
    IPIntelligenceResult,
    StandardIPIntelligenceProvider,
    analyze_ip_infrastructure,
    analyze_ip_intelligence,
)


class MockFailingProvider(IPIntelligenceProvider):
    """Mock provider simulating network timeout or HTTP 429 quota exhaustion."""

    def analyze_ip(self, ip_address: str, asn: str = "", org: str = "", isp: str = "", raw_signals: dict = None) -> IPIntelligenceResult:
        res = IPIntelligenceResult(ip_address=ip_address)
        res.errors.append("HTTP 429: API Quota Exhausted")
        # Explicit Unknown status values on failure
        res.vpn_status = "Unknown"
        res.proxy_status = "Unknown"
        res.tor_status = "Unknown"
        res.datacenter_status = "Unknown"
        return res


class TestPhase16IPIntelligence(unittest.TestCase):
    """Test suite for Phase 16 IP Intelligence Engine."""

    def test_valid_ipv4_cloud_infrastructure(self):
        """Test IPv4 classification on Google Cloud infrastructure."""
        res = analyze_ip_infrastructure("142.250.118.138", asn="AS15169", org="Google LLC", isp="Google LLC")
        self.assertEqual(res.ip_address, "142.250.118.138")
        self.assertEqual(res.ip_version, "IPv4")
        self.assertEqual(res.infrastructure_type, "Cloud Hosting")
        self.assertEqual(res.network_type, "Cloud")
        self.assertEqual(res.datacenter_status, "Detected")

    def test_valid_ipv6_classification(self):
        """Test IPv6 version detection and classification."""
        res = analyze_ip_infrastructure("2607:f8b0:4005:805::200e", asn="AS15169", org="Google LLC", isp="Google LLC")
        self.assertEqual(res.ip_version, "IPv6")
        self.assertEqual(res.infrastructure_type, "Cloud Hosting")

    def test_commercial_isp_residential_ip(self):
        """Test Commercial ISP network classification."""
        res = analyze_ip_infrastructure("73.15.20.1", asn="AS7922", org="Comcast Cable Communications", isp="Comcast")
        self.assertEqual(res.infrastructure_type, "Commercial ISP")
        self.assertEqual(res.network_type, "Residential")
        self.assertEqual(res.datacenter_status, "Not Detected")
        # Datacenter IP or ISP does NOT automatically imply VPN! Explicit Unknown/Not Detected.
        self.assertIn(res.vpn_status, ["Not Detected", "Unknown"])

    def test_anonymizer_tor_vpn_proxy_signals(self):
        """Test Tor, VPN, and Proxy detection signals."""
        raw = {"tor": True, "vpn": True, "proxy": False}
        res = analyze_ip_infrastructure("185.220.101.5", asn="AS208367", org="Tor Exit Node", isp="Mullvad VPN", raw_signals=raw)
        self.assertEqual(res.tor_status, "Detected")
        self.assertEqual(res.vpn_status, "Detected")
        self.assertEqual(res.proxy_status, "Not Detected")

    def test_quota_429_provider_failure_graceful_handling(self):
        """Test provider failure / HTTP 429 quota handling returning explicit Unknown states."""
        failing_provider = MockFailingProvider()
        res = analyze_ip_infrastructure("8.8.8.8", provider=failing_provider)
        self.assertEqual(res.ip_address, "8.8.8.8")
        self.assertEqual(res.vpn_status, "Unknown")
        self.assertEqual(res.proxy_status, "Unknown")
        self.assertEqual(res.tor_status, "Unknown")
        self.assertIn("HTTP 429: API Quota Exhausted", res.errors)

    def test_invalid_ip_format(self):
        """Test invalid IP handling."""
        res = analyze_ip_infrastructure("invalid_ip_text")
        self.assertIn("Invalid IP address format", res.errors)
        self.assertEqual(res.ip_version, "Unknown")

    def test_backward_compatible_ip_intelligence_bridge(self):
        """Test backward compatibility with analyze_ip_intelligence bridge."""
        intel = analyze_ip_intelligence("104.16.132.229", asn="AS13335", org="Cloudflare, Inc.", isp="Cloudflare")
        self.assertEqual(intel.infrastructure_type, "CDN / Edge Hub")
        self.assertTrue(intel.is_datacenter)


if __name__ == "__main__":
    unittest.main()
