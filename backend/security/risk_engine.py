"""
Explainable Website Trust & IP Risk Engine Module for IP PULSE Platform (Phase 17).

Provides:
- Deterministic, explainable Website Trust Score (0–100) based on verified security signals
- Deterministic, explainable IP Risk Score (0–100) based on verified IP & infrastructure signals
- Strict separation of Website Trust (security-centric) and IP Risk (infrastructure-centric)
- Fine-grained signal attribution: status, point delta, reasoning, and evidence coverage
- Independent confidence calculation based on evidence coverage
- Neutral treatment of missing/unknown data (unknown != safe, unknown != dangerous)
- Non-overclaiming analytical classifications with ethical disclaimers
- 100% backward compatibility with existing IP PULSE pipelines and consumers
"""
from dataclasses import asdict, dataclass, field
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.intelligence.ip_intel import IPIntelligence, IPIntelligenceResult
from backend.security.security_scanner import SecurityInfo, WebsiteSecurityResult

# ==============================================================================
# Configurable Classification Constants & Thresholds
# ==============================================================================

# Website Trust Score Tiers (0–100: Higher = more positive security signals)
TRUST_TIER_LIKELY_SAFE = "LIKELY SAFE"            # 80–100
TRUST_TIER_GENERALLY_SAFE = "GENERALLY SAFE"        # 60–79
TRUST_TIER_REVIEW_RECOMMENDED = "REVIEW RECOMMENDED" # 40–59
TRUST_TIER_SUSPICIOUS = "SUSPICIOUS"                # 20–39
TRUST_TIER_HIGH_RISK = "HIGH RISK"                  # 0–19
TRUST_TIER_UNKNOWN = "UNKNOWN"

TRUST_TIER_LIKELY_SAFE_MIN = 80
TRUST_TIER_GENERALLY_SAFE_MIN = 60
TRUST_TIER_REVIEW_RECOMMENDED_MIN = 40
TRUST_TIER_SUSPICIOUS_MIN = 20

# IP Risk Score Tiers (0–100: Higher = more observed risk indicators)
RISK_TIER_LOW = "LOW RISK"                          # 0–19
RISK_TIER_MODERATE = "MODERATE"                     # 20–39
RISK_TIER_ELEVATED = "ELEVATED"                     # 40–59
RISK_TIER_HIGH = "HIGH RISK"                        # 60–79
RISK_TIER_CRITICAL = "CRITICAL"                     # 80–100
RISK_TIER_UNKNOWN = "UNKNOWN"

RISK_TIER_LOW_MAX = 19
RISK_TIER_MODERATE_MAX = 39
RISK_TIER_ELEVATED_MAX = 59
RISK_TIER_HIGH_MAX = 79

# Confidence Levels (Reflects breadth of available evidence, independent of score)
CONFIDENCE_HIGH = "HIGH"                            # >= 80% evidence coverage
CONFIDENCE_MEDIUM = "MEDIUM"                        # 50%–79% evidence coverage
CONFIDENCE_LOW = "LOW"                              # 20%–49% evidence coverage
CONFIDENCE_UNKNOWN = "UNKNOWN"                      # < 20% evidence coverage

CONFIDENCE_HIGH_MIN = 0.80
CONFIDENCE_MEDIUM_MIN = 0.50
CONFIDENCE_LOW_MIN = 0.20

# Mandatory Analytical Disclaimers
TRUST_DISCLAIMER = (
    "IP PULSE Website Trust Scores are heuristic analytical assessments derived strictly from "
    "observed technical indicators (e.g. TLS certificates, protocol enforcement, and headers). "
    "They do not constitute definitive proof of website legitimacy, business integrity, or safety from fraud."
)

IP_RISK_DISCLAIMER = (
    "IP PULSE IP Risk Scores reflect observed network infrastructure indicators (e.g. Tor, VPN, proxy, "
    "or datacenter hosting) and must not be interpreted as definitive proof of malicious activity or threat actor origin."
)

UNIFIED_DISCLAIMER = (
    "IP PULSE scores are heuristic analytical assessments based on available technical signals. "
    "They do not guarantee that a website is legitimate, safe, fraudulent, or malicious. "
    "IP Risk reflects observed network indicators and should not be interpreted as proof of malicious activity."
)


# ==============================================================================
# Structured Data Models
# ==============================================================================

@dataclass
class ScoringSignal:
    """Represents a single evaluated technical signal and its scoring contribution."""

    name: str
    status: str
    points: int
    reason: str
    source: str = "IP PULSE Analytics"
    is_available: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrustScoreResult:
    """Structured evaluation output for Website Trust Score."""

    score: int = 50
    classification: str = TRUST_TIER_REVIEW_RECOMMENDED
    confidence: str = CONFIDENCE_MEDIUM
    evidence_coverage: str = "0/0"
    available_signals_count: int = 0
    total_signals_count: int = 0
    positive_points: int = 0
    negative_points: int = 0
    signals: List[Dict[str, Any]] = field(default_factory=list)
    unknown_signals: List[Dict[str, Any]] = field(default_factory=list)
    explanation: str = ""
    disclaimer: str = TRUST_DISCLAIMER
    generated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IPRiskResult:
    """Structured evaluation output for IP Risk Score."""

    score: int = 5
    classification: str = RISK_TIER_LOW
    confidence: str = CONFIDENCE_MEDIUM
    evidence_coverage: str = "0/0"
    available_signals_count: int = 0
    total_signals_count: int = 0
    risk_points: int = 0
    mitigation_points: int = 0
    signals: List[Dict[str, Any]] = field(default_factory=list)
    neutral_signals: List[Dict[str, Any]] = field(default_factory=list)
    unknown_signals: List[Dict[str, Any]] = field(default_factory=list)
    explanation: str = ""
    disclaimer: str = IP_RISK_DISCLAIMER
    generated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskScore:
    """
    Unified Trust & Risk Engine output.
    Maintains 100% backward compatibility with legacy consumers while providing rich Phase 17 structures.
    """

    trust_score: int = 100
    risk_score: int = 0
    risk_level: str = "Low"                        # Legacy: "Low", "Moderate", "High", "Critical"
    risk_category: str = RISK_TIER_LOW             # Phase 17: "LOW RISK", "MODERATE", etc.
    confidence_score: float = 1.0                  # Legacy: 0.0 to 1.0 float
    confidence_rating: str = CONFIDENCE_HIGH       # Phase 17: "HIGH", "MEDIUM", "LOW", "UNKNOWN"
    positive_factors: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    trust: Optional[TrustScoreResult] = None
    ip_risk: Optional[IPRiskResult] = None
    disclaimer: str = UNIFIED_DISCLAIMER

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trust_score": self.trust_score,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "risk_category": self.risk_category,
            "confidence_score": self.confidence_score,
            "confidence_rating": self.confidence_rating,
            "positive_factors": self.positive_factors,
            "risk_factors": self.risk_factors,
            "trust": self.trust.to_dict() if self.trust else None,
            "ip_risk": self.ip_risk.to_dict() if self.ip_risk else None,
            "disclaimer": self.disclaimer,
        }


# ==============================================================================
# Helper Functions for Classification & Confidence
# ==============================================================================

def classify_trust_score(score: int, available_signals: int = 1) -> str:
    """Map numeric trust score (0–100) to analytical classification tier."""
    if available_signals == 0:
        return TRUST_TIER_UNKNOWN
    if score >= TRUST_TIER_LIKELY_SAFE_MIN:
        return TRUST_TIER_LIKELY_SAFE
    if score >= TRUST_TIER_GENERALLY_SAFE_MIN:
        return TRUST_TIER_GENERALLY_SAFE
    if score >= TRUST_TIER_REVIEW_RECOMMENDED_MIN:
        return TRUST_TIER_REVIEW_RECOMMENDED
    if score >= TRUST_TIER_SUSPICIOUS_MIN:
        return TRUST_TIER_SUSPICIOUS
    return TRUST_TIER_HIGH_RISK


def classify_ip_risk_score(score: int, available_signals: int = 1) -> str:
    """Map numeric IP risk score (0–100) to analytical classification tier."""
    if available_signals == 0:
        return RISK_TIER_UNKNOWN
    if score <= RISK_TIER_LOW_MAX:
        return RISK_TIER_LOW
    if score <= RISK_TIER_MODERATE_MAX:
        return RISK_TIER_MODERATE
    if score <= RISK_TIER_ELEVATED_MAX:
        return RISK_TIER_ELEVATED
    if score <= RISK_TIER_HIGH_MAX:
        return RISK_TIER_HIGH
    return RISK_TIER_CRITICAL


def calculate_confidence(available_count: int, total_count: int, penalty: float = 0.0) -> Tuple[str, float]:
    """
    Calculate evidence confidence tier and numeric ratio.
    Confidence reflects how much evidence was available, strictly independent of score value.
    """
    if total_count <= 0:
        return CONFIDENCE_UNKNOWN, 0.0

    raw_ratio = available_count / total_count
    adj_ratio = max(0.0, min(1.0, raw_ratio - penalty))

    if adj_ratio >= CONFIDENCE_HIGH_MIN:
        return CONFIDENCE_HIGH, round(adj_ratio, 2)
    if adj_ratio >= CONFIDENCE_MEDIUM_MIN:
        return CONFIDENCE_MEDIUM, round(adj_ratio, 2)
    if adj_ratio >= CONFIDENCE_LOW_MIN:
        return CONFIDENCE_LOW, round(adj_ratio, 2)
    return CONFIDENCE_UNKNOWN, round(adj_ratio, 2)


# ==============================================================================
# Website Trust Score Evaluation
# ==============================================================================

def evaluate_website_trust(
    security: Optional[Union[SecurityInfo, WebsiteSecurityResult]],
) -> TrustScoreResult:
    """
    Evaluate deterministic 0–100 Website Trust Score using verified security signals.

    Principles:
    - Base neutral score: 50.
    - Positive security configurations add points (+).
    - Missing or insecure configurations deduct points (-).
    - Unknown/missing data is treated neutrally (0 points) and documented.
    - Output is strictly clamped between 0 and 100.
    """
    base_score = 50
    evaluated_signals: List[ScoringSignal] = []
    unknown_signals: List[ScoringSignal] = []

    # Handle null / empty security input gracefully
    if security is None:
        unknown_sig = ScoringSignal(
            name="Security Inspection",
            status="Unknown",
            points=0,
            reason="No website security intelligence data was available.",
            source="Security Scanner",
            is_available=False,
        )
        return TrustScoreResult(
            score=base_score,
            classification=TRUST_TIER_REVIEW_RECOMMENDED,
            confidence=CONFIDENCE_UNKNOWN,
            evidence_coverage="0/8",
            available_signals_count=0,
            total_signals_count=8,
            positive_points=0,
            negative_points=0,
            signals=[],
            unknown_signals=[unknown_sig.to_dict()],
            explanation="Assessment limited: Security inspection was not performed or failed to execute.",
        )

    # Normalize fields across SecurityInfo and WebsiteSecurityResult
    https_enabled = getattr(security, "https_enabled", None)
    ssl_valid = getattr(security, "ssl_valid", getattr(security, "certificate_valid", None))
    cert_present = getattr(security, "certificate_present", None)
    if cert_present is None and ssl_valid is not None:
        cert_present = True if ssl_valid else (True if getattr(security, "ssl_issuer", "N/A") != "N/A" else False)
    
    expiry_days = getattr(security, "ssl_expiry_days", getattr(security, "certificate_days_remaining", None))
    redirect_count = getattr(security, "redirect_count", None)
    http_to_https_redirect = getattr(security, "http_to_https_redirect", None)
    if http_to_https_redirect is None and redirect_count is not None:
        http_to_https_redirect = (redirect_count > 0)

    sec_headers = getattr(security, "security_headers", {}) or {}
    hsts_active = sec_headers.get("hsts")
    csp_active = sec_headers.get("csp")
    x_frame_active = sec_headers.get("x_frame_options")

    # --------------------------------------------------------------------------
    # Signal 1: HTTPS Transport Encryption
    # --------------------------------------------------------------------------
    if https_enabled is True:
        evaluated_signals.append(ScoringSignal(
            name="HTTPS Protocol",
            status="Enabled",
            points=20,
            reason="Website enforces encrypted HTTPS transport, protecting in-transit user traffic.",
            source="Security Probe",
            is_available=True,
        ))
    elif https_enabled is False:
        evaluated_signals.append(ScoringSignal(
            name="HTTPS Protocol",
            status="Disabled",
            points=-25,
            reason="Unencrypted HTTP transport detected; traffic is vulnerable to eavesdropping and tampering.",
            source="Security Probe",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="HTTPS Protocol",
            status="Unknown",
            points=0,
            reason="HTTPS availability could not be verified due to network timeout or probe restriction.",
            source="Security Probe",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 2: SSL/TLS Certificate Presence
    # --------------------------------------------------------------------------
    if cert_present is True:
        evaluated_signals.append(ScoringSignal(
            name="Certificate Presence",
            status="Present",
            points=15,
            reason="An SSL/TLS public key certificate was presented during the cryptographic handshake.",
            source="TLS Handshake",
            is_available=True,
        ))
    elif cert_present is False:
        evaluated_signals.append(ScoringSignal(
            name="Certificate Presence",
            status="Missing",
            points=-20,
            reason="Endpoint did not present an SSL/TLS certificate during connection negotiation.",
            source="TLS Handshake",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="Certificate Presence",
            status="Unknown",
            points=0,
            reason="Certificate presence could not be confirmed.",
            source="TLS Handshake",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 3: Certificate Trust & Validation
    # --------------------------------------------------------------------------
    if ssl_valid is True:
        issuer_str = getattr(security, "ssl_issuer", getattr(security, "certificate_issuer", "Trusted CA"))
        evaluated_signals.append(ScoringSignal(
            name="Certificate Trust Chain",
            status="Valid",
            points=15,
            reason=f"Certificate successfully validated against system trust store (Issuer: {issuer_str}).",
            source="X.509 Chain Verifier",
            is_available=True,
        ))
    elif ssl_valid is False and cert_present is True:
        evaluated_signals.append(ScoringSignal(
            name="Certificate Trust Chain",
            status="Invalid / Untrusted",
            points=-25,
            reason="Certificate failed cryptographic validation (self-signed, untrusted CA, or hostname mismatch).",
            source="X.509 Chain Verifier",
            is_available=True,
        ))
    elif cert_present is False:
        evaluated_signals.append(ScoringSignal(
            name="Certificate Trust Chain",
            status="No Certificate",
            points=0,
            reason="Trust chain validation skipped: no certificate presented.",
            source="X.509 Chain Verifier",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="Certificate Trust Chain",
            status="Unknown",
            points=0,
            reason="Certificate trust verification was not determinable.",
            source="X.509 Chain Verifier",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 4: Certificate Expiration Lifespan
    # --------------------------------------------------------------------------
    if isinstance(expiry_days, (int, float)):
        if expiry_days >= 30:
            evaluated_signals.append(ScoringSignal(
                name="Certificate Lifespan",
                status="Healthy",
                points=5,
                reason=f"Certificate validity window is healthy with {int(expiry_days)} days remaining before expiration.",
                source="X.509 Temporal Audit",
                is_available=True,
            ))
        elif 0 <= expiry_days < 30:
            evaluated_signals.append(ScoringSignal(
                name="Certificate Lifespan",
                status="Expiring Soon",
                points=0,
                reason=f"Certificate remains valid but expires soon ({int(expiry_days)} days remaining).",
                source="X.509 Temporal Audit",
                is_available=True,
            ))
        else:
            evaluated_signals.append(ScoringSignal(
                name="Certificate Lifespan",
                status="Expired",
                points=-15,
                reason=f"Certificate expired {abs(int(expiry_days))} days ago and is no longer valid.",
                source="X.509 Temporal Audit",
                is_available=True,
            ))
    else:
        unknown_signals.append(ScoringSignal(
            name="Certificate Lifespan",
            status="Unknown",
            points=0,
            reason="Certificate expiration timeline is unavailable.",
            source="X.509 Temporal Audit",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 5: Automatic HTTP -> HTTPS Redirection
    # --------------------------------------------------------------------------
    if http_to_https_redirect is True:
        evaluated_signals.append(ScoringSignal(
            name="HTTPS Redirection",
            status="Enforced",
            points=10,
            reason="Insecure HTTP requests automatically redirect to encrypted HTTPS endpoints.",
            source="HTTP Redirect Audit",
            is_available=True,
        ))
    elif http_to_https_redirect is False:
        evaluated_signals.append(ScoringSignal(
            name="HTTPS Redirection",
            status="Not Enforced",
            points=-10,
            reason="Plain HTTP requests do not upgrade to HTTPS; downgrade attacks are possible.",
            source="HTTP Redirect Audit",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="HTTPS Redirection",
            status="Unknown",
            points=0,
            reason="HTTP to HTTPS redirection behavior was not tested or probe failed.",
            source="HTTP Redirect Audit",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 6: Strict Transport Security (HSTS)
    # --------------------------------------------------------------------------
    if hsts_active is True:
        evaluated_signals.append(ScoringSignal(
            name="HSTS Policy",
            status="Enforced",
            points=10,
            reason="HTTP Strict Transport Security (HSTS) header enforced, preventing SSL stripping.",
            source="HTTP Security Headers",
            is_available=True,
        ))
    elif hsts_active is False:
        # HSTS absence is neutral (many legitimate sites do not mandate HSTS)
        evaluated_signals.append(ScoringSignal(
            name="HSTS Policy",
            status="Not Detected",
            points=0,
            reason="Strict-Transport-Security header not detected (neutral).",
            source="HTTP Security Headers",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="HSTS Policy",
            status="Unknown",
            points=0,
            reason="HSTS header status was not inspected.",
            source="HTTP Security Headers",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 7: Defensive Framing & Injection Headers (CSP / X-Frame-Options)
    # --------------------------------------------------------------------------
    if csp_active is True or x_frame_active is True:
        active_headers = []
        if csp_active: active_headers.append("CSP")
        if x_frame_active: active_headers.append("X-Frame-Options")
        evaluated_signals.append(ScoringSignal(
            name="Defensive Headers",
            status="Active",
            points=5,
            reason=f"Defensive client-side security headers ({', '.join(active_headers)}) detected.",
            source="HTTP Security Headers",
            is_available=True,
        ))
    elif csp_active is False and x_frame_active is False:
        evaluated_signals.append(ScoringSignal(
            name="Defensive Headers",
            status="Not Detected",
            points=0,
            reason="CSP and X-Frame-Options headers not detected (neutral).",
            source="HTTP Security Headers",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="Defensive Headers",
            status="Unknown",
            points=0,
            reason="Defensive frame headers were not inspected.",
            source="HTTP Security Headers",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 8: Redirect Chain Depth
    # --------------------------------------------------------------------------
    if isinstance(redirect_count, int):
        if redirect_count > 3:
            evaluated_signals.append(ScoringSignal(
                name="Redirect Depth",
                status="Excessive",
                points=-10,
                reason=f"Excessive HTTP redirection hops ({redirect_count} hops) detected; possible configuration loop.",
                source="HTTP Redirect Audit",
                is_available=True,
            ))
        else:
            evaluated_signals.append(ScoringSignal(
                name="Redirect Depth",
                status="Normal",
                points=0,
                reason=f"Normal redirection hops ({redirect_count} hops).",
                source="HTTP Redirect Audit",
                is_available=True,
            ))
    else:
        unknown_signals.append(ScoringSignal(
            name="Redirect Depth",
            status="Unknown",
            points=0,
            reason="Redirect hop count unavailable.",
            source="HTTP Redirect Audit",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Summation & Boundary Normalization
    # --------------------------------------------------------------------------
    pos_pts = sum(s.points for s in evaluated_signals if s.points > 0)
    neg_pts = sum(abs(s.points) for s in evaluated_signals if s.points < 0)

    calculated_trust = base_score + pos_pts - neg_pts
    final_trust_score = max(0, min(100, calculated_trust))

    avail_count = len(evaluated_signals)
    total_count = len(evaluated_signals) + len(unknown_signals)

    coverage_str = f"{avail_count}/{total_count}"
    confidence_tier, _ = calculate_confidence(avail_count, total_count)
    classification_tier = classify_trust_score(final_trust_score, available_signals=avail_count)

    explanation = (
        f"Website Trust Score of {final_trust_score}/100 ({classification_tier}) computed from "
        f"{avail_count} of {total_count} available security signals. "
        f"Gained +{pos_pts} points from positive security configurations and lost -{neg_pts} points from security warnings."
    )

    return TrustScoreResult(
        score=final_trust_score,
        classification=classification_tier,
        confidence=confidence_tier,
        evidence_coverage=coverage_str,
        available_signals_count=avail_count,
        total_signals_count=total_count,
        positive_points=pos_pts,
        negative_points=neg_pts,
        signals=[s.to_dict() for s in evaluated_signals],
        unknown_signals=[s.to_dict() for s in unknown_signals],
        explanation=explanation,
        disclaimer=TRUST_DISCLAIMER,
    )


# ==============================================================================
# IP Risk Score Evaluation
# ==============================================================================

def evaluate_ip_risk(
    ip_intel: Optional[Union[IPIntelligence, IPIntelligenceResult]],
    geolocation_available: bool = True,
) -> IPRiskResult:
    """
    Evaluate deterministic 0–100 IP Risk Score using verified infrastructure signals.

    Principles:
    - Base ambient Internet risk: 5 (normal infrastructure is NOT 0 risk).
    - Anonymizers (Tor, Proxy, VPN) add risk points (+).
    - Datacenter hosting adds small analytical points (+10). Datacenter is NOT classified as malicious.
    - Verified CDN edge presence provides modest mitigation (-5).
    - Unknown/missing data is treated neutrally (0 points) and documented.
    - Output is strictly clamped between 0 and 100.
    """
    base_risk = 5
    evaluated_signals: List[ScoringSignal] = []
    neutral_signals: List[ScoringSignal] = []
    unknown_signals: List[ScoringSignal] = []

    # Handle null / empty IP intelligence input gracefully
    if ip_intel is None:
        unknown_sig = ScoringSignal(
            name="IP Intelligence",
            status="Unknown",
            points=0,
            reason="No IP infrastructure intelligence data was available.",
            source="Infrastructure Engine",
            is_available=False,
        )
        return IPRiskResult(
            score=base_risk,
            classification=RISK_TIER_LOW,
            confidence=CONFIDENCE_UNKNOWN,
            evidence_coverage="0/5",
            available_signals_count=0,
            total_signals_count=5,
            risk_points=0,
            mitigation_points=0,
            signals=[],
            neutral_signals=[],
            unknown_signals=[unknown_sig.to_dict()],
            explanation="Assessment limited: IP intelligence data was not available.",
        )

    # Normalize fields across IPIntelligence and IPIntelligenceResult
    is_tor = getattr(ip_intel, "is_tor", False)
    tor_status = getattr(ip_intel, "tor_status", "Detected" if is_tor else "Not Detected")
    
    is_proxy = getattr(ip_intel, "is_proxy", False)
    proxy_status = getattr(ip_intel, "proxy_status", "Detected" if is_proxy else "Not Detected")
    
    is_vpn = getattr(ip_intel, "is_vpn", False)
    vpn_status = getattr(ip_intel, "vpn_status", "Detected" if is_vpn else "Not Detected")

    is_datacenter = getattr(ip_intel, "is_datacenter", False)
    infra_type = getattr(ip_intel, "infrastructure_type", "Unknown")
    datacenter_status = getattr(ip_intel, "datacenter_status", "Detected" if is_datacenter else "Not Detected")

    # --------------------------------------------------------------------------
    # Signal 1: Tor Anonymous Exit Node
    # --------------------------------------------------------------------------
    if is_tor or str(tor_status).lower() == "detected":
        evaluated_signals.append(ScoringSignal(
            name="Tor Exit Node",
            status="Detected",
            points=65,
            reason="IP address is an active Tor anonymous relay exit node, frequently associated with high anonymization.",
            source="Anonymizer Heuristics",
            is_available=True,
        ))
    elif str(tor_status).lower() in ["not detected", "not_detected"]:
        neutral_signals.append(ScoringSignal(
            name="Tor Exit Node",
            status="Not Detected",
            points=0,
            reason="No Tor anonymous exit node indicators observed.",
            source="Anonymizer Heuristics",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="Tor Exit Node",
            status="Unknown",
            points=0,
            reason="Tor exit node verification unavailable.",
            source="Anonymizer Heuristics",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 2: Commercial / Open Proxy Gateway
    # --------------------------------------------------------------------------
    if is_proxy or str(proxy_status).lower() == "detected":
        evaluated_signals.append(ScoringSignal(
            name="Proxy Gateway",
            status="Detected",
            points=25,
            reason="IP address operates as a public or commercial proxy server.",
            source="Anonymizer Heuristics",
            is_available=True,
        ))
    elif str(proxy_status).lower() in ["not detected", "not_detected"]:
        neutral_signals.append(ScoringSignal(
            name="Proxy Gateway",
            status="Not Detected",
            points=0,
            reason="No public or commercial proxy server indicators observed.",
            source="Anonymizer Heuristics",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="Proxy Gateway",
            status="Unknown",
            points=0,
            reason="Proxy gateway status could not be determined.",
            source="Anonymizer Heuristics",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 3: Commercial VPN Exit Gateway
    # --------------------------------------------------------------------------
    if is_vpn or str(vpn_status).lower() == "detected":
        evaluated_signals.append(ScoringSignal(
            name="Commercial VPN",
            status="Detected",
            points=20,
            reason="IP address is associated with a commercial VPN exit service.",
            source="Anonymizer Heuristics",
            is_available=True,
        ))
    elif str(vpn_status).lower() in ["not detected", "not_detected"]:
        neutral_signals.append(ScoringSignal(
            name="Commercial VPN",
            status="Not Detected",
            points=0,
            reason="No commercial VPN service indicators observed.",
            source="Anonymizer Heuristics",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="Commercial VPN",
            status="Unknown",
            points=0,
            reason="Commercial VPN status could not be determined.",
            source="Anonymizer Heuristics",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 4: Datacenter / Cloud Hosting Facility
    # --------------------------------------------------------------------------
    dc_detected = is_datacenter or str(datacenter_status).lower() == "detected" or (infra_type == "Cloud Hosting" and str(datacenter_status).lower() not in ["not detected", "not_detected"])
    if dc_detected:
        evaluated_signals.append(ScoringSignal(
            name="Datacenter Hosting",
            status="Detected",
            points=10,
            reason="IP resides in a commercial datacenter or cloud facility rather than residential subscriber infrastructure.",
            source="Infrastructure Classification",
            is_available=True,
        ))
    elif str(datacenter_status).lower() in ["not detected", "not_detected"]:
        neutral_signals.append(ScoringSignal(
            name="Datacenter Hosting",
            status="Not Detected",
            points=0,
            reason="IP belongs to standard consumer ISP, residential, or institutional network.",
            source="Infrastructure Classification",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="Datacenter Hosting",
            status="Unknown",
            points=0,
            reason="Datacenter status could not be classified.",
            source="Infrastructure Classification",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Signal 5: Infrastructure Class Context (CDN Mitigation)
    # --------------------------------------------------------------------------
    if infra_type == "CDN / Edge Hub":
        evaluated_signals.append(ScoringSignal(
            name="Edge Hub Context",
            status="Active CDN",
            points=-5,
            reason="Major CDN edge node architecture dampens raw endpoint exposure risks.",
            source="Infrastructure Classification",
            is_available=True,
        ))
    elif infra_type in ["Enterprise Network", "Commercial ISP", "Cloud Hosting"]:
        neutral_signals.append(ScoringSignal(
            name="Infrastructure Context",
            status=infra_type,
            points=0,
            reason=f"Standard network context classified as {infra_type}.",
            source="Infrastructure Classification",
            is_available=True,
        ))
    else:
        unknown_signals.append(ScoringSignal(
            name="Infrastructure Context",
            status="Unknown",
            points=0,
            reason="Infrastructure context unclassified.",
            source="Infrastructure Classification",
            is_available=False,
        ))

    # --------------------------------------------------------------------------
    # Summation & Boundary Normalization
    # --------------------------------------------------------------------------
    risk_pts = sum(s.points for s in evaluated_signals if s.points > 0)
    mitigation_pts = sum(abs(s.points) for s in evaluated_signals if s.points < 0)

    calculated_risk = base_risk + risk_pts - mitigation_pts
    final_risk_score = max(0, min(100, calculated_risk))

    avail_count = len(evaluated_signals) + len(neutral_signals)
    total_count = avail_count + len(unknown_signals)

    coverage_str = f"{avail_count}/{total_count}"
    penalty = 0.15 if not geolocation_available else 0.0
    confidence_tier, _ = calculate_confidence(avail_count, total_count, penalty=penalty)
    classification_tier = classify_ip_risk_score(final_risk_score, available_signals=avail_count)

    explanation = (
        f"IP Risk Score of {final_risk_score}/100 ({classification_tier}) computed from "
        f"{avail_count} of {total_count} available infrastructure signals. "
        f"Observed +{risk_pts} risk points with {mitigation_pts} point mitigation."
    )

    all_signals_output = [s.to_dict() for s in evaluated_signals]

    return IPRiskResult(
        score=final_risk_score,
        classification=classification_tier,
        confidence=confidence_tier,
        evidence_coverage=coverage_str,
        available_signals_count=avail_count,
        total_signals_count=total_count,
        risk_points=risk_pts,
        mitigation_points=mitigation_pts,
        signals=all_signals_output,
        neutral_signals=[s.to_dict() for s in neutral_signals],
        unknown_signals=[s.to_dict() for s in unknown_signals],
        explanation=explanation,
        disclaimer=IP_RISK_DISCLAIMER,
    )


# ==============================================================================
# Unified Authoritative Scoring Function
# ==============================================================================

def evaluate_trust_and_risk(
    security: Optional[Union[SecurityInfo, WebsiteSecurityResult]],
    ip_intel: Optional[Union[IPIntelligence, IPIntelligenceResult]],
    geolocation_available: bool = True,
) -> RiskScore:
    """
    Compute explainable Website Trust Score (0–100) and IP Risk Score (0–100).
    Maintains 100% backward compatibility with existing IP PULSE pipelines and consumers.

    Args:
    - security: SecurityInfo or WebsiteSecurityResult instance
    - ip_intel: IPIntelligence or IPIntelligenceResult instance
    - geolocation_available: bool flag indicating whether geolocation was resolved

    Returns:
    - RiskScore instance with both backward-compatible fields and rich Phase 17 structures.
    """
    trust_res = evaluate_website_trust(security)
    risk_res = evaluate_ip_risk(ip_intel, geolocation_available=geolocation_available)

    # Legacy Factor Attribution String Lists
    positive_factors: List[str] = [
        f"{s['name']}: {s['status']} (+{s['points']})"
        for s in trust_res.signals if s.get("points", 0) > 0
    ]
    if any(s.get("points", 0) < 0 for s in risk_res.signals):
        positive_factors.append("CDN Edge Node Infrastructure (-5 Risk)")

    risk_factors: List[str] = [
        f"{s['name']}: {s['status']} ({s['points']} points)"
        for s in trust_res.signals if s.get("points", 0) < 0
    ] + [
        f"{s['name']}: {s['status']} (+{s['points']} Risk)"
        for s in risk_res.signals if s.get("points", 0) > 0
    ]

    # Legacy Categorical Risk Level
    if risk_res.score <= 20:
        legacy_risk_level = "Low"
    elif risk_res.score <= 45:
        legacy_risk_level = "Moderate"
    elif risk_res.score <= 70:
        legacy_risk_level = "High"
    else:
        legacy_risk_level = "Critical"

    # Legacy Float Confidence Score (0.0 to 1.0)
    conf_map = {
        CONFIDENCE_HIGH: 1.0,
        CONFIDENCE_MEDIUM: 0.75,
        CONFIDENCE_LOW: 0.50,
        CONFIDENCE_UNKNOWN: 0.25,
    }
    legacy_conf_score = conf_map.get(trust_res.confidence, 0.75)
    if not geolocation_available:
        legacy_conf_score = max(0.25, round(legacy_conf_score - 0.2, 2))

    return RiskScore(
        trust_score=trust_res.score,
        risk_score=risk_res.score,
        risk_level=legacy_risk_level,
        risk_category=risk_res.classification,
        confidence_score=legacy_conf_score,
        confidence_rating=trust_res.confidence,
        positive_factors=positive_factors,
        risk_factors=risk_factors,
        trust=trust_res,
        ip_risk=risk_res,
        disclaimer=UNIFIED_DISCLAIMER,
    )

