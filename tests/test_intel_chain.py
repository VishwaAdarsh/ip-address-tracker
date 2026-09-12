"""
Automated Unit Tests for core/intel_chain.py
"""
import unittest

from core.intel_chain import IntelligenceChain, build_intelligence_chain, generate_ip_personality
from core.ip_intel import IPIntelligence
from services.lookup_service import LookupResult, LookupStatus


class TestIntelChain(unittest.TestCase):
    """Test suite for Intelligence Chain & IP Personality module."""

    def test_ip_personality_generation(self):
        """Test natural language IP personality synthesis."""
        p = generate_ip_personality("google.com", "142.250.118.138", "Google LLC", "Cloud Hosting", "Mountain View", "United States")
        self.assertIn("Cloud Hosting", p)
        self.assertIn("Mountain View, United States", p)

    def test_build_intelligence_chain(self):
        """Test building full intelligence chain from lookup result and ip intel."""
        lookup = LookupResult(
            input="google.com",
            normalized_input="google.com",
            input_type="DOMAIN",
            selected_ip="142.250.118.138",
            country="United States",
            country_code="US",
            region="California",
            city="Mountain View",
            organization="Google LLC",
            overall_status=LookupStatus.SUCCESS,
        )
        intel = IPIntelligence(
            ip_address="142.250.118.138",
            infrastructure_type="Cloud Hosting",
            organization="Google LLC",
        )

        chain = build_intelligence_chain(lookup, intel)
        self.assertEqual(chain.domain_or_input, "google.com")
        self.assertEqual(chain.resolved_ip, "142.250.118.138")
        self.assertEqual(chain.infrastructure_type, "Cloud Hosting")
        self.assertIn("Google LLC", chain.ip_personality)


if __name__ == "__main__":
    unittest.main()
