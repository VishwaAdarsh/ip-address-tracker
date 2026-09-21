"""
Unit Tests for Phase 21: Research Report & Data Export.

Verifies:
1. Pre-export data validation (clean datasets vs issues detected)
2. CSV export schema (38 columns, RFC 4180 compliance, explicit UNKNOWNs)
3. Structured JSON export structure (metadata, validation, observations, analytics)
4. Comprehensive 12-section Markdown research report generation
5. Publication-grade PDF report generation (magic bytes, layout, non-empty)
6. Empty dataset behavior (N=0)
7. Partial dataset behavior (1 <= N < 50)
8. Complete 50-site dataset behavior (N=50, TARGET_REACHED)
9. Preservation of UNKNOWN states (zero fabrication)
10. Analytics consistency between Phase 20 and Phase 21 exports
11. Artifact saving helper (data/exports directory containment)
"""
import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import pytest

from backend.database.db import init_db, save_field_observation
from backend.models.models import FieldObservation
from backend.analytics.analytics_service import compute_field_study_analytics
from backend.reports.export_service import (
    FIELD_STUDY_CSV_COLUMNS,
    export_field_study_csv,
    export_field_study_json,
    generate_research_report_markdown,
    generate_research_report_pdf,
    save_export_artifact,
    validate_field_study_dataset,
)


def _make_obs(
    test_id: int,
    domain: str,
    ip: str = "1.2.3.4",
    ip_version: str = "IPv4",
    country: str = "United States",
    asn: str = "AS13335",
    org: str = "Cloudflare, Inc.",
    infra: str = "Cloud / Datacenter",
    net_type: str = "Data Center",
    https: str = "Enabled",
    tls: str = "Valid",
    vpn: str = "Not Detected",
    proxy: str = "Not Detected",
    tor: str = "Not Detected",
    trust_score: float = 85.0,
    trust_class: str = "High Trust",
    risk_score: float = 20.0,
    risk_class: str = "Low Risk",
    status: str = "RECORDED",
    lat: float = 37.7749,
    lon: float = -122.4194,
    observed_at: str = None,
) -> FieldObservation:
    """Helper to construct a FieldObservation for testing."""
    return FieldObservation(
        id=None,
        test_id=test_id,
        domain=domain,
        category="Technology",
        resolved_ip=ip,
        ip_version=ip_version,
        country=country,
        region="California",
        city="San Francisco",
        latitude=lat,
        longitude=lon,
        geolocation_confidence="High",
        asn=asn,
        organization=org,
        isp=org,
        network_type=net_type,
        infrastructure_type=infra,
        https_status=https,
        tls_status=tls,
        vpn_status=vpn,
        proxy_status=proxy,
        tor_status=tor,
        website_trust_score=trust_score,
        website_trust_classification=trust_class,
        ip_risk_score=risk_score,
        ip_risk_classification=risk_class,
        score_confidence="High",
        evidence_coverage=90.0,
        observation_status=status,
        observed_at=observed_at or datetime.now(timezone.utc).isoformat(),
        raw_history_id=None,
        dns_response_time_ms=12.5,
        api_response_time_ms=45.0,
        error_message=None,
    )


def test_validate_field_study_dataset_clean(tmp_path: Path):
    """Clean dataset returns is_valid=True and 0 warnings."""
    db_file = tmp_path / "clean_val.db"
    init_db(db_file)

    for i in range(1, 6):
        obs = _make_obs(test_id=i, domain=f"clean-site{i}.org", ip=f"10.0.0.{i}")
        save_field_observation(obs, db_path=db_file)

    val = validate_field_study_dataset(db_path=db_file)

    assert val["is_valid"] is True
    assert val["total_records"] == 5
    assert val["issues_count"] == 0
    assert len(val["warnings"]) == 0
    assert val["details"]["duplicate_domains"] == []


def test_validate_field_study_dataset_with_issues():
    """Detects missing IPs, out-of-bounds scores, and coordinate violations."""
    records = [
        # Record 1: missing domain & invalid score
        _make_obs(test_id=1, domain="", trust_score=150.0),
        # Record 2: unresolved IP & invalid coordinates
        _make_obs(test_id=2, domain="bad-coords.com", ip="Unknown", lat=120.0, lon=-250.0),
        # Record 3: negative risk score
        _make_obs(test_id=3, domain="negative-risk.com", risk_score=-15.0),
        # Record 4 & 5: duplicate domain
        _make_obs(test_id=4, domain="duplicate.com"),
        _make_obs(test_id=5, domain="https://duplicate.com/"),
    ]

    val = validate_field_study_dataset(observations=records)

    assert val["is_valid"] is False
    assert val["issues_count"] > 0

    types = [w["type"] for w in val["warnings"]]
    assert "MISSING_DOMAIN" in types
    assert "UNRESOLVED_IP" in types
    assert "INVALID_SCORE_RANGE" in types
    assert "INVALID_COORDINATES" in types
    assert "DUPLICATE_DOMAIN" in types


def test_export_field_study_csv_schema(tmp_path: Path):
    """Verifies all 38 columns, headers, and explicit UNKNOWN formatting."""
    db_file = tmp_path / "csv_schema.db"
    init_db(db_file)

    obs1 = _make_obs(test_id=1, domain="test-site.org", ip="1.1.1.1", ip_version="IPv4")
    save_field_observation(obs1, db_path=db_file)

    csv_text = export_field_study_csv(db_path=db_file)
    reader = list(csv.reader(io.StringIO(csv_text)))

    assert len(reader) == 2  # 1 header + 1 data row
    header = reader[0]
    row = reader[1]

    assert len(header) == 38
    assert header == FIELD_STUDY_CSV_COLUMNS
    assert header[0] == "Observation ID"
    assert header[1] == "Domain"
    assert header[3] == "Resolved IP"
    assert header[4] == "IPv4"
    assert header[5] == "IPv6"
    assert header[28] == "Website Trust Score"
    assert header[30] == "IP Risk Score"
    assert header[34] == "IP Personality"
    assert header[35] == "Intelligence Chain"

    assert row[1] == "test-site.org"
    assert row[3] == "1.1.1.1"
    assert row[4] == "1.1.1.1"
    assert row[5] == "UNKNOWN"  # IPv6 should be UNKNOWN for IPv4 address
    assert row[21] == "UNKNOWN"  # HTTP redirect
    assert row[23] == "UNKNOWN"  # TLS Issuer
    assert row[27] == "UNKNOWN"  # TLS Days Remaining


def test_export_field_study_json_structure(tmp_path: Path):
    """Verifies metadata, validation summary, observation records, and Phase 20 analytics."""
    db_file = tmp_path / "json_struct.db"
    init_db(db_file)

    for i in range(1, 4):
        obs = _make_obs(test_id=i, domain=f"json-site{i}.com", ip=f"2.2.2.{i}")
        save_field_observation(obs, db_path=db_file)

    payload = export_field_study_json(db_path=db_file, target_count=50)

    assert payload["project"] == "IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform"
    assert payload["target_observations"] == 50
    assert payload["observations_collected"] == 3
    assert payload["remaining_to_target"] == 47
    assert payload["dataset_status"] == "INCOMPLETE"
    assert "validation_summary" in payload
    assert "analytics" in payload
    assert "observations" in payload

    assert len(payload["observations"]) == 3
    obs_first = payload["observations"][0]
    assert obs_first["observation_id"] == 1
    assert obs_first["domain"] == "json-site1.com"
    assert obs_first["normalized_domain"] == "json-site1.com"
    assert "geolocation" in obs_first
    assert "network" in obs_first
    assert "security" in obs_first
    assert "scoring" in obs_first
    assert "intelligence_chain" in obs_first

    # Security unknown fields
    assert obs_first["security"]["tls_issuer"] == "UNKNOWN"
    assert obs_first["security"]["http_to_https_redirect"] == "UNKNOWN"


def test_generate_research_report_markdown(tmp_path: Path):
    """Verifies all 12 required sections and non-speculative indicators."""
    db_file = tmp_path / "report_md.db"
    init_db(db_file)

    obs = _make_obs(test_id=1, domain="report-target.com", trust_score=92.0, risk_score=15.0)
    save_field_observation(obs, db_path=db_file)

    md = generate_research_report_markdown(db_path=db_file, target_count=50)

    # Verify all 12 key section headers exist
    assert "1. Executive Summary" in md
    assert "2. Research Objective" in md
    assert "3. Empirical Methodology & Data Collection" in md
    assert "4. Dataset Quota & Quality Summary" in md
    assert "5. Transport Security & Cryptographic Posture" in md
    assert "6. IP Intelligence & Protocol Analysis" in md
    assert "7. Explainable Website Trust & IP Risk Analysis" in md
    assert "8. Network Infrastructure & Topology Classification" in md
    assert "9. Geographic & Autonomous System (BGP) Distribution" in md
    assert "10. Key Deterministic Research Insights" in md
    assert "11. Methodological Limitations & Analytical Disclaimers" in md
    assert "12. Dataset Status & Integrity Attestation" in md

    # Verify ethical disclaimers
    assert "Analytical Indicators, Not Absolute Proof" in md
    assert "Explicit UNKNOWN Representation" in md


def test_generate_research_report_pdf(tmp_path: Path):
    """Verifies PDF byte generation, valid PDF magic header, and file persistence."""
    db_file = tmp_path / "report_pdf.db"
    init_db(db_file)

    obs = _make_obs(test_id=1, domain="pdf-target.org", trust_score=88.0, risk_score=20.0)
    save_field_observation(obs, db_path=db_file)

    pdf_file = tmp_path / "output_report.pdf"
    pdf_bytes = generate_research_report_pdf(db_path=db_file, output_path=pdf_file, target_count=50)

    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")
    assert pdf_file.exists()
    assert pdf_file.stat().st_size > 1000


def test_empty_dataset_exports(tmp_path: Path):
    """Empty database (N=0) produces valid exports without dividing by zero."""
    db_file = tmp_path / "empty_exports.db"
    init_db(db_file)

    csv_text = export_field_study_csv(db_path=db_file)
    reader = list(csv.reader(io.StringIO(csv_text)))
    assert len(reader) == 1  # Only header

    json_payload = export_field_study_json(db_path=db_file, target_count=50)
    assert json_payload["observations_collected"] == 0
    assert json_payload["remaining_to_target"] == 50
    assert json_payload["dataset_status"] == "INCOMPLETE"
    assert json_payload["observations"] == []
    assert json_payload["analytics"]["insufficient_data"] is True

    md_report = generate_research_report_markdown(db_path=db_file, target_count=50)
    assert "Total Observations Collected | **0**" in md_report
    assert "Deficit to Target Quota" in md_report

    pdf_bytes = generate_research_report_pdf(db_path=db_file, target_count=50)
    assert pdf_bytes.startswith(b"%PDF-")


def test_partial_dataset_exports(tmp_path: Path):
    """Partial dataset (e.g. N=7) accurately reflects quota progress."""
    db_file = tmp_path / "partial_exports.db"
    init_db(db_file)

    for i in range(1, 8):
        obs = _make_obs(test_id=i, domain=f"partial{i}.com", ip=f"192.168.0.{i}")
        save_field_observation(obs, db_path=db_file)

    json_payload = export_field_study_json(db_path=db_file, target_count=50)
    assert json_payload["observations_collected"] == 7
    assert json_payload["remaining_to_target"] == 43
    assert json_payload["dataset_status"] == "INCOMPLETE"


def test_target_50_dataset_exports(tmp_path: Path):
    """50-site dataset marks TARGET_REACHED and 0 remaining."""
    db_file = tmp_path / "target_50_exports.db"
    init_db(db_file)

    for i in range(1, 51):
        obs = _make_obs(test_id=i, domain=f"target-site-{i}.edu", ip=f"10.1.{i // 256}.{i % 256}")
        save_field_observation(obs, db_path=db_file)

    json_payload = export_field_study_json(db_path=db_file, target_count=50)
    assert json_payload["observations_collected"] == 50
    assert json_payload["remaining_to_target"] == 0
    assert json_payload["dataset_status"] == "TARGET_REACHED"

    md_report = generate_research_report_markdown(db_path=db_file, target_count=50)
    assert "TARGET REACHED (50/50)" in md_report


def test_unknown_values_preservation(tmp_path: Path):
    """Unmeasured or missing fields are strictly preserved as UNKNOWN."""
    db_file = tmp_path / "unknowns.db"
    init_db(db_file)

    obs = _make_obs(
        test_id=1,
        domain="unknown-host.org",
        https="Unknown",
        tls="Unknown",
        vpn="Unknown",
        proxy="Unknown",
        tor="Unknown",
        trust_score=None,
        risk_score=None,
        lat=None,
        lon=None,
    )
    save_field_observation(obs, db_path=db_file)

    csv_text = export_field_study_csv(db_path=db_file)
    reader = list(csv.reader(io.StringIO(csv_text)))
    row = reader[1]

    # Lat, Lon, Trust, Risk, HTTPS, TLS must all be 'UNKNOWN'
    assert row[9] == "UNKNOWN"   # Latitude
    assert row[10] == "UNKNOWN"  # Longitude
    assert row[17] == "UNKNOWN"  # VPN
    assert row[20] == "UNKNOWN"  # HTTPS
    assert row[22] == "UNKNOWN"  # TLS
    assert row[28] == "UNKNOWN"  # Trust Score
    assert row[30] == "UNKNOWN"  # Risk Score


def test_analytics_consistency_with_phase_20(tmp_path: Path):
    """Exported JSON analytics payload matches Phase 20 analytics exactly."""
    db_file = tmp_path / "consistency.db"
    init_db(db_file)

    for i in range(1, 6):
        obs = _make_obs(test_id=i, domain=f"consistent{i}.com", trust_score=80.0 + i, risk_score=20.0 + i)
        save_field_observation(obs, db_path=db_file)

    direct_analytics = compute_field_study_analytics(db_path=db_file, target_count=50)
    json_export = export_field_study_json(db_path=db_file, target_count=50)

    # Verify overview statistics match
    assert json_export["analytics"]["overview"]["total_observations"] == direct_analytics["overview"]["total_observations"]
    assert json_export["analytics"]["overview"]["mean_trust_score"] == direct_analytics["overview"]["mean_trust_score"]
    assert json_export["analytics"]["overview"]["mean_risk_score"] == direct_analytics["overview"]["mean_risk_score"]


def test_save_export_artifact(tmp_path: Path):
    """Verifies deterministic saving to destination directory."""
    test_exports_dir = tmp_path / "test_exports"

    # Text artifact
    txt_path = save_export_artifact("test_output.csv", "col1,col2\nval1,val2", exports_dir=test_exports_dir)
    assert txt_path.exists()
    assert txt_path.read_text(encoding="utf-8") == "col1,col2\nval1,val2"

    # Binary artifact
    bin_path = save_export_artifact("test_output.pdf", b"%PDF-1.4 sample bytes", exports_dir=test_exports_dir)
    assert bin_path.exists()
    assert bin_path.read_bytes() == b"%PDF-1.4 sample bytes"
