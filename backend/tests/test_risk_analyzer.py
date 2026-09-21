"""
Automated Unit Tests for analysis/risk_analyzer.py
"""
import os
import unittest

from backend.analytics.risk_analyzer import compute_risk_analytics_from_dataset


class TestRiskAnalyzer(unittest.TestCase):
    """Test suite for Risk Analyzer module."""

    def test_compute_risk_analytics_from_dataset(self):
        """Test dataset risk analysis stats calculation."""
        csv_p = "data/field_test/websites.csv"
        if not os.path.exists(csv_p):
            self.skipTest("Field test CSV not found")

        stats = compute_risk_analytics_from_dataset(csv_p)
        self.assertIn("sample_size", stats)
        self.assertGreater(stats["sample_size"], 0)
        self.assertIn("trust_score_stats", stats)
        self.assertIn("infrastructure_distribution", stats)
        self.assertIn("security_adoption", stats)


if __name__ == "__main__":
    unittest.main()
