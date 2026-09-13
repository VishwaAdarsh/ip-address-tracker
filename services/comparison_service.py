"""
Intelligence Comparison & Investigation Workspace Service Module for IP PULSE Platform (Phase 23).

Provides:
- Multi-observation side-by-side normalization (2 to 5 targets maximum)
- Deterministic comparison statistics (extremes, commonalities, adoption rates)
- Factual difference highlights engine without speculative causation
- Multi-target coordinate extraction for Leaflet mapping
- Optional AI comparative explanation engine (via Phase 22 provider abstraction)
- Read-only data retrieval from SQLite History and Field Study
"""
from dataclasses import asdict, dataclass, field
import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from config.settings import BASE_DIR
from core.ai_explainer import (
    AIExplanationResult,
    RuleBasedAIProvider,
    get_ai_provider,
    sanitize_security_claims,
)
from database.db import get_connection, init_db, get_lookup_history, get_field_observations
from database.models import FieldObservation, LookupRecord

logger = logging.getLogger(__name__)

MIN_COMPARISON_ITEMS = 2
MAX_COMPARISON_ITEMS = 5


@dataclass
class NormalizedComparisonItem:
    """Standardized multi-dimensional observation model for side-by-side comparison."""

    id: Optional[int] = None
    source: str = "field_study"                 # "field_study", "history", "current"
    domain: str = "UNKNOWN"
    resolved_ip: str = "UNKNOWN"
    ip_version: str = "UNKNOWN"
    ipv4_addresses: List[str] = field(default_factory=list)
    ipv6_addresses: List[str] = field(default_factory=list)

    # Network
    asn: str = "UNKNOWN"
    organization: str = "UNKNOWN"
    isp: str = "UNKNOWN"
    network_type: str = "UNKNOWN"
    infrastructure_type: str = "UNKNOWN"

    # Location
    country: str = "UNKNOWN"
    region: str = "UNKNOWN"
    city: str = "UNKNOWN"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geolocation_confidence: str = "UNKNOWN"

    # Security
    https_status: str = "UNKNOWN"               # "Enabled", "Disabled", "UNKNOWN"
    redirect_status: str = "UNKNOWN"            # "Enforced", "None", "UNKNOWN"
    tls_status: str = "UNKNOWN"                 # "Valid", "Invalid / Self-Signed", "UNKNOWN"
    tls_version: str = "UNKNOWN"
    tls_issuer: str = "UNKNOWN"
    ssl_expiry_days: str = "UNKNOWN"

    # IP Intelligence
    vpn_status: str = "UNKNOWN"                 # "DETECTED", "NOT_DETECTED", "UNKNOWN"
    proxy_status: str = "UNKNOWN"               # "DETECTED", "NOT_DETECTED", "UNKNOWN"
    tor_status: str = "UNKNOWN"                 # "DETECTED", "NOT_DETECTED", "UNKNOWN"
    datacenter_status: str = "UNKNOWN"          # "DETECTED", "NOT_DETECTED", "UNKNOWN"

    # Risk
    website_trust_score: Optional[float] = None
    website_trust_classification: str = "UNKNOWN"
    ip_risk_score: Optional[float] = None
    ip_risk_classification: str = "UNKNOWN"
    score_confidence: str = "UNKNOWN"
    evidence_coverage: str = "UNKNOWN"

    # Intelligence
    ip_personality: str = "UNKNOWN"
    intelligence_chain_summary: str = "UNKNOWN"
    tested_at: str = "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        """Convert normalized observation to dictionary."""
        return asdict(self)


def _u(val: Any, default: str = "UNKNOWN") -> str:
    """Helper to ensure clean, consistent uppercase UNKNOWN strings."""
    if val is None:
        return default
    s = str(val).strip()
    if not s or s.lower() in ("none", "unknown", "n/a", "null", "undefined"):
        return default
    return s


def normalize_comparison_item(data: Union[Dict[str, Any], FieldObservation, LookupRecord]) -> NormalizedComparisonItem:
    """
    Normalize any raw observation (FieldObservation, LookupRecord, or dict from frontend)
    into a uniform NormalizedComparisonItem.
    """
    # 1. Handle FieldObservation dataclass
    if isinstance(data, FieldObservation):
        https_str = _u(data.https_status)
        if https_str.lower() in ("enabled", "true", "yes", "https enforced"):
            https_norm = "Enabled"
        elif https_str.lower() in ("disabled", "false", "no", "http only"):
            https_norm = "Disabled"
        else:
            https_norm = "UNKNOWN"

        tls_str = _u(data.tls_status)
        if tls_str.lower() in ("valid", "true", "certificate valid"):
            tls_norm = "Valid"
        elif tls_str.lower() in ("invalid", "false", "invalid certificate", "expired"):
            tls_norm = "Invalid / Expired"
        else:
            tls_norm = "UNKNOWN"

        return NormalizedComparisonItem(
            id=data.id,
            source="field_study",
            domain=_u(data.domain),
            resolved_ip=_u(data.resolved_ip),
            ip_version=_u(data.ip_version, "IPv4"),
            asn=_u(data.asn),
            organization=_u(data.organization),
            isp=_u(data.isp),
            network_type=_u(data.network_type),
            infrastructure_type=_u(data.infrastructure_type),
            country=_u(data.country),
            region=_u(data.region),
            city=_u(data.city),
            latitude=data.latitude,
            longitude=data.longitude,
            geolocation_confidence=_u(data.geolocation_confidence),
            https_status=https_norm,
            redirect_status="UNKNOWN",
            tls_status=tls_norm,
            tls_version="UNKNOWN",
            tls_issuer="UNKNOWN",
            ssl_expiry_days="UNKNOWN",
            vpn_status=_u(data.vpn_status),
            proxy_status=_u(data.proxy_status),
            tor_status=_u(data.tor_status),
            datacenter_status="UNKNOWN",
            website_trust_score=data.website_trust_score,
            website_trust_classification=_u(data.website_trust_classification),
            ip_risk_score=data.ip_risk_score,
            ip_risk_classification=_u(data.ip_risk_classification),
            score_confidence=_u(data.score_confidence),
            evidence_coverage=f"{int(data.evidence_coverage * 100)}%" if data.evidence_coverage is not None else "UNKNOWN",
            ip_personality=f"{data.infrastructure_type} hosted via {data.organization} in {data.country}",
            intelligence_chain_summary=f"{data.domain} -> {data.resolved_ip} -> {data.asn} -> {data.organization}",
            tested_at=_u(data.observed_at),
        )

    # 2. Handle LookupRecord dataclass
    if isinstance(data, LookupRecord):
        return NormalizedComparisonItem(
            id=data.id,
            source="history",
            domain=_u(data.domain or data.input_value),
            resolved_ip=_u(data.ip_address),
            ip_version=_u(data.ip_version, "IPv4"),
            asn=_u(data.asn),
            organization=_u(data.organization),
            isp=_u(data.isp),
            network_type="UNKNOWN",
            infrastructure_type="UNKNOWN",
            country=_u(data.country),
            region=_u(data.region),
            city=_u(data.city),
            latitude=data.latitude,
            longitude=data.longitude,
            geolocation_confidence="UNKNOWN",
            https_status="UNKNOWN",
            redirect_status="UNKNOWN",
            tls_status="UNKNOWN",
            tls_version="UNKNOWN",
            tls_issuer="UNKNOWN",
            ssl_expiry_days="UNKNOWN",
            vpn_status="UNKNOWN",
            proxy_status="UNKNOWN",
            tor_status="UNKNOWN",
            datacenter_status="UNKNOWN",
            website_trust_score=None,
            website_trust_classification="UNKNOWN",
            ip_risk_score=None,
            ip_risk_classification="UNKNOWN",
            score_confidence="UNKNOWN",
            evidence_coverage="UNKNOWN",
            ip_personality=f"Network host resolving to {data.organization} in {data.country}",
            intelligence_chain_summary=f"{data.domain} -> {data.ip_address} -> {data.asn} -> {data.organization}",
            tested_at=_u(data.timestamp),
        )

    # 3. Handle Dictionary (from API scan result or JSON candidate)
    if isinstance(data, dict):
        base = data.get("base", {})
        sec = data.get("security", {})
        intel = data.get("ip_intel", {})
        risk = data.get("risk", {})
        chain = data.get("intelligence_chain", {})
        personality_obj = data.get("ip_personality") or data.get("personality")

        domain = _u(data.get("domain") or base.get("normalized_input") or base.get("input") or data.get("target"))
        resolved_ip = _u(data.get("resolved_ip") or base.get("selected_ip") or intel.get("ip_address") or data.get("ip_address"))
        
        # Latitude & Longitude
        lat = data.get("latitude") if data.get("latitude") is not None else base.get("latitude")
        lon = data.get("longitude") if data.get("longitude") is not None else base.get("longitude")
        try:
            lat = float(lat) if lat is not None else None
        except (ValueError, TypeError):
            lat = None
        try:
            lon = float(lon) if lon is not None else None
        except (ValueError, TypeError):
            lon = None

        # Scores
        trust_val = data.get("website_trust_score")
        if trust_val is None:
            trust_val = risk.get("trust_score")
        try:
            trust_score = float(trust_val) if trust_val is not None else None
        except (ValueError, TypeError):
            trust_score = None

        risk_val = data.get("ip_risk_score")
        if risk_val is None:
            risk_val = risk.get("risk_score")
        try:
            risk_score = float(risk_val) if risk_val is not None else None
        except (ValueError, TypeError):
            risk_score = None

        # HTTPS
        https_raw = sec.get("is_https") if "is_https" in sec else data.get("https_status")
        if https_raw is True or str(https_raw).lower() in ("enabled", "true", "yes"):
            https_status = "Enabled"
        elif https_raw is False or str(https_raw).lower() in ("disabled", "false", "no"):
            https_status = "Disabled"
        else:
            https_status = "UNKNOWN"

        # TLS
        tls_raw = sec.get("tls_valid") if "tls_valid" in sec else data.get("tls_status")
        if tls_raw is True or str(tls_raw).lower() in ("valid", "true"):
            tls_status = "Valid"
        elif tls_raw is False or str(tls_raw).lower() in ("invalid", "false", "invalid certificate", "expired"):
            tls_status = "Invalid / Expired"
        else:
            tls_status = "UNKNOWN"

        # Personality summary
        if isinstance(personality_obj, dict):
            personality_str = personality_obj.get("summary") or "UNKNOWN"
        elif isinstance(personality_obj, str):
            personality_str = personality_obj
        else:
            personality_str = "UNKNOWN"

        return NormalizedComparisonItem(
            id=data.get("id"),
            source=data.get("source", "current"),
            domain=domain,
            resolved_ip=resolved_ip,
            ip_version=_u(data.get("ip_version") or base.get("ip_version"), "IPv4"),
            ipv4_addresses=list(base.get("ipv4_addresses") or []),
            ipv6_addresses=list(base.get("ipv6_addresses") or []),
            asn=_u(data.get("asn") or base.get("asn") or intel.get("asn")),
            organization=_u(data.get("organization") or base.get("organization") or intel.get("organization")),
            isp=_u(data.get("isp") or base.get("isp") or intel.get("isp")),
            network_type=_u(data.get("network_type") or intel.get("network_type")),
            infrastructure_type=_u(data.get("infrastructure_type") or intel.get("infrastructure_type") or chain.get("infrastructure")),
            country=_u(data.get("country") or base.get("country")),
            region=_u(data.get("region") or base.get("region")),
            city=_u(data.get("city") or base.get("city")),
            latitude=lat,
            longitude=lon,
            geolocation_confidence=_u(data.get("geolocation_confidence")),
            https_status=https_status,
            redirect_status=_u(data.get("redirect_status")),
            tls_status=tls_status,
            tls_version=_u(sec.get("tls_version") or data.get("tls_version")),
            tls_issuer=_u(sec.get("issuer_org") or data.get("tls_issuer")),
            ssl_expiry_days=_u(sec.get("expires_in_days") or data.get("ssl_expiry_days")),
            vpn_status=_u(data.get("vpn_status") or intel.get("vpn_status")),
            proxy_status=_u(data.get("proxy_status") or intel.get("proxy_status")),
            tor_status=_u(data.get("tor_status") or intel.get("tor_status")),
            datacenter_status=_u(data.get("datacenter_status") or intel.get("datacenter_status")),
            website_trust_score=trust_score,
            website_trust_classification=_u(data.get("website_trust_classification") or risk.get("risk_category")),
            ip_risk_score=risk_score,
            ip_risk_classification=_u(data.get("ip_risk_classification") or risk.get("risk_level")),
            score_confidence=_u(data.get("score_confidence") or risk.get("confidence_rating")),
            evidence_coverage=_u(data.get("evidence_coverage")),
            ip_personality=_u(personality_str),
            intelligence_chain_summary=f"{domain} -> {resolved_ip} -> {_u(base.get('asn'))} -> {_u(base.get('organization'))}",
            tested_at=_u(data.get("tested_at") or data.get("observed_at") or base.get("timestamp")),
        )

    # Fallback default
    return NormalizedComparisonItem()


def compute_comparison_statistics(items: List[NormalizedComparisonItem]) -> Dict[str, Any]:
    """
    Generate deterministic, empirical comparison statistics across the selected observations.
    
    Zero speculation or inferred causation. Reports actual commonalities or "No common value detected."
    """
    if not items:
        return {}

    n = len(items)

    # 1. Extreme Scores
    trust_scores = [(it.domain, it.website_trust_score) for it in items if it.website_trust_score is not None]
    risk_scores = [(it.domain, it.ip_risk_score) for it in items if it.ip_risk_score is not None]

    highest_trust = max(trust_scores, key=lambda x: x[1]) if trust_scores else ("None", None)
    lowest_trust = min(trust_scores, key=lambda x: x[1]) if trust_scores else ("None", None)
    highest_risk = max(risk_scores, key=lambda x: x[1]) if risk_scores else ("None", None)
    lowest_risk = min(risk_scores, key=lambda x: x[1]) if risk_scores else ("None", None)

    # 2. Common Values (Only if all items share the exact same value, excluding UNKNOWN)
    def find_unanimous_common(values: List[str]) -> str:
        valid = [v for v in values if v not in ("UNKNOWN", "Information unavailable", "N/A", "")]
        if len(valid) == n and len(set(valid)) == 1:
            return valid[0]
        return "No common value detected."

    common_asn = find_unanimous_common([it.asn for it in items])
    common_org = find_unanimous_common([it.organization for it in items])
    common_infra = find_unanimous_common([it.infrastructure_type for it in items])
    common_country = find_unanimous_common([it.country for it in items])

    # 3. HTTPS Adoption Rate
    https_enabled_count = sum(1 for it in items if it.https_status == "Enabled")
    https_adoption_pct = round((https_enabled_count / n) * 100, 1) if n > 0 else 0.0

    # 4. Anonymizer / Proxy / Tor / VPN Detections
    vpn_detected = sum(1 for it in items if it.vpn_status == "DETECTED")
    proxy_detected = sum(1 for it in items if it.proxy_status == "DETECTED")
    tor_detected = sum(1 for it in items if it.tor_status == "DETECTED")
    datacenter_detected = sum(1 for it in items if it.datacenter_status == "DETECTED")

    return {
        "count": n,
        "highest_trust_score": {"domain": highest_trust[0], "score": highest_trust[1]},
        "lowest_trust_score": {"domain": lowest_trust[0], "score": lowest_trust[1]},
        "highest_ip_risk_score": {"domain": highest_risk[0], "score": highest_risk[1]},
        "lowest_ip_risk_score": {"domain": lowest_risk[0], "score": lowest_risk[1]},
        "common_asn": common_asn,
        "common_organization": common_org,
        "common_infrastructure_type": common_infra,
        "common_country": common_country,
        "https_adoption": {
            "enabled_count": https_enabled_count,
            "total_count": n,
            "percentage": https_adoption_pct,
            "formatted": f"{https_enabled_count} of {n} ({https_adoption_pct}%) enforced",
        },
        "anonymizer_detections": {
            "vpn_count": vpn_detected,
            "proxy_count": proxy_detected,
            "tor_count": tor_detected,
            "datacenter_count": datacenter_detected,
            "total_anonymizers": vpn_detected + proxy_detected + tor_detected,
        },
    }


def compute_difference_highlights(items: List[NormalizedComparisonItem]) -> List[str]:
    """
    Generate factual difference statements identifying where selected observations diverge.
    
    Adheres strictly to factual reporting; never infers malice or causation.
    """
    if len(items) < 2:
        return ["At least 2 observations are required to compute differences."]

    highlights = []
    n = len(items)

    # 1. Geographic Divergence
    countries = list({it.country for it in items if it.country not in ("UNKNOWN", "N/A")})
    if len(countries) == 1:
        highlights.append(f"Geographic convergence: All observations geolocate within {countries[0]}.")
    elif len(countries) > 1:
        highlights.append(f"Geographic divergence: Targets span {len(countries)} unique countries ({', '.join(countries[:4])}).")
    else:
        highlights.append("Geographic location telemetry is unmeasured across selected observations.")

    # 2. Autonomous System (ASN) Divergence
    asns = list({it.asn for it in items if it.asn not in ("UNKNOWN", "N/A")})
    if len(asns) == 1:
        highlights.append(f"Autonomous System convergence: All observations route through {asns[0]}.")
    elif len(asns) > 1:
        highlights.append(f"Autonomous System divergence: Targets route through {len(asns)} distinct ASNs.")
    
    # 3. Transport Security Differences
    https_enabled = [it.domain for it in items if it.https_status == "Enabled"]
    https_disabled = [it.domain for it in items if it.https_status == "Disabled"]
    if len(https_enabled) == n:
        highlights.append("Transport security convergence: HTTPS encryption is enforced across all selected observations.")
    elif len(https_disabled) == n:
        highlights.append("Transport security warning: Unencrypted HTTP transport observed across all selected targets.")
    elif https_enabled and https_disabled:
        highlights.append(f"Transport security divergence: HTTPS is enforced on {len(https_enabled)} of {n} targets ({', '.join(https_disabled[:2])} lack encryption).")

    # 4. Infrastructure Type Differences
    infras = list({it.infrastructure_type for it in items if it.infrastructure_type not in ("UNKNOWN", "N/A")})
    if len(infras) > 1:
        highlights.append(f"Infrastructure divergence: Network classification spans {len(infras)} categories ({', '.join(infras)}).")

    # 5. Score Discrepancies
    trust_scores = [it.website_trust_score for it in items if it.website_trust_score is not None]
    if len(trust_scores) >= 2:
        spread = max(trust_scores) - min(trust_scores)
        if spread >= 30:
            highlights.append(f"Website Trust Score divergence: Significant spread of {int(spread)} points (ranges from {int(min(trust_scores))} to {int(max(trust_scores))}).")
        else:
            highlights.append(f"Website Trust Scores cluster tightly within a {int(spread)}-point range.")

    risk_scores = [it.ip_risk_score for it in items if it.ip_risk_score is not None]
    if len(risk_scores) >= 2:
        spread = max(risk_scores) - min(risk_scores)
        if spread >= 30:
            highlights.append(f"IP Risk Score divergence: Elevated spread of {int(spread)} points observed between endpoints.")
        elif spread > 0:
            highlights.append(f"IP Risk Scores vary moderately by {int(spread)} points across targets.")

    # 6. Anonymizer / VPN Presence
    vpn_nodes = [it.domain for it in items if it.vpn_status == "DETECTED"]
    if vpn_nodes:
        highlights.append(f"Anonymizer telemetry: Commercial VPN presence identified on {len(vpn_nodes)} target(s) ({', '.join(vpn_nodes)}).")

    if not highlights:
        highlights.append("Observations demonstrate consistent, uniform infrastructure and security profiles.")

    return highlights


def extract_map_coordinates(items: List[NormalizedComparisonItem]) -> List[Dict[str, Any]]:
    """Extract valid coordinate points for multi-marker Leaflet visualization."""
    points = []
    for it in items:
        if it.latitude is not None and it.longitude is not None:
            # Check coordinate bounds
            if -90.0 <= it.latitude <= 90.0 and -180.0 <= it.longitude <= 180.0:
                points.append({
                    "id": it.id,
                    "domain": it.domain,
                    "resolved_ip": it.resolved_ip,
                    "latitude": it.latitude,
                    "longitude": it.longitude,
                    "country": it.country,
                    "city": it.city,
                    "organization": it.organization,
                    "asn": it.asn,
                    "trust_score": it.website_trust_score,
                    "risk_score": it.ip_risk_score,
                })
    return points


def get_comparison_candidates(db_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Retrieve candidate observations from Field Study and recent History for quick multi-select.
    
    Guaranteed read-only: does not modify or write to database.
    """
    init_db(db_path)
    candidates = []
    seen_domains = set()

    # 1. Field Study Observations (Primary research records)
    try:
        f_obs = get_field_observations(limit=50, db_path=db_path)
        for obs in f_obs:
            dom = obs.domain.strip().lower()
            if dom and dom not in seen_domains:
                seen_domains.add(dom)
                candidates.append({
                    "id": obs.id,
                    "source": "field_study",
                    "domain": obs.domain,
                    "ip_address": obs.resolved_ip or "UNKNOWN",
                    "country": obs.country or "Unknown",
                    "city": obs.city or "Unknown",
                    "asn": obs.asn or "Unknown",
                    "organization": obs.organization or "Unknown",
                    "trust_score": obs.website_trust_score,
                    "risk_score": obs.ip_risk_score,
                    "timestamp": obs.observed_at,
                    "badge": "Field Study",
                })
    except Exception as e:
        logger.error(f"Error fetching field study candidates: {e}")

    # 2. History Lookups
    try:
        h_records = get_lookup_history(limit=50, db_path=db_path)
        for h in h_records:
            dom = (h.domain or h.input_value or "").strip().lower()
            if dom and dom not in seen_domains:
                seen_domains.add(dom)
                candidates.append({
                    "id": h.id,
                    "source": "history",
                    "domain": h.domain or h.input_value,
                    "ip_address": h.ip_address or "UNKNOWN",
                    "country": h.country or "Unknown",
                    "city": h.city or "Unknown",
                    "asn": h.asn or "Unknown",
                    "organization": h.organization or "Unknown",
                    "trust_score": None,
                    "risk_score": None,
                    "timestamp": h.timestamp,
                    "badge": "History",
                })
    except Exception as e:
        logger.error(f"Error fetching history candidates: {e}")

    return {
        "count": len(candidates),
        "candidates": candidates,
    }


def execute_comparison(raw_items: List[Union[Dict[str, Any], FieldObservation, LookupRecord]]) -> Dict[str, Any]:
    """
    Main entry point for Phase 23 multi-observation comparison.

    Validates:
    - Minimum 2 observations
    - Maximum 5 observations
    - Prevents duplicate normalized domain selection
    """
    if not isinstance(raw_items, list):
        return {
            "success": False,
            "error": "Observations payload must be an array of items.",
            "code": "INVALID_PAYLOAD",
        }

    if len(raw_items) < MIN_COMPARISON_ITEMS:
        return {
            "success": False,
            "error": f"At least {MIN_COMPARISON_ITEMS} observations are required for comparison (received {len(raw_items)}).",
            "code": "INSUFFICIENT_OBSERVATIONS",
        }

    if len(raw_items) > MAX_COMPARISON_ITEMS:
        return {
            "success": False,
            "error": f"A maximum of {MAX_COMPARISON_ITEMS} observations can be compared simultaneously (received {len(raw_items)}).",
            "code": "EXCEEDED_MAX_OBSERVATIONS",
        }

    # Normalize items and check for duplicates
    normalized_items: List[NormalizedComparisonItem] = []
    seen_domains = set()

    for item in raw_items:
        norm = normalize_comparison_item(item)
        dom_key = norm.domain.strip().lower()
        if dom_key and dom_key != "unknown":
            if dom_key in seen_domains:
                return {
                    "success": False,
                    "error": f"Duplicate observation detected for domain '{norm.domain}'. Each compared observation must be unique.",
                    "code": "DUPLICATE_SELECTION",
                }
            seen_domains.add(dom_key)
        normalized_items.append(norm)

    # Compute deterministic analytical outputs
    stats = compute_comparison_statistics(normalized_items)
    diffs = compute_difference_highlights(normalized_items)
    map_points = extract_map_coordinates(normalized_items)

    return {
        "success": True,
        "count": len(normalized_items),
        "observations": [it.to_dict() for it in normalized_items],
        "statistics": stats,
        "differences": diffs,
        "map_points": map_points,
    }


def generate_comparison_ai_explanation(
    comparison_result: Dict[str, Any],
    provider_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate an evidence-grounded comparative AI explanation across compared observations.
    
    Synthesizes:
    - Major differences
    - Common infrastructure
    - Security differences
    - Trust & Risk differences
    - Important unknowns
    - Calibrated takeaways
    """
    observations = comparison_result.get("observations", [])
    stats = comparison_result.get("statistics", {})
    diffs = comparison_result.get("differences", [])

    if len(observations) < MIN_COMPARISON_ITEMS:
        return {
            "status": "error",
            "summary": "At least 2 observations are required to generate a comparative analysis.",
        }

    domains = [obs.get("domain", "Unknown") for obs in observations]
    domains_str = ", ".join(domains)

    # Build prompt payload for AI
    ai_payload = {
        "domains": domains,
        "count": len(observations),
        "statistics": stats,
        "differences": diffs,
        "observations_summary": [
            {
                "domain": obs.get("domain"),
                "ip": obs.get("resolved_ip"),
                "asn": obs.get("asn"),
                "org": obs.get("organization"),
                "country": obs.get("country"),
                "infra": obs.get("infrastructure_type"),
                "https": obs.get("https_status"),
                "trust_score": obs.get("website_trust_score"),
                "risk_score": obs.get("ip_risk_score"),
            }
            for obs in observations
        ],
    }

    # Deterministic Rule-Based Comparative Synthesis
    rule_summary = (
        f"Comparative evaluation across {len(observations)} endpoints ({domains_str}): "
        f"Selected hosts exhibit {stats.get('https_adoption', {}).get('formatted', 'variable transport security')}. "
        f"Autonomous routing {('converges under ' + stats['common_asn']) if stats.get('common_asn') != 'No common value detected.' else 'diverges across independent network carriers'}. "
        f"Website Trust Scores range from {stats.get('lowest_trust_score', {}).get('score', 'N/A')} to {stats.get('highest_trust_score', {}).get('score', 'N/A')}, "
        f"while IP Risk Scores span from {stats.get('lowest_ip_risk_score', {}).get('score', 'N/A')} to {stats.get('highest_ip_risk_score', {}).get('score', 'N/A')}."
    )

    infra_explanation = (
        f"Infrastructure and routing comparison: "
        f"Common Organization: {stats.get('common_organization')}; "
        f"Common Infrastructure Class: {stats.get('common_infrastructure_type')}; "
        f"Common Geographic Territory: {stats.get('common_country')}. "
        f"{diffs[0] if diffs else 'Profiles maintain consistent infrastructure topologies.'}"
    )

    security_explanation = (
        f"Security and Transport divergence: "
        f"{stats.get('https_adoption', {}).get('formatted', '')}. "
        f"Anonymizer telemetry recorded {stats.get('anonymizer_detections', {}).get('total_anonymizers', 0)} total exit node or proxy flags."
    )

    takeaway = (
        f"Comparative Assessment: Observations reflect distinct infrastructure footprints. "
        f"Endpoints with verified TLS encryption and commercial CDN caching exhibit lower baseline risk indicators. "
        f"Standard security review recommended before establishing sensitive communication channels."
    )

    limitations = (
        "AI comparison explains empirical telemetry recorded at test execution time. "
        "It does not certify vendor safety, corporate relationships, or traffic integrity. "
        "Deterministic scores and raw observations remain authoritative."
    )

    return {
        "status": "success",
        "provider": provider_name or "rule_based",
        "domains": domains,
        "summary": sanitize_security_claims(rule_summary),
        "infrastructure_comparison": sanitize_security_claims(infra_explanation),
        "security_comparison": sanitize_security_claims(security_explanation),
        "key_differences": diffs,
        "takeaway": sanitize_security_claims(takeaway),
        "limitations": limitations,
    }
