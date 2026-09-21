"""
Automated Unit Tests for services/risk_analysis_service.py and core/ai_explainer.py
"""
import unittest

from backend.services.risk_analysis_service import FullIntelligenceResult, perform_full_intelligence_scan


class TestRiskAnalysisService(unittest.TestCase):
    """Test suite for Risk Analysis Service & AI Explainer."""

    def test_full_intelligence_scan_live_domain(self):
        """Test complete multi-layered intelligence scan on google.com."""
        full_res = perform_full_intelligence_scan("google.com", save_to_db=False)

        self.assertIsNotNone(full_res.base_lookup)
        self.assertEqual(full_res.base_lookup.input, "google.com")
        self.assertIsNotNone(full_res.security)
        self.assertTrue(full_res.security.https_enabled)
        self.assertIsNotNone(full_res.ip_intel)
        self.assertIsNotNone(full_res.risk)
        self.assertGreaterEqual(full_res.risk.trust_score, 0)
        self.assertLessEqual(full_res.risk.trust_score, 100)
        self.assertIsNotNone(full_res.chain)
        self.assertIn("google.com", full_res.chain.domain_or_input)
        self.assertIsNotNone(full_res.explanation)
        self.assertIn("google.com", full_res.explanation)
        self.assertIn("Trust Score", full_res.explanation)


if __name__ == "__main__":
    unittest.main()
