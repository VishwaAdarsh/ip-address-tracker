"""
Automated Unit Tests for core/risk_engine.py
"""
import unittest

from backend.intelligence.ip_intel import IPIntelligence
from backend.security.risk_engine import RiskScore, evaluate_trust_and_risk
from backend.security.security_scanner import SecurityInfo


class TestRiskEngine(unittest.TestCase):
    """Test suite for Trust & Risk Engine module."""

    def test_high_trust_secure_site(self):
        """Test score calculation for a secure, verified HTTPS website on CDN."""
        sec = SecurityInfo(
            https_enabled=True,
            ssl_valid=True,
            ssl_issuer="DigiCert",
            security_headers={"hsts": True, "csp": True, "x_frame_options": True},
        )
        intel = IPIntelligence(
            infrastructure_type="CDN / Edge Hub",
            hosting_provider="Cloudflare",
        )

        score = evaluate_trust_and_risk(sec, intel, geolocation_available=True)
        self.assertGreaterEqual(score.trust_score, 80)
        self.assertLessEqual(score.risk_score, 20)
        self.assertEqual(score.risk_level, "Low")
        self.assertGreater(len(score.positive_factors), 0)

    def test_high_risk_tor_site(self):
        """Test score calculation for a non-HTTPS site on Tor exit node."""
        sec = SecurityInfo(https_enabled=False, ssl_valid=False)
        intel = IPIntelligence(is_tor=True, infrastructure_type="Unknown")

        score = evaluate_trust_and_risk(sec, intel, geolocation_available=False)
        self.assertLessEqual(score.trust_score, 30)
        self.assertGreaterEqual(score.risk_score, 70)
        self.assertIn(score.risk_level, ["High", "Critical"])
        self.assertGreater(len(score.risk_factors), 0)


if __name__ == "__main__":
    unittest.main()
