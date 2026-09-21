"""
Unit and Integration Tests for Phase 22 Explainable AI Intelligence Layer.

Validates:
- Data minimization and privacy protection
- Factual grounding and zero hallucination
- Explicit handling and reporting of UNKNOWN signals
- Prohibition of definitive/absolute security claims
- 100% score preservation (Trust & Risk scores unchanged)
- Multi-provider abstraction (Rule-Based and Gemini)
- Provider unavailable and disabled states
- In-memory caching and duplicate request prevention
- Seamless integration with core deterministic scan services
"""
import pytest
from unittest.mock import MagicMock, patch

from backend.intelligence.ai_explainer import (
    AIExplanationResult,
    GeminiAIProvider,
    RuleBasedAIProvider,
    _EXPLANATION_CACHE,
    build_explanation_payload,
    explain_intelligence,
    generate_ai_explanation,
    get_ai_provider,
    sanitize_security_claims,
)
from backend.intelligence.intel_chain import IntelligenceChain, build_intelligence_chain
from backend.intelligence.ip_intel import IPIntelligence, analyze_ip_intelligence
from backend.security.risk_engine import RiskScore, evaluate_trust_and_risk
from backend.security.security_scanner import SecurityInfo
from backend.services.lookup_service import LookupResult, LookupStatus
from backend.services.risk_analysis_service import perform_full_intelligence_scan


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure clean explanation cache before each test."""
    _EXPLANATION_CACHE.clear()
    yield
    _EXPLANATION_CACHE.clear()


@pytest.fixture
def sample_scan_dict():
    """Return a standard serialized scan result dictionary."""
    return {
        "target": "example.com",
        "base": {
            "input": "example.com",
            "normalized_input": "example.com",
            "selected_ip": "93.184.216.34",
            "ip_version": "IPv4",
            "country": "United States",
            "region": "California",
            "city": "Los Angeles",
            "latitude": 34.0522,
            "longitude": -118.2437,
            "asn": "AS15133",
            "organization": "EDGECAST",
            "isp": "Verizon Digital Media Services",
        },
        "security": {
            "is_https": True,
            "tls_valid": True,
            "tls_version": "TLS 1.3",
            "issuer_org": "DigiCert Global Root G2",
            "expires_in_days": 180,
            "hsts_header": True,
            "csp_header": False,
            "redirect_count": 0,
        },
        "ip_intel": {
            "ip_address": "93.184.216.34",
            "asn": "AS15133",
            "organization": "EDGECAST",
            "isp": "Verizon Digital Media Services",
            "infrastructure_type": "CDN / Edge Hub",
            "network_type": "Cloud / Hosting",
            "vpn_status": "NOT_DETECTED",
            "proxy_status": "NOT_DETECTED",
            "tor_status": "NOT_DETECTED",
            "datacenter_status": "DETECTED",
        },
        "risk": {
            "trust_score": 92,
            "risk_score": 12,
            "risk_category": "Low",
            "confidence_score": 0.95,
            "positive_factors": [
                "HTTPS transport enforced",
                "Valid TLS certificate with >30 days validity",
                "HTTP Strict Transport Security (HSTS) active",
            ],
            "risk_factors": [
                "Infrastructure hosted in Datacenter / Cloud environment",
            ],
        },
        "personality": "High-capacity commercial Content Delivery Network (CDN) edge endpoint.",
        "intelligence_chain": {
            "domain": "example.com",
            "resolved_ip": "93.184.216.34",
            "asn": "AS15133",
            "organization": "EDGECAST",
            "infrastructure": "CDN / Edge Hub",
            "location": "Los Angeles, United States",
        },
    }


# =============================================================================
# 1. Payload Minimization & Privacy Protection
# =============================================================================

def test_build_explanation_payload_data_minimization(sample_scan_dict):
    """Verify only relevant network/security telemetry is sent, omitting internal paths or credentials."""
    payload = build_explanation_payload("example.com", sample_scan_dict)

    assert payload["target"] == "example.com"
    assert payload["resolved_ip"] == "93.184.216.34"
    assert payload["website_trust_score"] == 92
    assert payload["ip_risk_score"] == 12
    assert payload["https_enabled"] is True
    assert payload["asn"] == "AS15133"

    # Ensure no internal keys or sensitive fields exist
    forbidden_keys = {"db_path", "api_key", "password", "token", "history", "secret"}
    for k in payload:
        assert k not in forbidden_keys


# =============================================================================
# 2. Score Preservation Guarantee
# =============================================================================

def test_deterministic_score_preservation(sample_scan_dict):
    """Verify Trust Score and IP Risk Score are identical before and after AI explanation."""
    orig_trust = sample_scan_dict["risk"]["trust_score"]
    orig_risk = sample_scan_dict["risk"]["risk_score"]

    result = explain_intelligence("example.com", sample_scan_dict, provider_name="rule_based")

    # Scores must remain 100% unchanged in the intelligence payload
    assert sample_scan_dict["risk"]["trust_score"] == orig_trust
    assert sample_scan_dict["risk"]["risk_score"] == orig_risk

    # Result mentions the exact scores
    assert str(orig_trust) in result.summary or str(orig_trust) in result.trust_explanation
    assert str(orig_risk) in result.summary or str(orig_risk) in result.risk_explanation


# =============================================================================
# 3. Rule-Based Provider Structure & Content
# =============================================================================

def test_rule_based_provider_structure(sample_scan_dict):
    """Verify all 9 structured dimensions are returned by the rule-based provider."""
    provider = RuleBasedAIProvider()
    payload = build_explanation_payload("example.com", sample_scan_dict)
    res = provider.generate_explanation(payload)

    assert res.status == "success"
    assert res.provider == "rule_based"
    assert res.summary != ""
    assert res.trust_explanation != ""
    assert res.risk_explanation != ""
    assert len(res.positive_signals) > 0
    assert len(res.negative_signals) > 0
    assert res.recommendation != ""
    assert res.limitations != ""
    assert not res.cached


# =============================================================================
# 4. Strict Factual Grounding & UNKNOWN Reporting
# =============================================================================

def test_unknown_signals_explicit_reporting():
    """Verify missing signals are explicitly categorized as UNKNOWN and never fabricated."""
    sparse_data = {
        "target": "unknown-host.test",
        "base": {
            "selected_ip": "198.51.100.1",
            "country": "UNKNOWN",
            "city": "UNKNOWN",
            "asn": "UNKNOWN",
            "organization": "UNKNOWN",
        },
        "security": {
            "is_https": False,
            "tls_valid": False,
            "issuer_org": "UNKNOWN",
            "hsts_header": None,
        },
        "ip_intel": {
            "infrastructure_type": "Unknown",
            "network_type": "Unknown",
        },
        "risk": {
            "trust_score": 25,
            "risk_score": 45,
            "positive_factors": [],
            "risk_factors": ["Plain HTTP transport"],
        },
    }

    payload = build_explanation_payload("unknown-host.test", sparse_data)
    assert len(payload["unknown_signals"]) >= 3

    # Generate explanation
    res = explain_intelligence("unknown-host.test", sparse_data, provider_name="rule_based")
    assert res.status == "success"
    assert len(res.unknown_signals) >= 3
    # Check that unknown telemetry is mentioned
    assert any("Geographic" in u or "ASN" in u or "TLS" in u for u in res.unknown_signals)


# =============================================================================
# 5. Prohibition of Absolute Security Claims
# =============================================================================

def test_sanitize_security_claims():
    """Verify absolute assertions are transformed into calibrated, non-definitive language."""
    input_text = (
        "This domain is 100% safe and definitely genuine. "
        "The server is completely secure and guaranteed safe."
    )
    sanitized = sanitize_security_claims(input_text)

    assert "100% safe" not in sanitized.lower()
    assert "definitely genuine" not in sanitized.lower()
    assert "completely secure" not in sanitized.lower()
    assert "guaranteed safe" not in sanitized.lower()

    assert "appears lower risk" in sanitized
    assert "authentic infrastructure" in sanitized


# =============================================================================
# 6. In-Memory Caching & Duplicate Request Prevention
# =============================================================================

def test_in_memory_caching_behavior(sample_scan_dict):
    """Verify identical subsequent explanation requests hit cache without re-evaluating."""
    res1 = explain_intelligence("example.com", sample_scan_dict, provider_name="rule_based")
    assert not res1.cached

    res2 = explain_intelligence("example.com", sample_scan_dict, provider_name="rule_based")
    assert res2.cached
    assert res2.summary == res1.summary

    # Bypass cache flag
    res3 = explain_intelligence("example.com", sample_scan_dict, provider_name="rule_based", bypass_cache=True)
    assert not res3.cached


# =============================================================================
# 7. Provider Unavailable & Missing Key Handling
# =============================================================================

def test_gemini_provider_missing_key():
    """Verify requesting Gemini without an API key gracefully returns provider_unavailable."""
    provider = GeminiAIProvider(api_key="")
    res = provider.generate_explanation({"target": "test.com"})

    assert res.status == "provider_unavailable"
    assert res.provider == "gemini"
    assert "API key" in res.summary
    assert "Deterministic analysis" in res.trust_explanation


def test_ai_disabled_toggle(sample_scan_dict):
    """Verify explain_intelligence returns disabled status when AI_ENABLED is False."""
    with patch("backend.intelligence.ai_explainer.AI_ENABLED", False):
        res = explain_intelligence("example.com", sample_scan_dict)
        assert res.status == "provider_unavailable"
        assert res.model == "disabled"
        assert "disabled" in res.summary.lower()


# =============================================================================
# 8. Backward Compatibility with Existing Services
# =============================================================================

def test_backward_compatible_generate_ai_explanation():
    """Verify legacy generate_ai_explanation signature returns unified text."""
    sec = SecurityInfo(https_enabled=True, ssl_valid=True, ssl_issuer="Let's Encrypt")
    intel = IPIntelligence(ip_address="1.1.1.1", asn="AS13335", organization="Cloudflare")
    risk = RiskScore(trust_score=88, risk_score=15, risk_level="Low")
    chain = IntelligenceChain(resolved_ip="1.1.1.1", ip_personality="High performance DNS resolver")

    text = generate_ai_explanation("1.1.1.1", sec, intel, risk, chain)
    assert isinstance(text, str)
    assert len(text) > 50
    assert "Trust Analysis" in text
    assert "Risk Analysis" in text


# =============================================================================
# 9. Full System Integration
# =============================================================================

def test_full_intelligence_scan_unaffected_by_ai():
    """Verify that perform_full_intelligence_scan works cleanly with the updated AI module."""
    # Run scan on a simulated or local lookup
    result = perform_full_intelligence_scan("127.0.0.1", save_to_db=False)

    assert result.base_lookup is not None
    assert result.security is not None
    assert result.ip_intel is not None
    assert result.risk is not None
    assert result.chain is not None
    assert isinstance(result.explanation, str)
    assert len(result.explanation) > 0
