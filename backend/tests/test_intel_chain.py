"""
Automated Unit Tests for core/intel_chain.py (Phase 18).
Validates deterministic IP Personality profile generation, 6-node intelligence chain,
unknown-data handling, boundary rules, and edge-case resilience.
"""
import unittest

from backend.intelligence.intel_chain import (
    CHAIN_DISCLAIMER,
    PERSONALITY_DISCLAIMER,
    IntelligenceChain,
    IPPersonality,
    build_intelligence_chain,
    generate_ip_personality,
    generate_ip_personality_profile,
)
from backend.intelligence.ip_intel import IPIntelligence, IPIntelligenceResult
from backend.services.lookup_service import LookupResult, LookupStatus


class TestIntelChain(unittest.TestCase):
    """Test suite for Intelligence Chain & IP Personality module."""

    # --------------------------------------------------------------------------
    # Backward Compatibility
    # --------------------------------------------------------------------------
    def test_legacy_ip_personality_generation(self):
        """Test backward-compatible natural language IP personality synthesis string."""
        p = generate_ip_personality("google.com", "142.250.118.138", "Google LLC", "Cloud Hosting", "Mountain View", "United States")
        self.assertIn("Cloud Hosting", p)
        self.assertIn("Mountain View, United States", p)

    def test_legacy_build_intelligence_chain(self):
        """Test building intelligence chain with legacy assertions."""
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
        self.assertIsNotNone(chain.personality)
        self.assertEqual(len(chain.nodes), 6)

    # --------------------------------------------------------------------------
    # Scenario 1: Cloud Infrastructure
    # --------------------------------------------------------------------------
    def test_01_cloud_infrastructure(self):
        intel = IPIntelligence(
            infrastructure_type="Cloud Hosting",
            organization="Google LLC",
            is_datacenter=True,
        )
        personality = generate_ip_personality_profile(intel)
        self.assertIn("CLOUD HOSTED", personality.labels)
        self.assertIn("DATACENTER INFRASTRUCTURE", personality.labels)
        self.assertIn("cloud", personality.summary.lower())

    # --------------------------------------------------------------------------
    # Scenario 2: Datacenter Infrastructure
    # --------------------------------------------------------------------------
    def test_02_datacenter_infrastructure(self):
        intel = IPIntelligenceResult(
            ip_address="209.85.233.100",
            infrastructure_type="Datacenter",
            datacenter_status="Detected",
            organization="Equinix Inc.",
        )
        personality = generate_ip_personality_profile(intel)
        self.assertIn("DATACENTER INFRASTRUCTURE", personality.labels)
        self.assertNotIn("RESIDENTIAL NETWORK", personality.labels)

    # --------------------------------------------------------------------------
    # Scenario 3: Residential Infrastructure
    # --------------------------------------------------------------------------
    def test_03_residential_infrastructure(self):
        intel = IPIntelligenceResult(
            ip_address="73.189.10.25",
            infrastructure_type="Commercial ISP",
            network_type="Residential",
            organization="Comcast Cable Communications",
            datacenter_status="Not Detected",
            tor_status="Not Detected",
            proxy_status="Not Detected",
            vpn_status="Not Detected",
        )
        personality = generate_ip_personality_profile(intel)
        self.assertIn("RESIDENTIAL NETWORK", personality.labels)
        self.assertIn("LOW ANONYMIZATION", personality.labels)
        self.assertNotIn("DATACENTER INFRASTRUCTURE", personality.labels)

    # --------------------------------------------------------------------------
    # Scenario 4: Mobile Infrastructure
    # --------------------------------------------------------------------------
    def test_04_mobile_infrastructure(self):
        intel = IPIntelligence(
            infrastructure_type="Mobile",
            organization="Vodafone Group",
        )
        personality = generate_ip_personality_profile(intel)
        self.assertIn("MOBILE NETWORK", personality.labels)
        self.assertIn("mobile", personality.summary.lower())

    # --------------------------------------------------------------------------
    # Scenario 5: VPN Detected
    # --------------------------------------------------------------------------
    def test_05_vpn_detected(self):
        intel = IPIntelligenceResult(
            ip_address="185.220.101.5",
            infrastructure_type="Datacenter",
            vpn_status="Detected",
            tor_status="Not Detected",
            proxy_status="Not Detected",
        )
        personality = generate_ip_personality_profile(intel)
        self.assertIn("VPN ASSOCIATED", personality.labels)
        self.assertNotIn("LOW ANONYMIZATION", personality.labels)
        self.assertIn("VPN", personality.summary)

    # --------------------------------------------------------------------------
    # Scenario 6: Proxy Detected
    # --------------------------------------------------------------------------
    def test_06_proxy_detected(self):
        intel = IPIntelligenceResult(
            ip_address="194.67.210.12",
            infrastructure_type="Datacenter",
            proxy_status="Detected",
            tor_status="Not Detected",
            vpn_status="Not Detected",
        )
        personality = generate_ip_personality_profile(intel)
        self.assertIn("PROXY ASSOCIATED", personality.labels)
        self.assertNotIn("LOW ANONYMIZATION", personality.labels)
        self.assertIn("proxy", personality.summary.lower())

    # --------------------------------------------------------------------------
    # Scenario 7: Tor Detected
    # --------------------------------------------------------------------------
    def test_07_tor_detected(self):
        intel = IPIntelligenceResult(
            ip_address="185.220.101.5",
            infrastructure_type="Cloud Hosting",
            tor_status="Detected",
            proxy_status="Not Detected",
            vpn_status="Not Detected",
        )
        personality = generate_ip_personality_profile(intel)
        self.assertIn("TOR ASSOCIATED", personality.labels)
        self.assertNotIn("LOW ANONYMIZATION", personality.labels)
        self.assertIn("Tor", personality.summary)

    # --------------------------------------------------------------------------
    # Scenario 8: All Anonymization Signals Absent
    # --------------------------------------------------------------------------
    def test_08_all_anonymization_signals_absent(self):
        intel = IPIntelligenceResult(
            ip_address="8.8.8.8",
            infrastructure_type="Cloud Hosting",
            tor_status="Not Detected",
            proxy_status="Not Detected",
            vpn_status="Not Detected",
        )
        personality = generate_ip_personality_profile(intel)
        self.assertIn("LOW ANONYMIZATION", personality.labels)

    # --------------------------------------------------------------------------
    # Scenario 9: Unknown Infrastructure
    # --------------------------------------------------------------------------
    def test_09_unknown_infrastructure(self):
        intel = IPIntelligenceResult(
            ip_address="10.0.0.1",
            infrastructure_type="Unknown",
            tor_status="Unknown",
            proxy_status="Unknown",
            vpn_status="Unknown",
            datacenter_status="Unknown",
        )
        personality = generate_ip_personality_profile(intel)
        # Unknown infrastructure must NOT default to Residential or Safe
        self.assertNotIn("RESIDENTIAL NETWORK", personality.labels)
        self.assertNotIn("LOW ANONYMIZATION", personality.labels)
        self.assertIn("INFRASTRUCTURE UNCLASSIFIED", personality.labels)
        self.assertEqual(personality.confidence, "UNKNOWN")

    # --------------------------------------------------------------------------
    # Scenario 10: Unknown VPN/Proxy/Tor
    # --------------------------------------------------------------------------
    def test_10_unknown_anonymization(self):
        intel = IPIntelligenceResult(
            ip_address="34.120.55.10",
            infrastructure_type="Cloud Hosting",
            tor_status="Unknown",
            proxy_status="Unknown",
            vpn_status="Unknown",
        )
        personality = generate_ip_personality_profile(intel)
        # Crucial principle: Unknown != Not Detected
        self.assertNotIn("LOW ANONYMIZATION", personality.labels)
        self.assertIn("CLOUD HOSTED", personality.labels)
        self.assertIn("Additional anonymization signals were unavailable", personality.summary)

    # --------------------------------------------------------------------------
    # Scenario 11: Partial Intelligence Data
    # --------------------------------------------------------------------------
    def test_11_partial_intelligence_data(self):
        # Graceful handling when intel is None or partially filled
        personality_none = generate_ip_personality_profile(None)
        self.assertIsNotNone(personality_none)
        self.assertGreaterEqual(len(personality_none.labels), 1)
        self.assertIn("Assessment limited", personality_none.summary)

        chain_partial = build_intelligence_chain(None, None)
        self.assertIsNotNone(chain_partial)
        self.assertEqual(len(chain_partial.nodes), 6)
        self.assertEqual(chain_partial.domain_or_input, "Unknown")
        self.assertEqual(chain_partial.resolved_ip, "Unknown")

    # --------------------------------------------------------------------------
    # Scenario 12: Complete 6-Node Intelligence Chain
    # --------------------------------------------------------------------------
    def test_12_complete_intelligence_chain(self):
        lookup = LookupResult(
            input="cloudflare.com",
            normalized_input="cloudflare.com",
            input_type="DOMAIN",
            selected_ip="104.16.132.229",
            ip_version="IPv4",
            asn="AS13335",
            organization="Cloudflare, Inc.",
            isp="Cloudflare, Inc.",
            country="United States",
            country_code="US",
            region="California",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            overall_status=LookupStatus.SUCCESS,
        )
        intel = IPIntelligenceResult(
            ip_address="104.16.132.229",
            infrastructure_type="CDN / Edge Hub",
            organization="Cloudflare, Inc.",
            asn="AS13335",
            tor_status="Not Detected",
            proxy_status="Not Detected",
            vpn_status="Not Detected",
        )

        chain = build_intelligence_chain(lookup, intel)
        self.assertEqual(len(chain.nodes), 6)

        # Verify exact 6-node flow: Domain -> IP -> ASN -> Org -> Infra -> Location
        keys = [n["key"] for n in chain.nodes]
        self.assertEqual(keys, ["domain", "ip", "asn", "organization", "infrastructure", "location"])

        self.assertEqual(chain.nodes[0]["value"], "cloudflare.com")
        self.assertEqual(chain.nodes[0]["status"], "RESOLVED")

        self.assertEqual(chain.nodes[1]["value"], "104.16.132.229")
        self.assertEqual(chain.nodes[1]["status"], "RESOLVED")

        self.assertEqual(chain.nodes[2]["value"], "AS13335")
        self.assertEqual(chain.nodes[2]["status"], "ASSIGNED")

        self.assertEqual(chain.nodes[3]["value"], "Cloudflare, Inc.")
        self.assertEqual(chain.nodes[3]["status"], "IDENTIFIED")

        self.assertEqual(chain.nodes[4]["value"], "CDN / Edge Hub")
        self.assertEqual(chain.nodes[4]["status"], "CLASSIFIED")

        self.assertIn("San Francisco", chain.nodes[5]["value"])
        self.assertEqual(chain.nodes[5]["status"], "GEOLOCATED")

    # --------------------------------------------------------------------------
    # Scenario 13: Partial Intelligence Chain (Direct IP Target)
    # --------------------------------------------------------------------------
    def test_13_partial_intelligence_chain_direct_ip(self):
        lookup = LookupResult(
            input="1.1.1.1",
            normalized_input="1.1.1.1",
            input_type="IPV4",
            selected_ip="1.1.1.1",
            country="Australia",
            city="Sydney",
            organization="Cloudflare, Inc.",
            overall_status=LookupStatus.SUCCESS,
        )
        intel = IPIntelligence(
            ip_address="1.1.1.1",
            infrastructure_type="CDN / Edge Hub",
        )

        chain = build_intelligence_chain(lookup, intel)
        self.assertEqual(chain.nodes[0]["value"], "Direct IP Target")
        self.assertEqual(chain.nodes[0]["status"], "DIRECT")
        self.assertEqual(chain.nodes[1]["value"], "1.1.1.1")

    # --------------------------------------------------------------------------
    # Scenario 14: Missing Organization Fallback
    # --------------------------------------------------------------------------
    def test_14_missing_organization(self):
        lookup = LookupResult(
            input="8.8.8.8",
            normalized_input="8.8.8.8",
            input_type="IPV4",
            selected_ip="8.8.8.8",
            organization=None,
            isp=None,
        )
        intel = IPIntelligence(
            ip_address="8.8.8.8",
            organization="N/A",
            isp="N/A",
        )

        chain = build_intelligence_chain(lookup, intel)
        org_node = next(n for n in chain.nodes if n["key"] == "organization")
        self.assertIn(org_node["value"], ["Unknown", "N/A"])
        self.assertEqual(org_node["status"], "UNKNOWN")

    # --------------------------------------------------------------------------
    # Scenario 15: Missing Location Fallback
    # --------------------------------------------------------------------------
    def test_15_missing_location(self):
        lookup = LookupResult(
            input="192.168.1.1",
            normalized_input="192.168.1.1",
            input_type="IPV4",
            selected_ip="192.168.1.1",
            city=None,
            region=None,
            country=None,
            latitude=None,
            longitude=None,
        )
        intel = IPIntelligence(ip_address="192.168.1.1")

        chain = build_intelligence_chain(lookup, intel)
        loc_node = next(n for n in chain.nodes if n["key"] == "location")
        self.assertEqual(loc_node["value"], "Unknown Location")
        self.assertEqual(loc_node["status"], "UNKNOWN")

    # --------------------------------------------------------------------------
    # Scenario 16: Strict Determinism
    # --------------------------------------------------------------------------
    def test_16_strict_determinism(self):
        intel = IPIntelligenceResult(
            ip_address="8.8.4.4",
            infrastructure_type="Cloud Hosting",
            organization="Google LLC",
            datacenter_status="Detected",
            tor_status="Not Detected",
            proxy_status="Not Detected",
            vpn_status="Not Detected",
        )
        first_prof = generate_ip_personality_profile(intel)

        for _ in range(50):
            next_prof = generate_ip_personality_profile(intel)
            self.assertEqual(first_prof.labels, next_prof.labels)
            self.assertEqual(first_prof.summary, next_prof.summary)
            self.assertEqual(first_prof.confidence, next_prof.confidence)

    # --------------------------------------------------------------------------
    # Scenario 17: Label Count Limit (Max 3–5)
    # --------------------------------------------------------------------------
    def test_17_personality_label_limit(self):
        intel = IPIntelligenceResult(
            ip_address="104.16.1.1",
            infrastructure_type="CDN / Edge Hub",
            organization="Cloudflare Global Network",
            datacenter_status="Detected",
            tor_status="Not Detected",
            proxy_status="Not Detected",
            vpn_status="Not Detected",
        )
        lookup = LookupResult(
            input="cloudflare.com",
            normalized_input="cloudflare.com",
            input_type="DOMAIN",
            ip_version="IPv6",
        )
        personality = generate_ip_personality_profile(intel, lookup)
        self.assertLessEqual(len(personality.labels), 5)
        self.assertGreaterEqual(len(personality.labels), 2)

    # --------------------------------------------------------------------------
    # Scenario 18: CDN Edge Node Personality
    # --------------------------------------------------------------------------
    def test_18_cdn_edge_node_personality(self):
        intel = IPIntelligenceResult(
            ip_address="151.101.1.1",
            infrastructure_type="CDN / Edge Hub",
            organization="Fastly, Inc.",
            tor_status="Not Detected",
            proxy_status="Not Detected",
            vpn_status="Not Detected",
        )
        personality = generate_ip_personality_profile(intel)
        self.assertIn("CDN EDGE NODE", personality.labels)
        self.assertIn("GLOBAL NETWORK", personality.labels)
        self.assertIn("LOW ANONYMIZATION", personality.labels)


if __name__ == "__main__":
    unittest.main()
