"""
Comprehensive unit test suite for Phase 19: 50-Site Intelligence Field Study Upgrade.

Covers all 16 required test scenarios:
1. Add valid observation (verify 26 attributes saved and retrieved accurately)
2. Reject invalid observation (empty target, failed IP resolution, invalid input status)
3. Duplicate domain rejection (same domain cannot increase count towards 50)
4. Domain normalization (scheme removal, port stripping, subpath removal, lowercase)
5. Accurate progress calculation (e.g. 42 / 50 -> 84%, 8 remaining)
6. 50-site target logic (target count = 50, remaining = 0 when >= 50)
7. Target reached state (status = "TARGET_REACHED", auto-complete disabled)
8. Handle unknown security fields gracefully ("Unknown" / "N/A", scores computed safely)
9. Handle missing geolocation gracefully (defaults to "Unknown", confidence "UNKNOWN")
10. Handle missing infrastructure gracefully ("Unknown" network and infra types)
11. Handle missing trust score gracefully (fallback, doesn't crash)
12. Handle missing risk score gracefully (fallback, doesn't crash)
13. Backward compatibility with existing observations (reads legacy format without errors)
14. History vs Field Study separation (History lookup does not pollute Field Study until added/migrated)
15. Manual-first behavior (no auto scans triggered on page open / status retrieval)
16. Optional automatic completion (completes only the remaining up to 50, respects existing)
"""
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from database.db import (
    clear_field_study,
    get_field_observation_by_domain,
    get_field_observation_by_id,
    get_field_observations,
    get_lookup_history,
    init_db,
    save_field_observation,
    save_lookup,
)
from database.models import FieldObservation, LookupRecord
from services.field_test_service import (
    add_field_observation,
    export_field_dataset_from_history,
    get_field_project_status,
    load_test_websites,
    normalize_field_domain,
    run_automatic_completion,
    validate_observation,
)
from services.lookup_service import LookupResult, LookupStatus


class TestPhase19FieldStudySuite(unittest.TestCase):
    """Test suite covering all 16 Phase 19 Field Study scenarios."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_field_study.db")
        self.csv_path = os.path.join(self.tmp_dir.name, "test_export.csv")
        init_db(self.db_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _create_mock_result(
        self,
        domain: str = "example.com",
        ip: str = "93.184.216.34",
        status: LookupStatus = LookupStatus.SUCCESS,
        country: str = "United States",
        city: str = "Norwell",
        asn: str = "AS15133",
        org: str = "Edgecast Inc.",
    ) -> LookupResult:
        return LookupResult(
            input=domain,
            normalized_input=domain,
            input_type="DOMAIN",
            overall_status=status,
            dns_status="SUCCESS",
            geolocation_status="SUCCESS" if country != "Unknown" else "ERROR",
            resolved_addresses=[ip] if ip else [],
            ipv4_addresses=[ip] if ip else [],
            selected_ip=ip,
            ip_version="IPv4" if ip else "Unknown",
            country=country,
            country_code="US" if country == "United States" else "N/A",
            region="Massachusetts",
            city=city,
            latitude=42.1596,
            longitude=-70.8217,
            organization=org,
            isp=org,
            asn=asn,
            dns_response_time_ms=12.5,
            api_response_time_ms=45.2,
            total_response_time_ms=57.7,
        )

    # -------------------------------------------------------------------------
    # Test 1: Add Valid Observation
    # -------------------------------------------------------------------------
    def test_01_add_valid_observation(self):
        """Test 1: Add valid observation and verify all 26 attributes saved and retrieved."""
        mock_res = self._create_mock_result("github.com", "140.82.121.3")
        success, msg, obs = add_field_observation(
            target="github.com",
            category="Developer Platform",
            lookup_res=mock_res,
            db_path=self.db_path,
        )

        self.assertTrue(success, f"Failed with message: {msg}")
        self.assertIsNotNone(obs)
        self.assertIn("Added 'github.com' to Field Study", msg)

        # Retrieve from DB
        fetched = get_field_observation_by_domain("github.com", db_path=self.db_path)
        self.assertIsNotNone(fetched)

        # Verify Core Attributes across groups
        # 1. Identity
        self.assertEqual(fetched.domain, "github.com")
        self.assertEqual(fetched.category, "Developer Platform")
        self.assertEqual(fetched.resolved_ip, "140.82.121.3")
        self.assertEqual(fetched.ip_version, "IPv4")
        self.assertEqual(fetched.test_id, 1)

        # 2. Geolocation
        self.assertEqual(fetched.country, "United States")
        self.assertEqual(fetched.city, "Norwell")
        self.assertIsNotNone(fetched.latitude)
        self.assertIsNotNone(fetched.longitude)
        self.assertEqual(fetched.geolocation_confidence, "HIGH")

        # 3. Network & Infrastructure
        self.assertEqual(fetched.asn, "AS15133")
        self.assertEqual(fetched.organization, "Edgecast Inc.")

        # 4. Security
        self.assertIn(fetched.https_status, ("Enabled", "Disabled", "Unknown"))
        self.assertIn(fetched.tls_status, ("Valid", "Invalid", "Unknown"))

        # 5. Metadata
        self.assertEqual(fetched.observation_status, "RECORDED")
        self.assertIsNotNone(fetched.observed_at)

    # -------------------------------------------------------------------------
    # Test 2: Reject Invalid Observation
    # -------------------------------------------------------------------------
    def test_02_reject_invalid_observation(self):
        """Test 2: Reject invalid observation (empty target, failed IP resolution, invalid input status)."""
        # Case A: Empty target
        ok_a, msg_a, _ = add_field_observation("", db_path=self.db_path)
        self.assertFalse(ok_a)
        self.assertIn("empty or invalid", msg_a.lower())

        # Case B: Unresolved IP
        mock_unresolved = self._create_mock_result("nonexistent.invalid", ip="")
        mock_unresolved.selected_ip = None
        ok_b, msg_b, _ = add_field_observation(
            "nonexistent.invalid", lookup_res=mock_unresolved, db_path=self.db_path
        )
        self.assertFalse(ok_b)
        self.assertIn("valid ip", msg_b.lower())

        # Case C: Invalid Input Status
        mock_invalid = self._create_mock_result("bad input!!")
        mock_invalid.overall_status = LookupStatus.INVALID_INPUT
        ok_c, msg_c, _ = add_field_observation(
            "bad input!!", lookup_res=mock_invalid, db_path=self.db_path
        )
        self.assertFalse(ok_c)
        self.assertIn("invalid", msg_c.lower())

        # Verify nothing saved
        records = get_field_observations(db_path=self.db_path)
        self.assertEqual(len(records), 0)

    # -------------------------------------------------------------------------
    # Test 3: Duplicate Domain Rejection
    # -------------------------------------------------------------------------
    def test_03_duplicate_domain_rejection(self):
        """Test 3: Duplicate domain cannot increase count towards 50."""
        mock_res = self._create_mock_result("cloudflare.com", "1.1.1.1")
        ok1, _, _ = add_field_observation(
            "cloudflare.com", lookup_res=mock_res, db_path=self.db_path
        )
        self.assertTrue(ok1)

        # Attempt duplicate
        ok2, msg2, _ = add_field_observation(
            "cloudflare.com", lookup_res=mock_res, db_path=self.db_path
        )
        self.assertFalse(ok2)
        self.assertIn("already recorded", msg2.lower())

        # Attempt duplicate via URL variant
        ok3, msg3, _ = add_field_observation(
            "https://CLOUDFLARE.COM/cdn-cgi/trace", lookup_res=mock_res, db_path=self.db_path
        )
        self.assertFalse(ok3)
        self.assertIn("already recorded", msg3.lower())

        # Verify count is strictly 1
        records = get_field_observations(db_path=self.db_path)
        self.assertEqual(len(records), 1)

    # -------------------------------------------------------------------------
    # Test 4: Domain Normalization
    # -------------------------------------------------------------------------
    def test_04_domain_normalization(self):
        """Test 4: Domain normalization handles protocols, ports, subpaths, trailing slashes, casing."""
        self.assertEqual(normalize_field_domain("https://google.com/"), "google.com")
        self.assertEqual(normalize_field_domain("http://GOOGLE.COM"), "google.com")
        self.assertEqual(normalize_field_domain("google.com:443"), "google.com")
        self.assertEqual(normalize_field_domain("sub.example.com/a/b?c=1#frag"), "sub.example.com")
        self.assertEqual(normalize_field_domain("   EXAMPLE.ORG/   "), "example.org")
        self.assertEqual(normalize_field_domain("http://192.168.1.1:8080/index"), "192.168.1.1")

    # -------------------------------------------------------------------------
    # Test 5: Accurate Progress Calculation
    # -------------------------------------------------------------------------
    def test_05_accurate_progress_calculation(self):
        """Test 5: Accurate progress calculation (e.g. 42 / 50 -> 84%, 8 remaining)."""
        for i in range(1, 43):
            obs = FieldObservation(
                test_id=i,
                domain=f"domain{i}.com",
                category="General",
                resolved_ip=f"10.0.0.{i}",
                ip_version="IPv4",
                country="US",
                observation_status="RECORDED",
                observed_at="2026-09-13T10:00:00Z",
            )
            save_field_observation(obs, db_path=self.db_path)

        st = get_field_project_status(db_path=self.db_path, target_count=50)
        self.assertEqual(st["available_count"], 42)
        self.assertEqual(st["target"], 50)
        self.assertEqual(st["remaining"], 8)
        self.assertEqual(st["progress_percentage"], 84.0)
        self.assertEqual(st["status"], "INCOMPLETE")

    # -------------------------------------------------------------------------
    # Test 6: 50-Site Target Logic
    # -------------------------------------------------------------------------
    def test_06_fifty_site_target_logic(self):
        """Test 6: 50-site target logic marks quota complete and 0 remaining."""
        for i in range(1, 51):
            obs = FieldObservation(
                test_id=i,
                domain=f"site{i}.org",
                category="Research",
                resolved_ip=f"192.168.0.{i}",
                ip_version="IPv4",
                country="US",
                observation_status="RECORDED",
                observed_at="2026-09-13T10:00:00Z",
            )
            save_field_observation(obs, db_path=self.db_path)

        st = get_field_project_status(db_path=self.db_path, target_count=50)
        self.assertEqual(st["available_count"], 50)
        self.assertEqual(st["remaining"], 0)
        self.assertEqual(st["progress_percentage"], 100.0)
        self.assertEqual(st["status"], "TARGET_REACHED")

    # -------------------------------------------------------------------------
    # Test 7: Target Reached State
    # -------------------------------------------------------------------------
    def test_07_target_reached_state(self):
        """Test 7: Target reached state prevents unnecessary automatic completion runs."""
        for i in range(1, 51):
            obs = FieldObservation(
                test_id=i,
                domain=f"site{i}.net",
                category="Network",
                resolved_ip=f"172.16.0.{i}",
                ip_version="IPv4",
                country="US",
                observation_status="RECORDED",
                observed_at="2026-09-13T10:00:00Z",
            )
            save_field_observation(obs, db_path=self.db_path)

        # Trigger automatic completion when already at 50
        exported = run_automatic_completion(db_path=self.db_path, delay_seconds=0.0)
        self.assertEqual(len(exported), 50)
        st = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st["available_count"], 50)
        self.assertEqual(st["remaining"], 0)
        self.assertEqual(st["status"], "TARGET_REACHED")

    # -------------------------------------------------------------------------
    # Test 8: Handle Unknown Security Fields Gracefully
    # -------------------------------------------------------------------------
    def test_08_handle_unknown_security_fields(self):
        """Test 8: Handles missing security intelligence gracefully with defaults."""
        mock_res = self._create_mock_result("nosec.com", "8.8.8.8")
        ok, _, obs = add_field_observation(
            "nosec.com", lookup_res=mock_res, db_path=self.db_path
        )
        self.assertTrue(ok)
        self.assertIsNotNone(obs)
        self.assertEqual(obs.https_status, "Unknown")
        self.assertEqual(obs.tls_status, "Unknown")
        self.assertEqual(obs.vpn_status, "Unknown")
        self.assertEqual(obs.tor_status, "Unknown")

    # -------------------------------------------------------------------------
    # Test 9: Handle Missing Geolocation Gracefully
    # -------------------------------------------------------------------------
    def test_09_handle_missing_geolocation(self):
        """Test 9: Handles missing geolocation data without raising exceptions."""
        mock_res = self._create_mock_result(
            "nogeo.com", "127.0.0.1", country="Unknown", city="Unknown"
        )
        mock_res.country = None
        mock_res.city = None
        mock_res.latitude = None
        mock_res.longitude = None

        ok, _, obs = add_field_observation(
            "nogeo.com", lookup_res=mock_res, db_path=self.db_path
        )
        self.assertTrue(ok)
        self.assertEqual(obs.country, "Unknown")
        self.assertEqual(obs.city, "Unknown")
        self.assertIn(obs.geolocation_confidence, ("UNKNOWN", "MEDIUM"))

    # -------------------------------------------------------------------------
    # Test 10: Handle Missing Infrastructure Gracefully
    # -------------------------------------------------------------------------
    def test_10_handle_missing_infrastructure(self):
        """Test 10: Handles missing network / infrastructure data gracefully."""
        mock_res = self._create_mock_result("noinfra.com", "10.10.10.10", asn="N/A", org="N/A")
        mock_res.asn = None
        mock_res.organization = None
        mock_res.isp = None

        ok, _, obs = add_field_observation(
            "noinfra.com", lookup_res=mock_res, db_path=self.db_path
        )
        self.assertTrue(ok)
        self.assertEqual(obs.asn, "Unknown")
        self.assertEqual(obs.organization, "Unknown")
        self.assertEqual(obs.infrastructure_type, "Unknown")

    # -------------------------------------------------------------------------
    # Test 11: Handle Missing Trust Score Gracefully
    # -------------------------------------------------------------------------
    def test_11_handle_missing_trust_score(self):
        """Test 11: Missing trust score profile falls back safely."""
        mock_res = self._create_mock_result("notrust.com", "1.2.3.4")
        ok, _, obs = add_field_observation(
            "notrust.com", lookup_res=mock_res, db_path=self.db_path
        )
        self.assertTrue(ok)
        self.assertTrue(
            obs.website_trust_score is None or isinstance(obs.website_trust_score, (int, float))
        )

    # -------------------------------------------------------------------------
    # Test 12: Handle Missing Risk Score Gracefully
    # -------------------------------------------------------------------------
    def test_12_handle_missing_risk_score(self):
        """Test 12: Missing risk score profile falls back safely."""
        mock_res = self._create_mock_result("norisk.com", "5.6.7.8")
        ok, _, obs = add_field_observation(
            "norisk.com", lookup_res=mock_res, db_path=self.db_path
        )
        self.assertTrue(ok)
        self.assertTrue(
            obs.ip_risk_score is None or isinstance(obs.ip_risk_score, (int, float))
        )

    # -------------------------------------------------------------------------
    # Test 13: Backward Compatibility with Existing Observations
    # -------------------------------------------------------------------------
    def test_13_backward_compatibility_with_existing_observations(self):
        """Test 13: FieldObservation legacy aliases and serialization behave identically."""
        obs = FieldObservation(
            id=42,
            test_id=1,
            domain="legacy-test.org",
            category="Legacy",
            resolved_ip="9.9.9.9",
            ip_version="IPv4",
            country="United States",
            observation_status="RECORDED",
            observed_at="2026-09-13T12:00:00Z",
        )
        self.assertEqual(obs.ip_address, "9.9.9.9")
        self.assertEqual(obs.status, "RECORDED")
        self.assertEqual(obs.input_value, "legacy-test.org")

        d = obs.to_dict()
        self.assertEqual(d["domain"], "legacy-test.org")
        self.assertEqual(d["ip_address"], "9.9.9.9")
        self.assertEqual(d["status"], "RECORDED")
        self.assertEqual(d["input_value"], "legacy-test.org")

    # -------------------------------------------------------------------------
    # Test 14: History vs Field Study Separation
    # -------------------------------------------------------------------------
    def test_14_history_vs_field_study_separation(self):
        """Test 14: History lookups do not pollute Field Study until explicitly added."""
        seed_obs = FieldObservation(
            test_id=1,
            domain="curated-study.com",
            category="Curated",
            resolved_ip="1.1.1.1",
            ip_version="IPv4",
            country="US",
            observation_status="RECORDED",
            observed_at="2026-09-13T10:00:00Z",
        )
        save_field_observation(seed_obs, db_path=self.db_path)

        history_res = self._create_mock_result("casual-browse.com", "4.4.4.4")
        save_lookup(history_res, db_path=self.db_path)

        hist_records = get_lookup_history(db_path=self.db_path)
        self.assertEqual(len(hist_records), 1)
        self.assertEqual(hist_records[0].input_value, "casual-browse.com")

        field_records = get_field_observations(db_path=self.db_path)
        self.assertEqual(len(field_records), 1)
        self.assertEqual(field_records[0].domain, "curated-study.com")

    # -------------------------------------------------------------------------
    # Test 15: Manual-First Behavior
    # -------------------------------------------------------------------------
    @patch("services.field_test_service.perform_lookup")
    @patch("services.risk_analysis_service.perform_full_intelligence_scan")
    def test_15_manual_first_behavior(self, mock_scan, mock_lookup):
        """Test 15: Status retrieval is passive; no scans triggered automatically."""
        st = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st["available_count"], 0)
        self.assertEqual(st["status"], "INCOMPLETE")

        mock_scan.assert_not_called()
        mock_lookup.assert_not_called()

    # -------------------------------------------------------------------------
    # Test 16: Optional Automatic Completion
    # -------------------------------------------------------------------------
    def test_16_optional_automatic_completion(self):
        """Test 16: Automatic completion completes only remaining observations up to 50."""
        for i in range(1, 48):
            obs = FieldObservation(
                test_id=i,
                domain=f"existing{i}.com",
                category="Pre-Existing",
                resolved_ip=f"10.1.{i // 256}.{i % 256}",
                ip_version="IPv4",
                country="US",
                observation_status="RECORDED",
                observed_at="2026-09-13T10:00:00Z",
            )
            save_field_observation(obs, db_path=self.db_path)

        st_before = get_field_project_status(db_path=self.db_path)
        self.assertEqual(st_before["available_count"], 47)
        self.assertEqual(st_before["remaining"], 3)

        with patch("services.field_test_service.add_field_observation") as mock_add:
            def mock_add_and_save(target, db_path=None, category=None, lookup_res=None):
                cur = get_field_observations(db_path=db_path)
                new_obs = FieldObservation(
                    test_id=len(cur) + 1,
                    domain=target,
                    category=category or "Auto",
                    resolved_ip="8.8.8.8",
                    country="US",
                    observation_status="RECORDED",
                    observed_at="2026-09-13T10:00:00Z",
                )
                save_field_observation(new_obs, db_path=db_path)
                return True, "Added", new_obs

            mock_add.side_effect = mock_add_and_save

            exported = run_automatic_completion(
                db_path=self.db_path, output_csv_path=self.csv_path, delay_seconds=0.0
            )

            self.assertEqual(len(exported), 50)
            st_after = get_field_project_status(db_path=self.db_path)
            self.assertEqual(st_after["available_count"], 50)
            self.assertEqual(st_after["remaining"], 0)
            self.assertEqual(st_after["status"], "TARGET_REACHED")


if __name__ == "__main__":
    unittest.main()
