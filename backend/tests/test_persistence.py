"""
Unit and integration tests for production datastore persistence, duplicate management,
record deletion, restart durability, and analytics derivation in IP PULSE.
"""
from pathlib import Path
import tempfile
import unittest

from backend.analytics.analytics_service import compute_field_study_analytics
from backend.database.db import (
    clear_field_study,
    clear_history,
    delete_field_observation,
    delete_field_observations_batch,
    delete_lookup,
    delete_lookups_batch,
    get_db_status,
    get_field_observation_by_domain,
    get_field_observation_by_id,
    get_field_observations,
    get_lookup_history,
    init_db,
    save_field_observation,
    save_lookup,
)
from backend.database.repository import SQLiteRepository, reset_repository_singleton
from backend.models.models import FieldObservation, LookupRecord
from backend.services.field_test_service import (
    add_field_observation,
    get_field_project_status,
)
from backend.services.lookup_service import LookupResult, LookupStatus


class TestProductionPersistence(unittest.TestCase):
    """Comprehensive test suite for persistence, duplicate handling, and deletion."""

    def setUp(self):
        """Create an isolated temporary database for each test case."""
        reset_repository_singleton()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_persistence.db"
        self.repo = SQLiteRepository(db_path=self.db_path)
        self.repo.init_schema()

    def tearDown(self):
        """Tear down repository connection and cleanup temporary storage."""
        if hasattr(self, "repo") and self.repo:
            self.repo.close()
        reset_repository_singleton()
        self.temp_dir.cleanup()

    def _sample_lookup_result(self, domain="cloudflare.com", ip="104.16.132.229"):
        """Create a complete LookupResult for testing."""
        return LookupResult(
            input=domain,
            normalized_input=domain,
            input_type="DOMAIN",
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
            timezone="America/Los_Angeles",
            organization="Cloudflare, Inc.",
            isp="Cloudflare, Inc.",
            asn="AS13335",
            dns_response_time_ms=12.4,
            api_response_time_ms=85.1,
            total_response_time_ms=97.5,
            dns_status="SUCCESS",
            geolocation_status="SUCCESS",
            overall_status=LookupStatus.SUCCESS,
            error_message=None,
        )

    def _sample_field_observation(self, domain="cloudflare.com", ip="104.16.132.229", test_id=1):
        """Create a complete FieldObservation for testing."""
        return FieldObservation(
            test_id=test_id,
            domain=domain,
            category="Security & CDN",
            resolved_ip=ip,
            ip_version="IPv4",
            country="United States",
            country_code="US",
            region="California",
            city="San Francisco",
            latitude=37.7749,
            longitude=-122.4194,
            geolocation_confidence="HIGH",
            organization="Cloudflare, Inc.",
            isp="Cloudflare, Inc.",
            asn="AS13335",
            network_type="Anycast CDN",
            infrastructure_type="Cloud / Datacenter",
            https_status="Enabled",
            tls_status="Valid",
            vpn_status="NOT_DETECTED",
            proxy_status="NOT_DETECTED",
            tor_status="NOT_DETECTED",
            website_trust_score=92.0,
            website_trust_classification="LIKELY SAFE",
            ip_risk_score=10.0,
            ip_risk_classification="LOW RISK",
            score_confidence="HIGH",
            evidence_coverage="8/8 signals",
            dns_response_time_ms=12.4,
            api_response_time_ms=85.1,
            searched_by="SecurityAuditor",
            observation_status="RECORDED",
        )

    # -------------------------------------------------------------------------
    # Scenario 1 & 2: Create and Read History Record
    # -------------------------------------------------------------------------
    def test_create_and_read_history_record(self):
        """Verify creating and retrieving lookup history records."""
        sample = self._sample_lookup_result("github.com", "140.82.112.3")
        rec_id = self.repo.save_lookup(sample)
        self.assertIsNotNone(rec_id)
        self.assertGreater(rec_id, 0)

        history = self.repo.get_lookup_history()
        self.assertEqual(len(history), 1)
        rec = history[0]
        self.assertEqual(rec.id, rec_id)
        self.assertEqual(rec.domain, "github.com")
        self.assertEqual(rec.ip_address, "140.82.112.3")
        self.assertEqual(rec.country, "United States")
        self.assertEqual(rec.status, "SUCCESS")

    # -------------------------------------------------------------------------
    # Scenario 3: Persist History After Simulated Restart
    # -------------------------------------------------------------------------
    def test_persist_history_after_restart(self):
        """Simulate backend service restart and confirm history records persist."""
        sample = self._sample_lookup_result("wikipedia.org", "208.80.154.224")
        rec_id = self.repo.save_lookup(sample)

        # Close current repository instance (simulate process teardown)
        self.repo.close()

        # Instantiate brand new repository pointing to the same file
        restarted_repo = SQLiteRepository(db_path=self.db_path)
        restarted_repo.init_schema()

        history = restarted_repo.get_lookup_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].id, rec_id)
        self.assertEqual(history[0].domain, "wikipedia.org")
        self.assertEqual(history[0].ip_address, "208.80.154.224")
        restarted_repo.close()

    # -------------------------------------------------------------------------
    # Scenario 4: Delete Individual History Record
    # -------------------------------------------------------------------------
    def test_delete_history_record(self):
        """Verify deleting an individual history record by primary key."""
        id1 = self.repo.save_lookup(self._sample_lookup_result("target1.com", "1.1.1.1"))
        id2 = self.repo.save_lookup(self._sample_lookup_result("target2.com", "2.2.2.2"))

        self.assertEqual(len(self.repo.get_lookup_history()), 2)

        deleted = self.repo.delete_lookup(id1)
        self.assertTrue(deleted)

        remaining = self.repo.get_lookup_history()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].id, id2)
        self.assertEqual(remaining[0].domain, "target2.com")

    # -------------------------------------------------------------------------
    # Scenario 5 & 6: Create and Read Field Study Observation
    # -------------------------------------------------------------------------
    def test_create_and_read_field_study_observation(self):
        """Verify saving and reading Field Study observations with complete telemetry."""
        obs = self._sample_field_observation("mozilla.org", "63.245.208.195", test_id=1)
        obs_id = self.repo.save_field_observation(obs)
        self.assertIsNotNone(obs_id)
        self.assertGreater(obs_id, 0)

        records = self.repo.get_field_observations()
        self.assertEqual(len(records), 1)
        r = records[0]
        self.assertEqual(r.id, obs_id)
        self.assertEqual(r.domain, "mozilla.org")
        self.assertEqual(r.resolved_ip, "63.245.208.195")
        self.assertEqual(r.website_trust_score, 92.0)
        self.assertEqual(r.website_trust_classification, "LIKELY SAFE")
        self.assertEqual(r.ip_risk_score, 10.0)
        self.assertEqual(r.searched_by, "SecurityAuditor")

    # -------------------------------------------------------------------------
    # Scenario 7: Persist Field Study After Simulated Restart
    # -------------------------------------------------------------------------
    def test_persist_field_study_after_restart(self):
        """Simulate backend restart and confirm Field Study observations remain intact."""
        obs = self._sample_field_observation("kernel.org", "147.75.80.249", test_id=1)
        obs_id = self.repo.save_field_observation(obs)

        # Close and re-open repository
        self.repo.close()
        restarted_repo = SQLiteRepository(db_path=self.db_path)
        restarted_repo.init_schema()

        records = restarted_repo.get_field_observations()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].id, obs_id)
        self.assertEqual(records[0].domain, "kernel.org")
        self.assertEqual(records[0].website_trust_classification, "LIKELY SAFE")
        restarted_repo.close()

    # -------------------------------------------------------------------------
    # Scenario 8: Delete Individual Field Study Observation
    # -------------------------------------------------------------------------
    def test_delete_field_study_observation(self):
        """Verify deleting an individual Field Study observation by ID."""
        id1 = self.repo.save_field_observation(self._sample_field_observation("obs1.org", "1.1.1.1", test_id=1))
        id2 = self.repo.save_field_observation(self._sample_field_observation("obs2.org", "2.2.2.2", test_id=2))

        self.assertEqual(len(self.repo.get_field_observations()), 2)

        deleted = self.repo.delete_field_observation(id1)
        self.assertTrue(deleted)

        remaining = self.repo.get_field_observations()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].id, id2)
        self.assertEqual(remaining[0].domain, "obs2.org")

    # -------------------------------------------------------------------------
    # Scenario 9: Batch Deletion for History and Field Study
    # -------------------------------------------------------------------------
    def test_batch_deletion_history_and_field_study(self):
        """Verify batch deletion across multiple record IDs."""
        # History batch deletion
        h_ids = [
            self.repo.save_lookup(self._sample_lookup_result(f"site{i}.com", f"1.1.1.{i}"))
            for i in range(1, 6)
        ]
        self.assertEqual(len(self.repo.get_lookup_history()), 5)

        deleted_h_count = self.repo.delete_lookups_batch([h_ids[0], h_ids[2], h_ids[4]])
        self.assertEqual(deleted_h_count, 3)

        remaining_h = self.repo.get_lookup_history()
        self.assertEqual(len(remaining_h), 2)
        remaining_h_ids = {r.id for r in remaining_h}
        self.assertEqual(remaining_h_ids, {h_ids[1], h_ids[3]})

        # Field Study batch deletion
        fs_ids = [
            self.repo.save_field_observation(self._sample_field_observation(f"fs{i}.org", f"2.2.2.{i}", test_id=i))
            for i in range(1, 5)
        ]
        self.assertEqual(len(self.repo.get_field_observations()), 4)

        deleted_fs_count = self.repo.delete_field_observations_batch([fs_ids[1], fs_ids[2]])
        self.assertEqual(deleted_fs_count, 2)

        remaining_fs = self.repo.get_field_observations()
        self.assertEqual(len(remaining_fs), 2)
        remaining_fs_ids = {r.id for r in remaining_fs}
        self.assertEqual(remaining_fs_ids, {fs_ids[0], fs_ids[3]})

    # -------------------------------------------------------------------------
    # Scenario 10: Duplicate Detection (Field Study Enforces Uniqueness)
    # -------------------------------------------------------------------------
    def test_duplicate_detection_field_study_and_history(self):
        """Verify uniqueness enforcement in Field Study and multi-scan tracking in History."""
        # 1. Field study uniqueness
        obs1 = self._sample_field_observation("eff.org", "104.18.25.10", test_id=1)
        id1 = self.repo.save_field_observation(obs1)
        self.assertIsNotNone(id1)

        # Attempt to insert identical domain without update_if_exists
        obs_duplicate = self._sample_field_observation("eff.org", "104.18.25.10", test_id=2)
        id2 = self.repo.save_field_observation(obs_duplicate, update_if_exists=False)
        # Duplicate domain is rejected, returning None
        self.assertIsNone(id2)
        self.assertEqual(len(self.repo.get_field_observations()), 1)

        # When update_if_exists=True, it updates the existing observation and returns its ID
        id3 = self.repo.save_field_observation(obs_duplicate, update_if_exists=True)
        self.assertEqual(id3, id1)
        self.assertEqual(len(self.repo.get_field_observations()), 1)

        # 2. History allows multiple scans and tracks occurrences
        self.repo.save_lookup(self._sample_lookup_result("eff.org", "104.18.25.10"))
        self.repo.save_lookup(self._sample_lookup_result("eff.org", "104.18.25.10"))
        self.repo.save_lookup(self._sample_lookup_result("other.org", "8.8.8.8"))

        hist = self.repo.get_lookup_history()
        self.assertEqual(len(hist), 3)
        eff_scans = [r for r in hist if r.domain == "eff.org"]
        self.assertEqual(len(eff_scans), 2)

    # -------------------------------------------------------------------------
    # Scenario 11: Empty Database State
    # -------------------------------------------------------------------------
    def test_empty_database_state_returns_zero_records(self):
        """Verify that a brand new empty database returns 0 records and does not crash."""
        history = self.repo.get_lookup_history()
        self.assertEqual(history, [])

        observations = self.repo.get_field_observations()
        self.assertEqual(observations, [])

        status = self.repo.get_health_status()
        self.assertTrue(status["connected"])
        self.assertEqual(status["type"], "sqlite")

        # Analytics computation on empty state returns valid zero-structures without error
        analytics = compute_field_study_analytics(db_path=str(self.db_path))
        self.assertTrue(analytics["success"])
        self.assertTrue(analytics["insufficient_data"])
        self.assertEqual(analytics["overview"]["total_observations"], 0)
        self.assertEqual(analytics["overview"]["valid_observations"], 0)
        self.assertIsNone(analytics["overview"]["avg_trust_score"])
        self.assertIsNone(analytics["overview"]["avg_risk_score"])
        self.assertEqual(analytics["map_points"], [])

    # -------------------------------------------------------------------------
    # Scenario 12: Database Failure and Error Handling
    # -------------------------------------------------------------------------
    def test_database_error_handling(self):
        """Verify graceful error handling for invalid operations or corrupt connections."""
        # Deleting non-existent ID should return False safely without raising exceptions
        result = self.repo.delete_lookup(999999)
        self.assertFalse(result)

        fs_result = self.repo.delete_field_observation(999999)
        self.assertFalse(fs_result)

        batch_result = self.repo.delete_lookups_batch([])
        self.assertEqual(batch_result, 0)

        # Querying non-existent observation returns None
        lookup_none = self.repo.get_field_observation_by_domain("non-existent-domain.xyz")
        self.assertIsNone(lookup_none)

    # -------------------------------------------------------------------------
    # Scenario 13: Analytics Computation from Real Persisted Records
    # -------------------------------------------------------------------------
    def test_analytics_computation_from_real_records(self):
        """Verify research metrics (mean trust, risk, HTTPS) are calculated from real records."""
        # Save 3 real observations with controlled values
        obs1 = self._sample_field_observation("site1.com", "1.1.1.1", test_id=1)
        obs1.website_trust_score = 90.0
        obs1.ip_risk_score = 10.0
        obs1.https_status = "Enabled"
        self.repo.save_field_observation(obs1)

        obs2 = self._sample_field_observation("site2.com", "2.2.2.2", test_id=2)
        obs2.website_trust_score = 70.0
        obs2.ip_risk_score = 30.0
        obs2.https_status = "Enabled"
        self.repo.save_field_observation(obs2)

        obs3 = self._sample_field_observation("site3.com", "3.3.3.3", test_id=3)
        obs3.website_trust_score = 50.0
        obs3.ip_risk_score = 50.0
        obs3.https_status = "Disabled"
        self.repo.save_field_observation(obs3)

        analytics = compute_field_study_analytics(db_path=str(self.db_path))
        self.assertTrue(analytics["success"])
        self.assertEqual(analytics["overview"]["total_observations"], 3)
        self.assertEqual(analytics["overview"]["valid_observations"], 3)

        # Expected Mean Trust: (90 + 70 + 50) / 3 = 70.0
        self.assertAlmostEqual(analytics["overview"]["mean_trust_score"], 70.0, places=1)

        # Expected Mean Risk: (10 + 30 + 50) / 3 = 30.0
        self.assertAlmostEqual(analytics["overview"]["mean_risk_score"], 30.0, places=1)

        # Expected HTTPS adoption: 2 / 3 * 100 = 66.7%
        self.assertAlmostEqual(analytics["overview"]["https_adoption_pct"], 66.7, places=1)

        # Verify map points match
        self.assertEqual(len(analytics["map_points"]), 3)


if __name__ == "__main__":
    unittest.main()
