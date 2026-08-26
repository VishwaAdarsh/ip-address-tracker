"""
Unit tests for analysis package modules (analyzer.py, visualizer.py, report_generator.py).
"""
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from analysis.analyzer import (
    compute_descriptive_stats,
    compute_distributions,
    compute_missing_data_report,
    load_and_validate_dataset,
)
from analysis.visualizer import generate_all_charts


class TestAnalysis(unittest.TestCase):
    """Test suite for data analysis, descriptive statistics, and chart visualizer."""

    def setUp(self):
        """Create sample DataFrame representing field-test results."""
        self.sample_data = {
            "test_id": [str(i) for i in range(1, 6)],
            "domain": ["google.com", "bing.com", "github.com", "mit.edu", "failed.xyz"],
            "category": ["Search", "Search", "Technology", "Education", "Technology"],
            "timestamp": ["2026-08-26T12:00:00Z"] * 5,
            "input_type": ["DOMAIN"] * 5,
            "dns_status": ["SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "DNS_FAILED"],
            "ipv4_addresses": ["142.250.190.46", "13.107.21.200", "140.82.121.4", "18.9.22.69", ""],
            "ipv6_addresses": ["", "", "", "", ""],
            "selected_ip": ["142.250.190.46", "13.107.21.200", "140.82.121.4", "18.9.22.69", ""],
            "ip_version": ["IPv4", "IPv4", "IPv4", "IPv4", "N/A"],
            "country": ["United States", "United States", "United States", "United States", "N/A"],
            "country_code": ["US", "US", "US", "US", "N/A"],
            "region": ["California", "Washington", "California", "Massachusetts", "N/A"],
            "city": ["Mountain View", "Redmond", "San Francisco", "Cambridge", "N/A"],
            "latitude": ["37.386", "47.674", "37.7749", "42.3601", ""],
            "longitude": ["-122.0838", "-122.1215", "-122.4194", "-71.0942", ""],
            "timezone": ["America/Los_Angeles", "America/Los_Angeles", "America/Los_Angeles", "America/New_York", "N/A"],
            "organization": ["Google LLC", "Microsoft Corp", "GitHub Inc", "MIT", "N/A"],
            "isp": ["Google LLC", "Microsoft Corp", "GitHub Inc", "MIT", "N/A"],
            "asn": ["AS15169", "AS8075", "AS36459", "AS3", "N/A"],
            "dns_response_time_ms": [10.0, 15.0, 20.0, 25.0, 30.0],
            "api_response_time_ms": [100.0, 150.0, 200.0, 250.0, 0.0],
            "total_response_time_ms": [110.0, 165.0, 220.0, 275.0, 30.0],
            "geolocation_status": ["SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "SKIPPED"],
            "overall_status": ["SUCCESS", "SUCCESS", "SUCCESS", "SUCCESS", "DNS_FAILED"],
            "error_message": ["", "", "", "", "DNS resolution failed"],
        }
        self.df = pd.DataFrame(self.sample_data)

    def test_descriptive_stats_computation(self):
        """Test calculation of mean, median, min, max, and percentiles."""
        stats = compute_descriptive_stats(self.df)

        self.assertIn("dns_response_time_ms", stats)
        dns_s = stats["dns_response_time_ms"]
        self.assertEqual(dns_s["count"], 5)
        self.assertEqual(dns_s["min"], 10.0)
        self.assertEqual(dns_s["max"], 30.0)
        self.assertEqual(dns_s["median"], 20.0)
        self.assertEqual(dns_s["mean"], 20.0)

    def test_missing_data_report(self):
        """Test detection of missing and N/A values."""
        report = compute_missing_data_report(self.df)
        self.assertIn("city", report)
        self.assertEqual(report["city"]["present_count"], 4)
        self.assertEqual(report["city"]["missing_count"], 1)
        self.assertEqual(report["city"]["missing_percentage"], 20.0)

    def test_distributions(self):
        """Test categorical distribution calculations."""
        dists = compute_distributions(self.df)
        c_dist = dists.get("country_distribution", {})
        self.assertEqual(c_dist.get("United States"), 4)
        self.assertEqual(c_dist.get("N/A"), 1)

        v_dist = dists.get("ip_version_distribution", {})
        self.assertEqual(v_dist.get("IPv4"), 4)

    def test_chart_generation(self):
        """Test that all 7 PNG charts are generated without error."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            chart_paths = generate_all_charts(self.df, tmp_dir)
            self.assertEqual(len(chart_paths), 7)
            for p in chart_paths:
                self.assertTrue(Path(p).exists())
                self.assertTrue(Path(p).stat().st_size > 0)


if __name__ == "__main__":
    unittest.main()
