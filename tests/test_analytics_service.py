"""
Unit Tests for Phase 20: Advanced Field Study Analytics & Comparison.

Verifies:
1. Empty dataset handling (N=0, graceful None percentages, zero divide protection)
2. Partial dataset (N < 50, quota progress tracking, remaining count)
3. Target 50-site dataset (N=50, target reached, 100% progress)
4. Unknown and missing value segregation
5. Trust score univariate statistics & 5-bracket histogram
6. IP risk univariate statistics & 5-bracket histogram
7. HTTPS adoption and TLS validity percentages
8. IPv4 vs IPv6 protocol distribution
9. Cloud/Datacenter vs Traditional infrastructure classification
10. Threat detections (VPN, Proxy, Tor)
11. Comparison analytics (highest/lowest rankings & infrastructure comparison)
12. Deterministic research insights generation
"""
import pytest
from datetime import datetime, timezone
from pathlib import Path
from database.db import init_db, save_field_observation
from database.models import FieldObservation
from services.analytics_service import compute_field_study_analytics


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
    dns_time: float = 12.5,
    api_time: float = 45.0,
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
        latitude=37.7749,
        longitude=-122.4194,
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
        observed_at=datetime.now(timezone.utc).isoformat(),
        raw_history_id=None,
        dns_response_time_ms=dns_time,
        api_response_time_ms=api_time,
        error_message=None,
    )


def test_empty_dataset(tmp_path: Path):
    """N=0 must return insufficient_data=True and graceful None percentages."""
    db_file = tmp_path / "empty_test.db"
    init_db(db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)

    assert res["success"] is True
    assert res["insufficient_data"] is True
    assert res["overview"]["total_observations"] == 0
    assert res["overview"]["sample_target"] == 50
    assert res["overview"]["remaining_to_target"] == 50
    assert res["overview"]["target_reached"] is False
    assert res["overview"]["collection_progress_pct"] == 0.0
    assert res["overview"]["https_adoption_pct"] is None
    assert res["overview"]["mean_trust_score"] is None
    assert res["overview"]["mean_risk_score"] is None

    # Trust histogram should have 5 empty brackets
    assert len(res["trust_analysis"]["histogram"]) == 5
    for b in res["trust_analysis"]["histogram"]:
        assert b["count"] == 0
        assert b["pct"] == 0.0

    # Risk histogram should have 5 empty brackets
    assert len(res["risk_analysis"]["histogram"]) == 5
    for b in res["risk_analysis"]["histogram"]:
        assert b["count"] == 0
        assert b["pct"] == 0.0

    # Insights and comparisons should be empty lists
    assert res["research_insights"] == []
    assert res["comparison_analytics"]["highest_trust_sites"] == []
    assert res["comparison_analytics"]["highest_risk_sites"] == []


def test_partial_dataset(tmp_path: Path):
    """N < 50 partial dataset tracking quota progress accurately."""
    db_file = tmp_path / "partial_test.db"
    init_db(db_file)

    # Insert 10 observations
    for i in range(1, 11):
        obs = _make_obs(
            test_id=i,
            domain=f"site{i}.org",
            ip=f"10.0.0.{i}",
            trust_score=50.0 + (i * 3),
            risk_score=20.0 + (i * 2),
        )
        save_field_observation(obs, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)

    assert res["success"] is True
    assert res["insufficient_data"] is False
    assert res["overview"]["total_observations"] == 10
    assert res["overview"]["sample_target"] == 50
    assert res["overview"]["remaining_to_target"] == 40
    assert res["overview"]["target_reached"] is False
    assert res["overview"]["collection_progress_pct"] == 20.0
    assert res["overview"]["study_status"] == "INCOMPLETE"


def test_target_50_dataset(tmp_path: Path):
    """N = 50 target reached state."""
    db_file = tmp_path / "target_test.db"
    init_db(db_file)

    for i in range(1, 51):
        obs = _make_obs(
            test_id=i,
            domain=f"target-site-{i}.com",
            ip=f"192.168.1.{i}",
            trust_score=70.0 + (i % 25),
            risk_score=15.0 + (i % 30),
        )
        save_field_observation(obs, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)

    assert res["overview"]["total_observations"] == 50
    assert res["overview"]["remaining_to_target"] == 0
    assert res["overview"]["target_reached"] is True
    assert res["overview"]["collection_progress_pct"] == 100.0
    assert res["overview"]["study_status"] == "TARGET_REACHED"


def test_unknown_and_missing_values(tmp_path: Path):
    """Unknown security, missing geo, and missing infra segregated cleanly."""
    db_file = tmp_path / "unknowns_test.db"
    init_db(db_file)

    # 1 known record
    obs1 = _make_obs(
        test_id=1,
        domain="known.com",
        https="Enabled",
        tls="Valid",
        infra="Cloud / Datacenter",
        trust_score=90.0,
        risk_score=10.0,
    )
    save_field_observation(obs1, db_path=db_file)

    # 1 record with Unknown values and None scores
    obs2 = _make_obs(
        test_id=2,
        domain="unknown-site.org",
        https="Unknown",
        tls="Unknown",
        infra="Unknown",
        trust_score=None,
        risk_score=None,
    )
    save_field_observation(obs2, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)

    sec = res["security_analysis"]
    assert sec["https_status"]["enabled"] == 1
    assert sec["https_status"]["unknown"] == 1
    assert sec["https_status"]["disabled"] == 0
    assert sec["https_status"]["adoption_pct"] == 50.0

    assert sec["tls_status"]["valid"] == 1
    assert sec["tls_status"]["unknown"] == 1
    assert sec["tls_status"]["invalid_or_expired"] == 0
    assert sec["tls_status"]["valid_pct"] == 50.0

    # Scores: missing score must NOT pull min down to 0
    trust = res["trust_analysis"]
    assert trust["count"] == 1
    assert trust["min"] == 90.0
    assert trust["max"] == 90.0
    assert trust["mean"] == 90.0


def test_trust_score_aggregation(tmp_path: Path):
    """Verify trust score univariate stats and 5-bracket histogram."""
    db_file = tmp_path / "trust_test.db"
    init_db(db_file)

    # 5 observations placed in each bracket: [10, 30, 50, 70, 90]
    scores = [10.0, 30.0, 50.0, 70.0, 90.0]
    classes = ["Very Low Trust", "Low Trust", "Moderate Trust", "High Trust", "Very High Trust"]
    for idx, (s, c) in enumerate(zip(scores, classes), start=1):
        obs = _make_obs(
            test_id=idx,
            domain=f"domain-{idx}.com",
            trust_score=s,
            trust_class=c,
        )
        save_field_observation(obs, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)
    trust = res["trust_analysis"]

    assert trust["count"] == 5
    assert trust["min"] == 10.0
    assert trust["max"] == 90.0
    assert trust["mean"] == 50.0
    assert trust["std_dev"] is not None

    hist = trust["histogram"]
    assert len(hist) == 5
    # Each bracket should have exactly 1 record (20.0%)
    for b in hist:
        assert b["count"] == 1
        assert b["pct"] == 20.0

    # Classifications count
    c_counts = {item["classification"]: item["count"] for item in trust["classifications"]}
    for c in classes:
        assert c_counts.get(c) == 1


def test_risk_score_aggregation(tmp_path: Path):
    """Verify IP risk score univariate stats and 5-bracket histogram."""
    db_file = tmp_path / "risk_test.db"
    init_db(db_file)

    # 5 observations placed in each bracket: [15, 35, 55, 75, 95]
    scores = [15.0, 35.0, 55.0, 75.0, 95.0]
    for idx, s in enumerate(scores, start=1):
        obs = _make_obs(
            test_id=idx,
            domain=f"risk-domain-{idx}.com",
            risk_score=s,
            risk_class="Custom Risk",
        )
        save_field_observation(obs, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)
    risk = res["risk_analysis"]

    assert risk["count"] == 5
    assert risk["min"] == 15.0
    assert risk["max"] == 95.0
    assert risk["mean"] == 55.0

    hist = risk["histogram"]
    for b in hist:
        assert b["count"] == 1
        assert b["pct"] == 20.0


def test_https_and_tls_statistics(tmp_path: Path):
    """Verify security analysis percentages across enabled, disabled, unknown."""
    db_file = tmp_path / "sec_test.db"
    init_db(db_file)

    # 2 Enabled, 1 Disabled, 1 Unknown
    specs = [
        ("site1.com", "Enabled", "Valid"),
        ("site2.com", "Enabled", "Valid"),
        ("site3.com", "Disabled", "Invalid"),
        ("site4.com", "Unknown", "Unknown"),
    ]
    for idx, (dom, h, t) in enumerate(specs, start=1):
        obs = _make_obs(test_id=idx, domain=dom, https=h, tls=t)
        save_field_observation(obs, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)
    sec = res["security_analysis"]

    assert sec["https_status"]["enabled"] == 2
    assert sec["https_status"]["disabled"] == 1
    assert sec["https_status"]["unknown"] == 1
    assert sec["https_status"]["adoption_pct"] == 50.0

    assert sec["tls_status"]["valid"] == 2
    assert sec["tls_status"]["invalid_or_expired"] == 1
    assert sec["tls_status"]["unknown"] == 1
    assert sec["tls_status"]["valid_pct"] == 50.0


def test_ip_version_statistics(tmp_path: Path):
    """Verify IPv4 vs IPv6 classification ratios."""
    db_file = tmp_path / "ip_ver_test.db"
    init_db(db_file)

    # 3 IPv4, 1 IPv6
    specs = [
        ("ipv4-1.com", "1.1.1.1", "IPv4"),
        ("ipv4-2.com", "8.8.8.8", "IPv4"),
        ("ipv4-3.com", "9.9.9.9", "IPv4"),
        ("ipv6-1.com", "2606:4700:4700::1111", "IPv6"),
    ]
    for idx, (dom, ip, ver) in enumerate(specs, start=1):
        obs = _make_obs(test_id=idx, domain=dom, ip=ip, ip_version=ver)
        save_field_observation(obs, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)
    net = res["network_analysis"]["ip_versions"]

    assert net["ipv4"] == 3
    assert net["ipv6"] == 1
    assert net["ipv4_pct"] == 75.0
    assert net["ipv6_pct"] == 25.0


def test_infrastructure_classification(tmp_path: Path):
    """Verify Cloud/Datacenter vs Traditional infrastructure density."""
    db_file = tmp_path / "infra_test.db"
    init_db(db_file)

    specs = [
        ("cloud1.com", "Cloud / Datacenter"),
        ("cloud2.com", "Hosting / CDN"),
        ("trad1.com", "Enterprise / ISP"),
        ("trad2.com", "Residential"),
    ]
    for idx, (dom, infra) in enumerate(specs, start=1):
        obs = _make_obs(test_id=idx, domain=dom, infra=infra)
        save_field_observation(obs, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)
    infra = res["network_analysis"]["infrastructure"]

    assert infra["cloud_datacenter"] == 2
    assert infra["traditional_other"] == 2
    assert infra["cloud_pct"] == 50.0


def test_threat_detection_counts(tmp_path: Path):
    """Verify VPN, Proxy, Tor threat indicator counters."""
    db_file = tmp_path / "threat_test.db"
    init_db(db_file)

    obs1 = _make_obs(test_id=1, domain="vpn-node.com", vpn="DETECTED")
    obs2 = _make_obs(test_id=2, domain="proxy-node.com", proxy="DETECTED")
    obs3 = _make_obs(test_id=3, domain="clean-node.com")
    for o in (obs1, obs2, obs3):
        save_field_observation(o, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)
    threats = res["network_analysis"]["threat_indicators"]

    assert threats["vpn"] == 1
    assert threats["proxy"] == 1
    assert threats["tor"] == 0
    assert threats["any_threat_flag"] == 2


def test_comparison_analytics(tmp_path: Path):
    """Verify highest and lowest trust/risk site sorting."""
    db_file = tmp_path / "cmp_test.db"
    init_db(db_file)

    obs_low = _make_obs(test_id=1, domain="low-trust.com", trust_score=20.0, risk_score=85.0)
    obs_mid = _make_obs(test_id=2, domain="mid-trust.com", trust_score=60.0, risk_score=40.0)
    obs_high = _make_obs(test_id=3, domain="high-trust.com", trust_score=95.0, risk_score=10.0)
    for o in (obs_low, obs_mid, obs_high):
        save_field_observation(o, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)
    cmp = res["comparison_analytics"]

    # Highest trust must have high-trust.com first
    assert cmp["highest_trust_sites"][0]["domain"] == "high-trust.com"
    assert cmp["highest_trust_sites"][0]["trust_score"] == 95.0

    # Lowest trust must have low-trust.com first
    assert cmp["lowest_trust_sites"][0]["domain"] == "low-trust.com"
    assert cmp["lowest_trust_sites"][0]["trust_score"] == 20.0

    # Highest risk must have low-trust.com first (risk=85.0)
    assert cmp["highest_risk_sites"][0]["domain"] == "low-trust.com"
    assert cmp["highest_risk_sites"][0]["risk_score"] == 85.0


def test_deterministic_insights(tmp_path: Path):
    """Verify factual, non-speculative empirical research insights are emitted."""
    db_file = tmp_path / "insights_test.db"
    init_db(db_file)

    # Create 5 HTTPS enabled cloud hosts
    for i in range(1, 6):
        obs = _make_obs(
            test_id=i,
            domain=f"corp{i}.com",
            https="Enabled",
            tls="Valid",
            infra="Cloud / Datacenter",
            country="United States",
        )
        save_field_observation(obs, db_path=db_file)

    res = compute_field_study_analytics(db_path=db_file, target_count=50)
    insights = res["research_insights"]

    assert len(insights) > 0
    # Every insight must have category, title, finding, metric
    for ins in insights:
        assert ins["category"] in ["security", "infrastructure", "network", "geographic", "reputation"]
        assert len(ins["title"]) > 0
        assert len(ins["finding"]) > 0
        assert len(ins["metric"]) > 0
