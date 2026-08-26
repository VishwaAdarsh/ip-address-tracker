"""
Unit tests for services/field_test_service.py.
"""
import csv
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from core.normalizer import GeoStatus
from services.field_test_service import (
    FIELD_TEST_HEADERS,
    load_test_websites,
    run_field_test,
)
from services.lookup_service import LookupResult, LookupStatus


class TestFieldTestService(unittest.TestCase):
    """Test suite for field-test dataset loading, validation, sequential execution, and CSV output."""

    def test_load_test_websites_success(self):
        """Test loading predefined websites.csv dataset."""
        websites = load_test_websites()
        self.assertEqual(len(websites), 50)

        ids = [w["test_id"] for w in websites]
        domains = [w["domain"] for w in websites]

        # Verify IDs 1 to 50
        self.assertEqual(ids, [str(i) for i in range(1, 51)])
        # Verify 50 unique domains
        self.assertEqual(len(set(domains)), 50)

    def test_load_test_websites_duplicate_validation(self):
        """Test validation error detection for invalid CSV files."""
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
            tmp.write("test_id,domain,category\n1,example.com,Tech\n1,example2.com,Tech\n")

        with self.assertRaises(ValueError):
            load_test_websites(tmp_path)

    @patch("services.field_test_service.perform_lookup")
    def test_run_field_test_sequential_and_csv_output(self, mock_perform_lookup):
        """Test sequential execution and CSV research dataset output using mocked lookups."""
        mock_result = LookupResult(
            input="google.com",
            normalized_input="google.com",
            input_type="DOMAIN",
            overall_status=LookupStatus.SUCCESS,
            dns_status="SUCCESS",
            geolocation_status="SUCCESS",
            resolved_addresses=["142.250.190.46"],
            ipv4_addresses=["142.250.190.46"],
            ipv6_addresses=[],
            selected_ip="142.250.190.46",
            ip_version="IPv4",
            country="United States",
            country_code="US",
            region="California",
            city="Mountain View",
            latitude=37.386,
            longitude=-122.0838,
            timezone="America/Los_Angeles",
            organization="Google LLC",
            isp="Google LLC",
            asn="AS15169",
            dns_response_time_ms=12.5,
            api_response_time_ms=110.2,
            total_response_time_ms=122.7,
        )
        mock_perform_lookup.return_value = mock_result

        test_websites = [
            {"test_id": "1", "domain": "google.com", "category": "Search"},
            {"test_id": "2", "domain": "bing.com", "category": "Search"},
        ]

        progress_calls = []

        def _cb(curr, tot, dom, res):
            progress_calls.append((curr, tot, dom))

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
            tmp_csv = tmp.name

        results = run_field_test(
            websites=test_websites,
            output_csv_path=tmp_csv,
            progress_callback=_cb,
            delay_seconds=0.0,
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(len(progress_calls), 2)
        self.assertEqual(mock_perform_lookup.call_count, 2)

        # Verify CSV contents
        with open(tmp_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["test_id"], "1")
            self.assertEqual(rows[0]["domain"], "google.com")
            self.assertEqual(rows[0]["selected_ip"], "142.250.190.46")
            self.assertEqual(rows[0]["country"], "United States")

    @patch("services.field_test_service.perform_lookup")
    def test_run_field_test_failure_preservation(self, mock_perform_lookup):
        """Test that individual lookup failures are preserved in CSV output."""
        failed_result = LookupResult(
            input="failed-domain.xyz",
            normalized_input="failed-domain.xyz",
            input_type="DOMAIN",
            overall_status=LookupStatus.DNS_FAILED,
            dns_status="DNS_FAILED",
            geolocation_status="SKIPPED",
            error_message="Domain resolution failed",
        )
        mock_perform_lookup.return_value = failed_result

        test_websites = [
            {"test_id": "1", "domain": "failed-domain.xyz", "category": "Tech"}
        ]

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
            tmp_csv = tmp.name

        results = run_field_test(
            websites=test_websites, output_csv_path=tmp_csv, delay_seconds=0.0
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["overall_status"], "DNS_FAILED")
        self.assertEqual(results[0]["dns_status"], "DNS_FAILED")
        self.assertEqual(results[0]["error_message"], "Domain resolution failed")


if __name__ == "__main__":
    unittest.main()
