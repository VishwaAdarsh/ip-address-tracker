"""
AI Evidence-Based Explainer Engine Module for IP PULSE Platform.

Provides:
- Evidence-grounded natural language risk and intelligence explanation generation
- Strictly relies on empirical scan findings without hallucinating or fabricating missing data
"""
from typing import Optional

from core.intel_chain import IntelligenceChain
from core.ip_intel import IPIntelligence
from core.risk_engine import RiskScore
from core.security_scanner import SecurityInfo


def generate_ai_explanation(
    target: str,
    security: SecurityInfo,
    ip_intel: IPIntelligence,
    risk: RiskScore,
    chain: IntelligenceChain,
) -> str:
    """
    Generate a transparent, evidence-based natural language explanation report.

    Args:
    - target: Target domain or IP string
    - security: SecurityInfo dataclass instance
    - ip_intel: IPIntelligence dataclass instance
    - risk: RiskScore dataclass instance
    - chain: IntelligenceChain dataclass instance

    Returns:
    - Multi-paragraph factual explanation string
    """
    paragraphs = []

    # 1. Executive Summary Paragraph
    paragraphs.append(
        f"Target '{target}' exhibits a Website Trust Score of {risk.trust_score}/100 "
        f"and an IP Risk Score of {risk.risk_score}/100, placing it in the '{risk.risk_level} Risk' classification "
        f"with a data confidence rating of {int(risk.confidence_score * 100)}%."
    )

    # 2. Security Signals Paragraph
    sec_details = []
    if security.https_enabled and security.ssl_valid:
        sec_details.append(f"a valid SSL/TLS certificate issued by '{security.ssl_issuer}' ({security.ssl_expiry_days} days remaining)")
    elif security.https_enabled:
        sec_details.append("HTTPS enabled with unverified or self-signed certificate")
    else:
        sec_details.append("unencrypted HTTP transport (HTTPS not enabled)")

    if security.security_headers.get("hsts"):
        sec_details.append("HSTS strict transport security enforced")
    if security.security_headers.get("csp"):
        sec_details.append("Content Security Policy (CSP) active")

    paragraphs.append(
        f"Security Intelligence Scan: The target operates with {', '.join(sec_details)}. "
        f"HTTP redirect chain registered {security.redirect_count} redirect hop(s) terminating at '{security.final_url}'."
    )

    # 3. Network Infrastructure & Provenance Paragraph
    paragraphs.append(
        f"Infrastructure & Network Provenance: The resolved target IP {chain.resolved_ip} ({chain.ip_version}) "
        f"is classified under '{chain.infrastructure_type}' ({chain.organization}, {chain.asn}) "
        f"geolocated in {chain.city}, {chain.country}. "
        f"Synthesis: {chain.ip_personality}."
    )

    # 4. Positive vs Risk Attribution Paragraph
    factor_summary = []
    if risk.positive_factors:
        factor_summary.append("Key Safety Drivers: " + "; ".join(risk.positive_factors[:3]))
    if risk.risk_factors:
        factor_summary.append("Identified Risk Factors: " + "; ".join(risk.risk_factors[:3]))
    if not risk.risk_factors:
        factor_summary.append("No active threat anomalies or anonymizer exit nodes were detected.")

    paragraphs.append("Risk Attribution Summary: " + " | ".join(factor_summary))

    return "\n\n".join(paragraphs)
