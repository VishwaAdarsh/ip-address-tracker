"""
Unit and Integration Tests for Phase 23 Intelligence Comparison & Investigation Workspace.

Validates:
- Multi-observation side-by-side normalization (FieldObservation, LookupRecord, Raw Dict)
- Observation limits enforcement (min 2, max 5)
- Duplicate domain selection rejection
- Deterministic statistics calculation (extremes, commonalities, HTTPS adoption, anonymizers)
- Difference highlights generator (divergence/convergence detection, factual reporting)
- Coordinate extraction and validation for Leaflet mapping
- Read-only candidate query (zero DB mutations)
- Comparative AI explanation generation and claim sanitization
"""
import pytest
from unittest.mock import patch

from database.models import FieldObservation, LookupRecord
from services.comparison_service import (
    MIN_COMPARISON_ITEMS,
    MAX_COMPARISON_ITEMS,
    NormalizedComparisonItem,
    compute_comparison_statistics,
    compute_difference_highlights,
    execute_comparison,
    extract_map_coordinates,
    generate_comparison_ai_explanation,
    get_comparison_candidates,
    normalize_comparison_item,
)


@pytest.fixture
def sample_field_obs_1():
    return FieldObservation(
        id=1,
        test_id=1,
        domain="alpha.example.com",
        resolved_ip="1.1.1.1",
        ip_version="IPv4",
        country="United States",
        region="California",
        city="San Jose",
        latitude=37.3382,
        longitude=-121.8863,
        geolocation_confidence="High",
        asn="AS13335",
        organization="Cloudflare, Inc.",
        isp="Cloudflare",
        network_type="CDN / Anycast",
        infrastructure_type="Cloud / Hosting",
        https_status="Enabled",
        tls_status="Valid",
        vpn_status="NOT_DETECTED",
        proxy_status="NOT_DETECTED",
        tor_status="NOT_DETECTED",
        website_trust_score=92.0,
        website_trust_classification="High Trust",
        ip_risk_score=15.0,
        ip_risk_classification="Low Risk",
        score_confidence="High",
        evidence_coverage=0.95,
        observed_at="2026-09-14T00:00:00Z",
    )


@pytest.fixture
def sample_field_obs_2():
    return FieldObservation(
        id=2,
        test_id=2,
        domain="beta.example.com",
        resolved_ip="8.8.8.8",
        ip_version="IPv4",
        country="United States",
        region="Virginia",
        city="Ashburn",
        latitude=39.0438,
        longitude=-77.4874,
        geolocation_confidence="High",
        asn="AS15169",
        organization="Google LLC",
        isp="Google",
        network_type="Anycast",
        infrastructure_type="Cloud / Hosting",
        https_status="Enabled",
        tls_status="Valid",
        vpn_status="NOT_DETECTED",
        proxy_status="NOT_DETECTED",
        tor_status="NOT_DETECTED",
        website_trust_score=88.0,
        website_trust_classification="High Trust",
        ip_risk_score=20.0,
        ip_risk_classification="Low Risk",
        score_confidence="High",
        evidence_coverage=0.90,
        observed_at="2026-09-14T00:01:00Z",
    )


@pytest.fixture
def sample_field_obs_3():
    return FieldObservation(
        id=3,
        test_id=3,
        domain="gamma.unencrypted.org",
        resolved_ip="192.0.2.1",
        ip_version="IPv4",
        country="Germany",
        region="Hesse",
        city="Frankfurt",
        latitude=50.1109,
        longitude=8.6821,
        geolocation_confidence="Medium",
        asn="AS24940",
        organization="Hetzner Online GmbH",
        isp="Hetzner",
        network_type="Datacenter",
        infrastructure_type="Dedicated Server",
        https_status="Disabled",
        tls_status="Invalid / Expired",
        vpn_status="DETECTED",
        proxy_status="NOT_DETECTED",
        tor_status="NOT_DETECTED",
        website_trust_score=35.0,
        website_trust_classification="Low Trust",
        ip_risk_score=75.0,
        ip_risk_classification="High Risk",
        score_confidence="Medium",
        evidence_coverage=0.70,
        observed_at="2026-09-14T00:02:00Z",
    )


class TestNormalization:
    """Test normalization of various observation formats."""

    def test_normalize_field_observation(self, sample_field_obs_1):
        item = normalize_comparison_item(sample_field_obs_1)
        assert isinstance(item, NormalizedComparisonItem)
        assert item.domain == "alpha.example.com"
        assert item.resolved_ip == "1.1.1.1"
        assert item.asn == "AS13335"
        assert item.country == "United States"
        assert item.https_status == "Enabled"
        assert item.tls_status == "Valid"
        assert item.website_trust_score == 92.0
        assert item.ip_risk_score == 15.0
        assert item.source == "field_study"

    def test_normalize_lookup_record(self):
        record = LookupRecord(
            id=10,
            ip_address="93.184.216.34",
            input_value="example.net",
            domain="example.net",
            country="United States",
            region="California",
            city="Los Angeles",
            latitude=34.0522,
            longitude=-118.2437,
            asn="AS15133",
            organization="EDGECAST",
            isp="Verizon",
            timestamp="2026-09-14T01:00:00Z",
        )
        item = normalize_comparison_item(record)
        assert item.domain == "example.net"
        assert item.resolved_ip == "93.184.216.34"
        assert item.country == "United States"
        assert item.source == "history"
        assert item.website_trust_score is None
        assert item.https_status == "UNKNOWN"

    def test_normalize_dict_payload(self):
        raw = {
            "target": "custom.org",
            "base": {
                "selected_ip": "198.51.100.2",
                "ip_version": "IPv4",
                "country": "Canada",
                "city": "Montreal",
                "latitude": 45.5017,
                "longitude": -73.5673,
                "asn": "AS54888",
                "organization": "OVH Hosting",
            },
            "security": {
                "is_https": True,
                "tls_valid": True,
                "tls_version": "TLS 1.3",
            },
            "risk": {
                "trust_score": 85.0,
                "risk_score": 22.0,
                "risk_category": "Good",
                "risk_level": "Low",
            },
            "ip_intel": {
                "vpn_status": "NOT_DETECTED",
                "proxy_status": "NOT_DETECTED",
                "tor_status": "NOT_DETECTED",
            },
        }
        item = normalize_comparison_item(raw)
        assert item.domain == "custom.org"
        assert item.resolved_ip == "198.51.100.2"
        assert item.country == "Canada"
        assert item.https_status == "Enabled"
        assert item.tls_status == "Valid"
        assert item.website_trust_score == 85.0
        assert item.ip_risk_score == 22.0


class TestComparisonExecutionValidation:
    """Test boundary conditions, input limits, and duplicate handling."""

    def test_reject_less_than_two_items(self, sample_field_obs_1):
        res = execute_comparison([sample_field_obs_1])
        assert res["success"] is False
        assert res["code"] == "INSUFFICIENT_OBSERVATIONS"
        assert "At least 2" in res["error"]

    def test_reject_more_than_five_items(self, sample_field_obs_1):
        items = [
            sample_field_obs_1,
            {"domain": "two.com"},
            {"domain": "three.com"},
            {"domain": "four.com"},
            {"domain": "five.com"},
            {"domain": "six.com"},
        ]
        res = execute_comparison(items)
        assert res["success"] is False
        assert res["code"] == "EXCEEDED_MAX_OBSERVATIONS"
        assert "maximum of 5" in res["error"]

    def test_reject_duplicate_domain(self, sample_field_obs_1):
        res = execute_comparison([sample_field_obs_1, sample_field_obs_1])
        assert res["success"] is False
        assert res["code"] == "DUPLICATE_SELECTION"
        assert "Duplicate observation detected" in res["error"]

    def test_reject_duplicate_domain_case_insensitive(self, sample_field_obs_1):
        item2 = {"domain": sample_field_obs_1.domain.upper()}
        res = execute_comparison([sample_field_obs_1, item2])
        assert res["success"] is False
        assert res["code"] == "DUPLICATE_SELECTION"

    def test_accept_valid_comparison(self, sample_field_obs_1, sample_field_obs_2):
        res = execute_comparison([sample_field_obs_1, sample_field_obs_2])
        assert res["success"] is True
        assert res["count"] == 2
        assert len(res["observations"]) == 2
        assert "statistics" in res
        assert "differences" in res
        assert "map_points" in res


class TestDeterministicStatistics:
    """Validate calculation of extreme scores, commonalities, and rates."""

    def test_extreme_scores_and_adoption(self, sample_field_obs_1, sample_field_obs_2, sample_field_obs_3):
        items = [
            normalize_comparison_item(sample_field_obs_1),
            normalize_comparison_item(sample_field_obs_2),
            normalize_comparison_item(sample_field_obs_3),
        ]
        stats = compute_comparison_statistics(items)
        assert stats["count"] == 3

        # Highest and lowest trust
        assert stats["highest_trust_score"]["domain"] == "alpha.example.com"
        assert stats["highest_trust_score"]["score"] == 92.0
        assert stats["lowest_trust_score"]["domain"] == "gamma.unencrypted.org"
        assert stats["lowest_trust_score"]["score"] == 35.0

        # Highest and lowest risk
        assert stats["highest_ip_risk_score"]["domain"] == "gamma.unencrypted.org"
        assert stats["highest_ip_risk_score"]["score"] == 75.0
        assert stats["lowest_ip_risk_score"]["domain"] == "alpha.example.com"
        assert stats["lowest_ip_risk_score"]["score"] == 15.0

        # Commonalities: Country diverges (US vs Germany)
        assert stats["common_country"] == "No common value detected."

        # Commonalities: ASN diverges
        assert stats["common_asn"] == "No common value detected."

        # HTTPS adoption: 2 of 3 (66.7%)
        assert stats["https_adoption"]["enabled_count"] == 2
        assert stats["https_adoption"]["total_count"] == 3
        assert stats["https_adoption"]["percentage"] == 66.7

        # Anonymizers: 1 VPN detected
        assert stats["anonymizer_detections"]["vpn_count"] == 1
        assert stats["anonymizer_detections"]["total_anonymizers"] == 1

    def test_unanimous_commonality(self, sample_field_obs_1, sample_field_obs_2):
        items = [
            normalize_comparison_item(sample_field_obs_1),
            normalize_comparison_item(sample_field_obs_2),
        ]
        stats = compute_comparison_statistics(items)
        # Both are in United States
        assert stats["common_country"] == "United States"
        # Both are Cloud / Hosting
        assert stats["common_infrastructure_type"] == "Cloud / Hosting"
        # ASNs differ
        assert stats["common_asn"] == "No common value detected."
        # HTTPS is 100%
        assert stats["https_adoption"]["percentage"] == 100.0


class TestDifferenceHighlights:
    """Validate generation of factual non-speculative difference points."""

    def test_highlights_divergence(self, sample_field_obs_1, sample_field_obs_3):
        items = [
            normalize_comparison_item(sample_field_obs_1),
            normalize_comparison_item(sample_field_obs_3),
        ]
        diffs = compute_difference_highlights(items)
        assert len(diffs) > 0

        text = " ".join(diffs)
        # Should detect country divergence
        assert "Geographic divergence" in text
        # Should detect ASN divergence
        assert "Autonomous System divergence" in text
        # Should detect transport security divergence
        assert "Transport security divergence" in text
        # Should detect trust score spread (92 - 35 = 57 >= 30)
        assert "Website Trust Score divergence" in text
        # Should detect VPN presence
        assert "Commercial VPN presence" in text

    def test_highlights_convergence(self, sample_field_obs_1):
        # Create clone with different domain but same network & country
        clone = dict(sample_field_obs_1.to_dict())
        clone["domain"] = "clone.example.com"
        item1 = normalize_comparison_item(sample_field_obs_1)
        item2 = normalize_comparison_item(clone)
        diffs = compute_difference_highlights([item1, item2])
        text = " ".join(diffs)
        assert "Geographic convergence" in text
        assert "Autonomous System convergence" in text
        assert "Transport security convergence" in text


class TestCoordinateExtraction:
    """Validate coordinate extraction and bounding for Leaflet map."""

    def test_extract_valid_coordinates(self, sample_field_obs_1, sample_field_obs_2):
        items = [
            normalize_comparison_item(sample_field_obs_1),
            normalize_comparison_item(sample_field_obs_2),
        ]
        points = extract_map_coordinates(items)
        assert len(points) == 2
        assert points[0]["domain"] == "alpha.example.com"
        assert points[0]["latitude"] == 37.3382
        assert points[0]["longitude"] == -121.8863
        assert points[1]["domain"] == "beta.example.com"

    def test_filter_invalid_coordinates(self):
        item_no_coords = NormalizedComparisonItem(domain="no-coords.com", latitude=None, longitude=None)
        item_out_of_bounds = NormalizedComparisonItem(domain="bad-coords.com", latitude=95.0, longitude=200.0)
        points = extract_map_coordinates([item_no_coords, item_out_of_bounds])
        assert len(points) == 0


class TestComparativeAIExplanation:
    """Validate AI comparative synthesis and safety claims sanitization."""

    def test_ai_explanation_generation(self, sample_field_obs_1, sample_field_obs_2):
        comp = execute_comparison([sample_field_obs_1, sample_field_obs_2])
        ai_res = generate_comparison_ai_explanation(comp)

        assert ai_res["status"] == "success"
        assert len(ai_res["domains"]) == 2
        assert "summary" in ai_res
        assert "infrastructure_comparison" in ai_res
        assert "security_comparison" in ai_res
        assert "takeaway" in ai_res
        assert "limitations" in ai_res
        assert "authoritative" in ai_res["limitations"]

    def test_ai_explanation_rejects_insufficient_items(self):
        res = generate_comparison_ai_explanation({"observations": [{"domain": "one.com"}]})
        assert res["status"] == "error"
        assert "At least 2" in res["summary"]

    def test_claim_sanitization(self):
        from core.ai_explainer import sanitize_security_claims
        dirty = "This host is 100% safe and guaranteed secure, completely safe and definitely malicious."
        cleaned = sanitize_security_claims(dirty)
        assert "100% safe" not in cleaned
        assert "guaranteed secure" not in cleaned
        assert "completely safe" not in cleaned
        assert "definitely malicious" not in cleaned
