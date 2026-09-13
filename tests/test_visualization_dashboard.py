"""
test_visualization_dashboard.py
Unit and regression test suite for Phase 24: Advanced Visualization & Research Dashboard.
Validates filter extraction, in-memory cohort filtering, geographic coordinate extraction,
mathematical consistency with Phase 20 analytics, and data state handling.
"""

import pytest
from services.analytics_service import (
    apply_observation_filters,
    extract_map_coordinates_for_analytics,
    extract_filter_options,
    compute_field_study_analytics,
)


@pytest.fixture
def sample_field_study_records():
    """Provides a realistic heterogeneous set of 6 field study records for filtering."""
    return [
        {
            "id": 1,
            "domain": "google.com",
            "resolved_ip": "142.250.190.46",
            "country": "United States",
            "country_code": "US",
            "city": "Mountain View",
            "latitude": 37.422,
            "longitude": -122.084,
            "asn": "AS15169",
            "organization": "Google LLC",
            "infrastructure": "Cloud / Datacenter",
            "is_vpn": 0,
            "is_proxy": 0,
            "is_tor": 0,
            "trust_score": 85.0,
            "trust_class": "Highly Trusted",
            "risk_score": 10.0,
            "risk_class": "Minimal Risk",
            "https_enabled": 1,
            "http_redirects_to_https": 1,
            "tls_valid": 1,
            "ip_version": "IPv4",
            "created_at": "2026-03-01T10:00:00Z",
        },
        {
            "id": 2,
            "domain": "github.com",
            "resolved_ip": "140.82.121.4",
            "country": "United States",
            "country_code": "US",
            "city": "San Francisco",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "asn": "AS36459",
            "organization": "GitHub, Inc.",
            "infrastructure": "Cloud / Datacenter",
            "is_vpn": 0,
            "is_proxy": 0,
            "is_tor": 0,
            "trust_score": 90.0,
            "trust_class": "Highly Trusted",
            "risk_score": 8.0,
            "risk_class": "Minimal Risk",
            "https_enabled": 1,
            "http_redirects_to_https": 1,
            "tls_valid": 1,
            "ip_version": "IPv4",
            "created_at": "2026-03-02T10:00:00Z",
        },
        {
            "id": 3,
            "domain": "ovh.net",
            "resolved_ip": "198.27.92.1",
            "country": "France",
            "country_code": "FR",
            "city": "Roubaix",
            "latitude": 50.6927,
            "longitude": 3.1778,
            "asn": "AS16276",
            "organization": "OVH SAS",
            "infrastructure": "Hosting / ISP",
            "is_vpn": 0,
            "is_proxy": 0,
            "is_tor": 0,
            "trust_score": 60.0,
            "trust_class": "Moderate Trust",
            "risk_score": 40.0,
            "risk_class": "Moderate Risk",
            "https_enabled": 0,
            "http_redirects_to_https": 0,
            "tls_valid": 0,
            "ip_version": "IPv4",
            "created_at": "2026-03-03T10:00:00Z",
        },
        {
            "id": 4,
            "domain": "berlin.de",
            "resolved_ip": "2001:db8::1",
            "country": "Germany",
            "country_code": "DE",
            "city": "Berlin",
            "latitude": 52.52,
            "longitude": 13.405,
            "asn": "AS3320",
            "organization": "Deutsche Telekom",
            "infrastructure": "Traditional / Enterprise",
            "is_vpn": 0,
            "is_proxy": 0,
            "is_tor": 0,
            "trust_score": 75.0,
            "trust_class": "Trusted",
            "risk_score": 25.0,
            "risk_class": "Low Risk",
            "https_enabled": 1,
            "http_redirects_to_https": 1,
            "tls_valid": 1,
            "ip_version": "IPv6",
            "created_at": "2026-03-04T10:00:00Z",
        },
        {
            "id": 5,
            "domain": "tor-exit-test.org",
            "resolved_ip": "185.220.101.5",
            "country": "Germany",
            "country_code": "DE",
            "city": "Frankfurt",
            "latitude": 50.1109,
            "longitude": 8.6821,
            "asn": "AS200651",
            "organization": "Flokinet Ltd",
            "infrastructure": "Cloud / Datacenter",
            "is_vpn": 0,
            "is_proxy": 1,
            "is_tor": 1,
            "trust_score": 20.0,
            "trust_class": "Untrusted",
            "risk_score": 85.0,
            "risk_class": "High Risk",
            "https_enabled": None,  # Unknown HTTPS
            "http_redirects_to_https": 0,
            "tls_valid": None,
            "ip_version": "IPv4",
            "created_at": "2026-03-05T10:00:00Z",
        },
        {
            "id": 6,
            "domain": "no-coords-site.org",
            "resolved_ip": "192.0.2.1",
            "country": "Unknown",
            "country_code": "",
            "city": "",
            "latitude": None,
            "longitude": None,
            "asn": None,
            "organization": None,
            "infrastructure": "Unknown",
            "is_vpn": 0,
            "is_proxy": 0,
            "is_tor": 0,
            "trust_score": None,
            "trust_class": "Untrusted",
            "risk_score": None,
            "risk_class": "Unknown",
            "https_enabled": 0,
            "http_redirects_to_https": 0,
            "tls_valid": 0,
            "ip_version": "IPv4",
            "created_at": "2026-03-06T10:00:00Z",
        },
    ]


class TestObservationFilters:
    """Tests for in-memory cohort filtering via apply_observation_filters."""

    def test_filter_by_country(self, sample_field_study_records):
        filtered, is_filtered, summary = apply_observation_filters(sample_field_study_records, {"country": "United States"})
        assert len(filtered) == 2
        assert is_filtered is True
        assert all(r["country"] == "United States" for r in filtered)
        assert summary.get("country") == "United States"

    def test_filter_by_country_case_insensitive(self, sample_field_study_records):
        filtered, is_filtered, _ = apply_observation_filters(sample_field_study_records, {"country": "germany"})
        assert len(filtered) == 2
        assert is_filtered is True
        assert all(r["country"] == "Germany" for r in filtered)

    def test_filter_by_infrastructure(self, sample_field_study_records):
        filtered, is_filtered, summary = apply_observation_filters(sample_field_study_records, {"infrastructure": "Cloud / Datacenter"})
        assert len(filtered) == 3
        assert is_filtered is True
        assert "infrastructure" in summary

    def test_filter_by_trust_class(self, sample_field_study_records):
        filtered, is_filtered, _ = apply_observation_filters(sample_field_study_records, {"trust_class": "Highly Trusted"})
        assert len(filtered) == 2
        assert is_filtered is True
        assert set(r["domain"] for r in filtered) == {"google.com", "github.com"}

    def test_filter_by_risk_class(self, sample_field_study_records):
        filtered, is_filtered, _ = apply_observation_filters(sample_field_study_records, {"risk_class": "High Risk"})
        assert len(filtered) == 1
        assert is_filtered is True
        assert filtered[0]["domain"] == "tor-exit-test.org"

    def test_filter_by_https_status_enabled(self, sample_field_study_records):
        filtered, is_filtered, _ = apply_observation_filters(sample_field_study_records, {"https_status": "Enabled"})
        assert len(filtered) == 3
        assert is_filtered is True
        assert all(r["https_enabled"] == 1 for r in filtered)

    def test_filter_by_https_status_disabled(self, sample_field_study_records):
        filtered, is_filtered, _ = apply_observation_filters(sample_field_study_records, {"https_status": "Disabled"})
        assert len(filtered) == 2
        assert is_filtered is True
        assert set(r["domain"] for r in filtered) == {"ovh.net", "no-coords-site.org"}

    def test_filter_by_https_status_unknown(self, sample_field_study_records):
        filtered, is_filtered, _ = apply_observation_filters(sample_field_study_records, {"https_status": "Unknown"})
        assert len(filtered) == 1
        assert is_filtered is True
        assert filtered[0]["domain"] == "tor-exit-test.org"

    def test_filter_by_ip_version_ipv6(self, sample_field_study_records):
        filtered, is_filtered, _ = apply_observation_filters(sample_field_study_records, {"ip_version": "IPv6"})
        assert len(filtered) == 1
        assert is_filtered is True
        assert filtered[0]["domain"] == "berlin.de"

    def test_filter_by_range_recent(self, sample_field_study_records):
        filtered, is_filtered, _ = apply_observation_filters(sample_field_study_records, {"range": "recent_10"})
        assert len(filtered) == 6
        assert is_filtered is True

    def test_filter_by_range_first_25(self, sample_field_study_records):
        filtered, is_filtered, _ = apply_observation_filters(sample_field_study_records, {"range": "first_25"})
        assert len(filtered) == 6
        assert is_filtered is True
        assert filtered[0]["id"] == 1

    def test_multi_filter_combination(self, sample_field_study_records):
        filtered, is_filtered, summary = apply_observation_filters(
            sample_field_study_records,
            {"country": "Germany", "risk_class": "High Risk"}
        )
        assert len(filtered) == 1
        assert is_filtered is True
        assert filtered[0]["domain"] == "tor-exit-test.org"
        assert summary.get("country") == "Germany"
        assert summary.get("risk_class") == "High Risk"

    def test_filter_yielding_zero_records(self, sample_field_study_records):
        filtered, is_filtered, summary = apply_observation_filters(sample_field_study_records, {"country": "NonExistentCountry"})
        assert len(filtered) == 0
        assert is_filtered is True
        assert summary.get("country") == "NonExistentCountry"


class TestMapCoordinatesExtraction:
    """Tests for extract_map_coordinates_for_analytics."""

    def test_valid_and_missing_coordinates(self, sample_field_study_records):
        points, mapped_count, missing_count = extract_map_coordinates_for_analytics(sample_field_study_records)
        # 5 records have valid coordinates, 1 (id:6) has None
        assert mapped_count == 5
        assert missing_count == 1
        assert len(points) == 5

        for pt in points:
            assert -90.0 <= pt["latitude"] <= 90.0
            assert -180.0 <= pt["longitude"] <= 180.0
            assert "domain" in pt
            assert "resolved_ip" in pt

    def test_out_of_range_coordinates_rejected(self):
        records = [
            {"domain": "bad1.com", "resolved_ip": "1.1.1.1", "latitude": 95.0, "longitude": 10.0},
            {"domain": "bad2.com", "resolved_ip": "2.2.2.2", "latitude": 10.0, "longitude": -190.0},
            {"domain": "good.com", "resolved_ip": "3.3.3.3", "latitude": 12.0, "longitude": 77.0},
        ]
        points, mapped, missing = extract_map_coordinates_for_analytics(records)
        assert mapped == 1
        assert missing == 2
        assert len(points) == 1
        assert points[0]["domain"] == "good.com"


class TestFilterOptionsExtraction:
    """Tests for extract_filter_options."""

    def test_extracts_distinct_sorted_values(self, sample_field_study_records):
        options = extract_filter_options(sample_field_study_records)
        assert "France" in options["countries"]
        assert "Germany" in options["countries"]
        assert "United States" in options["countries"]
        assert "Cloud / Datacenter" in options["infrastructures"]
        assert "Highly Trusted" in options["trust_classes"]
        assert "Minimal Risk" in options["risk_classes"]
        assert options["https_statuses"] == ["Enabled", "Disabled", "Unknown"]
        assert options["ip_versions"] == ["IPv4", "IPv6"]
        assert any(r["id"] == "recent_10" for r in options["ranges"])


class TestPhase20MathematicalEquivalence:
    """
    Validates that when no filters are applied, the dashboard analytics
    response is 100% mathematically consistent with Phase 20 analytics.
    """

    def test_unfiltered_analytics_equals_phase_20(self, sample_field_study_records):
        analytics = compute_field_study_analytics(records=sample_field_study_records, filters=None)

        assert analytics["is_filtered"] is False
        assert analytics["unfiltered_total_count"] == 6
        assert analytics["filtered_count"] == 6
        assert analytics["overview"]["total_observations"] == 6

        # Check trust score calculations
        # Valid trust scores: 85, 90, 60, 75, 20 (5 valid scores)
        # Sum = 330, Mean = 66.0, Min = 20.0, Max = 90.0
        assert analytics["trust_analysis"]["mean"] == 66.0
        assert analytics["trust_analysis"]["min"] == 20.0
        assert analytics["trust_analysis"]["max"] == 90.0

        # Check risk score calculations
        # Valid risk scores: 10, 8, 40, 25, 85 (5 valid scores)
        # Sum = 168, Mean = 33.6, Min = 8.0, Max = 85.0
        assert analytics["risk_analysis"]["mean"] == 33.6
        assert analytics["risk_analysis"]["min"] == 8.0
        assert analytics["risk_analysis"]["max"] == 85.0

        # Map points embedded
        assert analytics["mapped_points_count"] == 5
        assert analytics["missing_coordinates_count"] == 1
        assert len(analytics["map_points"]) == 5

        # Available filter options embedded
        assert "available_filter_options" in analytics
        assert len(analytics["available_filter_options"]["countries"]) >= 3


class TestFilteredAnalyticsResponse:
    """Tests for compute_field_study_analytics with active filters."""

    def test_filtered_by_country_analytics(self, sample_field_study_records):
        analytics = compute_field_study_analytics(
            records=sample_field_study_records,
            filters={"country": "United States"}
        )

        assert analytics["is_filtered"] is True
        assert analytics["unfiltered_total_count"] == 6
        assert analytics["filtered_count"] == 2
        assert analytics["overview"]["total_observations"] == 2
        assert analytics["trust_analysis"]["mean"] == 87.5  # (85 + 90) / 2
        assert analytics["risk_analysis"]["mean"] == 9.0    # (10 + 8) / 2
        assert analytics["mapped_points_count"] == 2
        assert analytics["missing_coordinates_count"] == 0

    def test_filtered_zero_matches_analytics(self, sample_field_study_records):
        analytics = compute_field_study_analytics(
            records=sample_field_study_records,
            filters={"country": "Antarctica"}
        )

        assert analytics["is_filtered"] is True
        assert analytics["unfiltered_total_count"] == 6
        assert analytics["filtered_count"] == 0
        assert analytics["overview"]["total_observations"] == 0
        assert analytics["mapped_points_count"] == 0
        assert analytics["missing_coordinates_count"] == 0
        assert len(analytics["map_points"]) == 0
        assert analytics["insufficient_data"] is True


class TestEmptyDatasetHandling:
    """Tests empty database response structure."""

    def test_empty_records_response(self):
        analytics = compute_field_study_analytics(records=[], filters=None)
        assert analytics["overview"]["total_observations"] == 0
        assert analytics["is_filtered"] is False
        assert analytics["unfiltered_total_count"] == 0
        assert analytics["filtered_count"] == 0
        assert analytics["mapped_points_count"] == 0
        assert analytics["missing_coordinates_count"] == 0
        assert analytics["available_filter_options"]["countries"] == []
