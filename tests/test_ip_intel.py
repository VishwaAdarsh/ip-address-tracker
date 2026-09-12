"""
Automated Unit Tests for core/ip_intel.py
"""
import unittest

from core.ip_intel import IPIntelligence, analyze_ip_intelligence, classify_infrastructure


class TestIPIntel(unittest.TestCase):
    """Test suite for IP Intelligence Engine module."""

    def test_cloudflare_cdn_classification(self):
        """Test classification of Cloudflare CDN edge hub."""
        intel = analyze_ip_intelligence("104.16.132.229", asn="AS13335", org="Cloudflare, Inc.", isp="Cloudflare")
        self.assertEqual(intel.infrastructure_type, "CDN / Edge Hub")
        self.assertEqual(intel.hosting_provider, "Cloudflare")
        self.assertTrue(intel.is_datacenter)
        self.assertEqual(intel.threat_level, "Low")

    def test_aws_cloud_hosting_classification(self):
        """Test classification of Amazon AWS cloud hosting."""
        intel = analyze_ip_intelligence("54.239.28.85", asn="AS16509", org="Amazon.com, Inc.", isp="AWS Datacenter")
        self.assertEqual(intel.infrastructure_type, "Cloud Hosting")
        self.assertEqual(intel.hosting_provider, "Amazon")
        self.assertTrue(intel.is_datacenter)

    def test_anonymizer_vpn_tor_detection(self):
        """Test detection of VPN and Tor exit nodes."""
        tor_intel = analyze_ip_intelligence("185.220.101.5", asn="AS208367", org="Tor Exit Node Network", isp="Mullvad VPN")
        self.assertTrue(tor_intel.is_tor)
        self.assertTrue(tor_intel.is_vpn)
        self.assertEqual(tor_intel.threat_level, "High")


if __name__ == "__main__":
    unittest.main()
