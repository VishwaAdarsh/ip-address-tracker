"""
Unit tests for services/field_test_service.py (Manual-First Field Project Workflow).
"""
import csv
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from database.db import save_lookup
from database.models import LookupRecord
from services.field_test_service import (
    FIELD_TEST_HEADERS,
    export_field_dataset_from_history,
    get_field_project_status,
    load_test_websites,
    run_automatic_completion,
)
from services.lookup_service import LookupResult, LookupStatus, perform_lookup


class TestFieldTestServiceManualFirst(unittest.TestCase):
    """Test suite for manual-first field project workflow and automatic completion."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_field.db")
        self.csv_path = os.path.join(self.tmp_dir.name, "test_results.csv")

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _create_mock_result(self, domain: str, ip: str = "1.1.1.1") -> LookupResult:
        return LookupResult(
            input=domain,
            normalized_input=domain,
            input_type="DOMAIN",
            overall_status=LookupStatus.SUCCESS,
            dns_status="SUCCESS",
            geolocation_status="SUCCESS",
            resolved_addresses=[ip],
            ipv4_addresses=[ip],
            selected_ip=ip,
            ip_version="IPv4",
            country="United States",
            country_code="US",
            region="California",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            organization="Cloudflare",
            isp="Cloudflare",
            asn="AS13335",
            dns_response_time_ms=10.0,
            api_response_time_ms=50.0,
            total_response_time_ms=60.0,
        )

    def test_scenario_1_history_0_observations(self):
        """Scenario 1: History contains 0 valid observations -> remaining = 50."""
        st = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st["available_count"], 0)
        self.assertEqual(st["remaining"], 50)
        self.assertEqual(st["status"], "INCOMPLETE")

    def test_scenario_2_history_20_observations(self):
        """Scenario 2: History contains 20 valid observations -> remaining = 30."""
        for i in range(1, 21):
            res = self._create_mock_result(f"site{i}.com")
            save_lookup(res, db_path=self.db_path)

        st = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st["available_count"], 20)
        self.assertEqual(st["remaining"], 30)
        self.assertEqual(st["status"], "INCOMPLETE")

    def test_scenario_3_history_49_observations(self):
        """Scenario 3: History contains 49 valid observations -> remaining = 1."""
        for i in range(1, 50):
            res = self._create_mock_result(f"site{i}.com")
            save_lookup(res, db_path=self.db_path)

        st = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st["available_count"], 49)
        self.assertEqual(st["remaining"], 1)

    def test_scenario_4_history_exactly_50_observations(self):
        """Scenario 4: History contains exactly 50 -> no automatic completion required."""
        for i in range(1, 51):
            res = self._create_mock_result(f"site{i}.com")
            save_lookup(res, db_path=self.db_path)

        st = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st["available_count"], 50)
        self.assertEqual(st["remaining"], 0)
        self.assertEqual(st["status"], "TARGET_REACHED")

    def test_scenario_5_history_70_observations(self):
        """Scenario 5: History contains 70 observations -> target already reached."""
        for i in range(1, 71):
            res = self._create_mock_result(f"site{i}.com")
            save_lookup(res, db_path=self.db_path)

        st = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st["available_count"], 70)
        self.assertEqual(st["remaining"], 0)
        self.assertEqual(st["status"], "TARGET_REACHED")

    def test_scenario_6_duplicate_domain_deduplication(self):
        """Scenario 6: Duplicate domain observations deduplicated properly."""
        # Add 10 lookups for google.com
        for _ in range(10):
            save_lookup(self._create_mock_result("google.com"), db_path=self.db_path)

        st = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st["available_count"], 1)
        self.assertEqual(st["remaining"], 49)

    @patch("services.field_test_service.perform_lookup")
    def test_scenario_7_automatic_completion_overrun_prevention(self, mock_perform_lookup):
        """Scenario 7: Automatic completion requested for 13 -> attempts at most 13 lookups."""
        mock_perform_lookup.side_effect = lambda dom, save_to_db=True, db_path=None: save_lookup(
            self._create_mock_result(dom), db_path=self.db_path
        )

        # Seed 37 unique domains
        for i in range(1, 38):
            save_lookup(self._create_mock_result(f"existing{i}.com"), db_path=self.db_path)

        st_before = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st_before["remaining"], 13)

        run_automatic_completion(db_path=self.db_path, output_csv_path=self.csv_path, delay_seconds=0.0)

        # Ensure no more than 13 lookups were attempted
        self.assertEqual(mock_perform_lookup.call_count, 13)

        st_after = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st_after["available_count"], 50)
        self.assertEqual(st_after["remaining"], 0)

    def test_scenario_8_existing_history_remains_intact(self):
        """Scenario 8: Existing History records remain intact during field export."""
        res = self._create_mock_result("example.org")
        rec_id = save_lookup(res, db_path=self.db_path)

        export_field_dataset_from_history(db_path=self.db_path, output_csv_path=self.csv_path)

        st = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st["available_count"], 1)
        self.assertTrue(os.path.exists(self.csv_path))

    def test_scenario_9_normal_manual_lookup(self):
        """Scenario 9: Normal manual lookup adds to History and updates status."""
        st1 = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st1["available_count"], 0)

        res = perform_lookup("test-manual.com", save_to_db=True, db_path=self.db_path)
        self.assertEqual(res.normalized_input, "test-manual.com")

        st2 = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st2["available_count"], 1)

    def test_scenario_10_field_project_refresh(self):
        """Scenario 10: Field project refreshes count after new manual lookups."""
        st1 = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st1["available_count"], 0)

        # Perform 5 manual lookups
        for d in ["siteA.com", "siteB.com", "siteC.com", "siteD.com", "siteE.com"]:
            perform_lookup(d, save_to_db=True, db_path=self.db_path)

        st2 = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st2["available_count"], 5)
        self.assertEqual(st2["remaining"], 45)


if __name__ == "__main__":
    unittest.main()
