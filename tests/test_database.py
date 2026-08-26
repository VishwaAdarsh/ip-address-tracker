"""
Unit tests for database/db.py and database/models.py.
"""
from pathlib import Path
import tempfile
import unittest

from database.db import (
    clear_history,
    delete_lookup,
    get_lookup_history,
    init_db,
    save_lookup,
)
from database.models import LookupRecord
from services.lookup_service import LookupResult, LookupStatus


class TestDatabase(unittest.TestCase):
    """Tests for SQLite database operations."""

    def setUp(self):
        """Create a temporary database file for isolated testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_ip_tracker.db"
        init_db(self.db_path)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_database_initialization(self):
        """Test that database schema initializes cleanly and is idempotent."""
        self.assertTrue(self.db_path.exists())
        # Re-run initialization to ensure it does not drop existing tables
        init_db(self.db_path)
        self.assertTrue(self.db_path.exists())

    def test_save_and_retrieve_lookup(self):
        """Test saving a LookupResult and retrieving it from history."""
        sample_result = LookupResult(
            input="google.com",
            normalized_input="google.com",
            input_type="DOMAIN",
            resolved_addresses=["142.250.29.113"],
            ipv4_addresses=["142.250.29.113"],
            selected_ip="142.250.29.113",
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
            dns_response_time_ms=10.5,
            api_response_time_ms=150.2,
            total_response_time_ms=160.7,
            dns_status="SUCCESS",
            geolocation_status="SUCCESS",
            overall_status=LookupStatus.SUCCESS,
            error_message=None,
        )

        record_id = save_lookup(sample_result, db_path=self.db_path)
        self.assertIsNotNone(record_id)
        self.assertGreater(record_id, 0)

        history = get_lookup_history(db_path=self.db_path)
        self.assertEqual(len(history), 1)

        rec = history[0]
        self.assertEqual(rec.id, record_id)
        self.assertEqual(rec.input_value, "google.com")
        self.assertEqual(rec.domain, "google.com")
        self.assertEqual(rec.ip_address, "142.250.29.113")
        self.assertEqual(rec.country, "United States")
        self.assertEqual(rec.latitude, 37.386)
        self.assertEqual(rec.longitude, -122.0838)
        self.assertEqual(rec.status, "SUCCESS")

    def test_multiple_and_duplicate_lookups(self):
        """Test inserting multiple lookups including duplicates with different timestamps."""
        res1 = LookupResult(
            input="example.com",
            normalized_input="example.com",
            input_type="DOMAIN",
            selected_ip="93.184.216.34",
            overall_status=LookupStatus.SUCCESS,
            timestamp="2026-08-26T10:00:00+00:00",
        )
        res2 = LookupResult(
            input="example.com",
            normalized_input="example.com",
            input_type="DOMAIN",
            selected_ip="93.184.216.34",
            overall_status=LookupStatus.SUCCESS,
            timestamp="2026-08-26T11:00:00+00:00",
        )

        id1 = save_lookup(res1, db_path=self.db_path)
        id2 = save_lookup(res2, db_path=self.db_path)

        history = get_lookup_history(db_path=self.db_path)
        self.assertEqual(len(history), 2)

        # Verify newest timestamp record is retrieved first
        self.assertEqual(history[0].id, id2)
        self.assertEqual(history[1].id, id1)

    def test_delete_lookup(self):
        """Test deleting a single record by ID."""
        res = LookupResult(
            input="8.8.8.8",
            normalized_input="8.8.8.8",
            input_type="IPV4",
            selected_ip="8.8.8.8",
            overall_status=LookupStatus.SUCCESS,
        )
        rec_id = save_lookup(res, db_path=self.db_path)

        deleted = delete_lookup(rec_id, db_path=self.db_path)
        self.assertTrue(deleted)

        history = get_lookup_history(db_path=self.db_path)
        self.assertEqual(len(history), 0)

        # Deleting non-existent ID should return False
        self.assertFalse(delete_lookup(9999, db_path=self.db_path))

    def test_clear_history(self):
        """Test clearing all records from the lookup history."""
        res1 = LookupResult(
            input="1.1.1.1",
            normalized_input="1.1.1.1",
            input_type="IPV4",
            selected_ip="1.1.1.1",
            overall_status=LookupStatus.SUCCESS,
        )
        res2 = LookupResult(
            input="8.8.8.8",
            normalized_input="8.8.8.8",
            input_type="IPV4",
            selected_ip="8.8.8.8",
            overall_status=LookupStatus.SUCCESS,
        )
        save_lookup(res1, db_path=self.db_path)
        save_lookup(res2, db_path=self.db_path)

        self.assertEqual(len(get_lookup_history(db_path=self.db_path)), 2)

        cleared = clear_history(db_path=self.db_path)
        self.assertTrue(cleared)
        self.assertEqual(len(get_lookup_history(db_path=self.db_path)), 0)

    def test_null_and_missing_optional_fields(self):
        """Test saving result with null/missing optional fields."""
        res = LookupResult(
            input="invalid-domain.test",
            normalized_input="invalid-domain.test",
            input_type="DOMAIN",
            dns_status="DNS_FAILED",
            geolocation_status="NOT_ATTEMPTED",
            overall_status=LookupStatus.DNS_FAILED,
            error_message="Name resolution failed",
            latitude=None,
            longitude=None,
        )
        rec_id = save_lookup(res, db_path=self.db_path)
        self.assertIsNotNone(rec_id)

        history = get_lookup_history(db_path=self.db_path)
        self.assertEqual(len(history), 1)
        rec = history[0]
        self.assertIsNone(rec.latitude)
        self.assertIsNone(rec.longitude)
        self.assertEqual(rec.error_message, "Name resolution failed")
        self.assertEqual(rec.status, "DNS_FAILED")


if __name__ == "__main__":
    unittest.main()
