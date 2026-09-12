"""
Trust & Risk Engine Module for IP PULSE Platform.

Provides:
- Transparent weighted 0–100 Website Trust Score and IP Risk Score computation
- Score factor attribution breakdowns (positive factors & risk factors)
- Dynamic confidence rating calculation (0.0 to 1.0)
- Categorical risk level classification (Low, Moderate, High, Critical)
"""
from dataclasses import dataclass, field
from typing import List, Optional

from core.ip_intel import IPIntelligence
from core.security_scanner import SecurityInfo


@dataclass
class RiskScore:
    """Dataclass holding complete Trust & Risk Engine evaluation outputs."""

    trust_score: int = 100        # 0 to 100 (higher = safer)
    risk_score: int = 0           # 0 to 100 (higher = riskier)
    risk_level: str = "Low"       # Low, Moderate, High, Critical
    confidence_score: float = 1.0  # 0.0 to 1.0 confidence
    positive_factors: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)


def evaluate_trust_and_risk(
    security: SecurityInfo,
    ip_intel: IPIntelligence,
    geolocation_available: bool = True,
) -> RiskScore:
    """
    Compute Website Trust Score (0-100) and IP Risk Score (0-100) with transparent factor attribution.

    Args:
    - security: SecurityInfo dataclass instance from Security Scanner
    - ip_intel: IPIntelligence dataclass instance from IP Intel Engine
    - geolocation_available: bool flag indicating if valid geolocation data was retrieved

    Returns:
    - RiskScore dataclass instance
    """
    raw_trust = 50  # Base neutral baseline score
    positives: List[str] = []
    risks: List[str] = []

    # 1. Security Signals Audit
    if security.https_enabled and security.ssl_valid:
        raw_trust += 25
        positives.append("Valid HTTPS SSL/TLS Certificate (+25)")
        if security.ssl_issuer != "N/A":
            positives.append(f"Trusted Certificate Issuer: {security.ssl_issuer}")
    elif security.https_enabled and not security.ssl_valid:
        raw_trust -= 20
        risks.append("HTTPS Enabled but SSL/TLS Certificate Unverified/Expired (-20)")
    else:
        raw_trust -= 30
        risks.append("HTTPS / SSL Encrypted Channel Not Enabled (-30)")

    # Security Headers
    headers = security.security_headers or {}
    if headers.get("hsts"):
        raw_trust += 10
        positives.append("HSTS Enforced Strict Transport Security (+10)")
    if headers.get("csp"):
        raw_trust += 5
        positives.append("Content Security Policy (CSP) Active (+5)")
    if headers.get("x_frame_options"):
        raw_trust += 5
        positives.append("Anti-Clickjacking X-Frame-Options Header (+5)")

    # Redirect Hops
    if security.redirect_count > 3:
        raw_trust -= 10
        risks.append(f"Multiple HTTP Redirect Hops Detected ({security.redirect_count} hops) (-10)")

    # 2. IP & Infrastructure Signals Audit
    infra = ip_intel.infrastructure_type
    if infra in ["CDN / Edge Hub", "Cloud Hosting"]:
        raw_trust += 15
        positives.append(f"Enterprise Infrastructure Hub: {infra} ({ip_intel.hosting_provider}) (+15)")
    elif infra == "Enterprise Network":
        raw_trust += 10
        positives.append("Verified Institutional / Corporate Network (+10)")

    # Anonymizers & Threat Signals
    if ip_intel.is_tor:
        raw_trust -= 45
        risks.append("Detected Active Tor Anonymous Exit Node (-45)")
    if ip_intel.is_vpn or ip_intel.is_proxy:
        raw_trust -= 25
        risks.append("Detected Commercial Anonymous VPN / Proxy Gateway (-25)")

    # Clamp Trust Score strictly between 0 and 100
    final_trust = max(0, min(100, raw_trust))
    final_risk = 100 - final_trust

    # Determine Categorical Risk Level
    if final_risk <= 20:
        r_level = "Low"
    elif final_risk <= 45:
        r_level = "Moderate"
    elif final_risk <= 70:
        r_level = "High"
    else:
        r_level = "Critical"

    # Calculate Data Confidence Score (0.0 to 1.0)
    conf = 1.0
    if not geolocation_available:
        conf -= 0.2
    if security.error_message:
        conf -= 0.1
    if ip_intel.organization == "N/A":
        conf -= 0.1
    conf_score = max(0.5, round(conf, 2))

    return RiskScore(
        trust_score=final_trust,
        risk_score=final_risk,
        risk_level=r_level,
        confidence_score=conf_score,
        positive_factors=positives,
        risk_factors=risks,
    )
