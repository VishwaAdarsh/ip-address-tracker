"""
Risk & Intelligence Orchestration Service Module for IP PULSE Platform.

Orchestrates:
- Base lookup service (DNS resolution & multi-provider Geolocation)
- Website Security Intelligence Scanner (HTTPS, SSL cert, redirects)
- IP Intelligence Engine (Infrastructure classification, Proxy/VPN/Tor heuristics)
- Trust & Risk Engine (0-100 weighted trust & risk scoring)
- Intelligence Chain & IP Personality Engine
- AI Evidence Explainer Engine
"""
from dataclasses import dataclass
from typing import Optional

from core.ai_explainer import generate_ai_explanation
from core.intel_chain import IntelligenceChain, build_intelligence_chain
from core.ip_intel import IPIntelligence, analyze_ip_intelligence
from core.risk_engine import RiskScore, evaluate_trust_and_risk
from core.security_scanner import SecurityInfo, scan_website_security
from services.lookup_service import LookupResult, LookupStatus, perform_lookup


@dataclass
class FullIntelligenceResult:
    """Dataclass holding complete multi-layered Intelligence Audit Result."""

    base_lookup: LookupResult
    security: SecurityInfo
    ip_intel: IPIntelligence
    risk: RiskScore
    chain: IntelligenceChain
    explanation: str


def perform_full_intelligence_scan(target: str, save_to_db: bool = True) -> FullIntelligenceResult:
    """
    Perform a complete multi-layered IP Intelligence, Geolocation & Website Risk scan.

    Args:
    - target: Domain name or IP address string
    - save_to_db: bool flag to persist base lookup to SQLite History

    Returns:
    - FullIntelligenceResult dataclass instance
    """
    # 1. Execute Base DNS & Geolocation Lookup
    lookup_res = perform_lookup(target, save_to_db=save_to_db)

    # 2. Execute Website Security Probing
    sec_info = scan_website_security(target)

    # 3. Execute IP Intelligence Classification
    ip_val = lookup_res.selected_ip or target
    ip_intel = analyze_ip_intelligence(
        ip_address=ip_val,
        asn=lookup_res.asn,
        org=lookup_res.organization,
        isp=lookup_res.isp,
    )

    # 4. Evaluate Trust & Risk Scoring
    geo_avail = lookup_res.overall_status == LookupStatus.SUCCESS
    risk_score = evaluate_trust_and_risk(
        security=sec_info,
        ip_intel=ip_intel,
        geolocation_available=geo_avail,
    )

    # 5. Assemble Provenance Chain & IP Personality
    intel_chain = build_intelligence_chain(lookup_res, ip_intel)

    # 6. Synthesize AI Evidence Explanation Report
    explanation_text = generate_ai_explanation(
        target=target,
        security=sec_info,
        ip_intel=ip_intel,
        risk=risk_score,
        chain=intel_chain,
    )

    return FullIntelligenceResult(
        base_lookup=lookup_res,
        security=sec_info,
        ip_intel=ip_intel,
        risk=risk_score,
        chain=intel_chain,
        explanation=explanation_text,
    )
