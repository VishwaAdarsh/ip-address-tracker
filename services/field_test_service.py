"""
Field-Test Orchestration Service for IP Address Tracker & Geolocation Tool.

Phase 19: 50-Site Intelligence Field Study Upgrade.
Implements the Manual-First 50-Site Intelligence Field Study Methodology:
- Curates an empirical research cohort of up to 50 website observations.
- Decoupled from general routine history lookups in lookup_history.
- Strict duplicate rejection based on normalized domain (google.com == https://google.com/).
- Stores 26 structured research attributes (Identity, Geolocation, Network, Security, Scoring, Metadata).
- Unknown data remains explicitly "Unknown" (neutral handling).
- Provides dynamic research summary calculations (sample size, HTTPS adoption, average trust, average risk, infrastructure mode).
- Preserves optional controlled automatic completion for remaining needed observations when N < 50.
- Exports formal 50-observation field dataset to data/field_test/field_test_results.csv.
"""
import csv
import logging
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

from config.settings import BASE_DIR
from database.db import (
    get_field_observation_by_domain,
    get_field_observation_by_id,
    get_field_observations,
    get_lookup_history,
    init_db,
    migrate_historical_to_field_study,
    save_field_observation,
)
from database.models import FieldObservation, LookupRecord
from services.lookup_service import LookupResult, LookupStatus, perform_lookup

logger = logging.getLogger(__name__)

# Complete 26-Attribute + Response Telemetry Field CSV Header Definitions (Phase 19)
FIELD_TEST_HEADERS = [
    "test_id",
    "domain",
    "category",
    "resolved_ip",
    "ip_version",
    "country",
    "country_code",
    "region",
    "city",
    "latitude",
    "longitude",
    "geolocation_confidence",
    "organization",
    "isp",
    "asn",
    "network_type",
    "infrastructure_type",
    "https_status",
    "tls_status",
    "vpn_status",
    "proxy_status",
    "tor_status",
    "website_trust_score",
    "website_trust_classification",
    "ip_risk_score",
    "ip_risk_classification",
    "score_confidence",
    "evidence_coverage",
    "dns_response_time_ms",
    "api_response_time_ms",
    "total_response_time_ms",
    "overall_status",
    "observed_at",
    "error_message",
]


def get_default_websites_path() -> Path:
    """Return default path to websites.csv dataset."""
    return BASE_DIR / "data" / "field_test" / "websites.csv"


def get_default_output_path() -> Path:
    """Return default path to output field_test_results.csv file."""
    path = BASE_DIR / "data" / "field_test" / "field_test_results.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def normalize_field_domain(domain_or_url: str) -> str:
    """
    Normalize domain or URL for consistent field-study identification & duplicate detection.

    Strips scheme, trailing slashes, paths, ports, whitespace, and lowercases.
    e.g.:
    - 'https://google.com/' -> 'google.com'
    - 'http://GOOGLE.COM'  -> 'google.com'
    - 'google.com:443'     -> 'google.com'
    - 'sub.example.com/a'  -> 'sub.example.com'
    """
    if not domain_or_url or not isinstance(domain_or_url, str):
        return ""

    raw = domain_or_url.strip()

    # Prepend scheme if missing so urlparse handles netloc properly
    if "://" not in raw:
        candidate = "http://" + raw
    else:
        candidate = raw

    try:
        parsed = urlparse(candidate)
        netloc = parsed.netloc or parsed.path
        if ":" in netloc:
            netloc = netloc.split(":", 1)[0]
        clean = netloc.strip("./ ").lower()
        return clean if clean else raw.lower().strip()
    except Exception:
        clean = raw
        if "://" in clean:
            clean = clean.split("://", 1)[1]
        clean = clean.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
        if ":" in clean:
            clean = clean.split(":", 1)[0]
        return clean.strip().lower()


def validate_observation(
    obs: Union[FieldObservation, Dict[str, Any], LookupResult]
) -> Tuple[bool, str]:
    """
    Define and enforce what counts as a valid observation for the 50-site research study.

    Requirements:
    1. Valid non-empty target domain.
    2. Successful / meaningful IP resolution (not empty, 'Unknown', or 'N/A').
    3. Valid observation timestamp.
    4. Not an INVALID_INPUT status.
    """
    if isinstance(obs, FieldObservation):
        domain = obs.domain
        ip = obs.resolved_ip
        ts = obs.observed_at
        status = obs.observation_status
    elif isinstance(obs, dict):
        domain = obs.get("domain") or obs.get("input_value")
        ip = obs.get("resolved_ip") or obs.get("ip_address")
        ts = obs.get("observed_at") or obs.get("timestamp")
        status = obs.get("observation_status") or obs.get("status")
    elif isinstance(obs, LookupResult):
        domain = obs.normalized_input if obs.input_type == "DOMAIN" else obs.input
        ip = obs.selected_ip
        ts = obs.timestamp
        status = (
            obs.overall_status.value
            if hasattr(obs.overall_status, "value")
            else str(obs.overall_status)
        )
    else:
        return False, "Unsupported observation object."

    norm_domain = normalize_field_domain(domain)
    if not norm_domain:
        return False, "Observation invalid: target domain is missing or malformed."

    if not ip or ip in ("Unknown", "N/A", "None", ""):
        return False, "Observation invalid: domain must resolve to a valid IP address."

    if not ts:
        return False, "Observation invalid: observation timestamp is missing."

    if status == "INVALID_INPUT":
        return False, "Observation invalid: target failed input validation."

    return True, "Valid observation."


def load_test_websites(
    csv_path: Optional[Union[str, Path]] = None
) -> List[Dict[str, str]]:
    """
    Load and validate the predefined 50-website dataset CSV file.

    Returns:
    - List of dicts with keys: 'test_id', 'domain', 'category'
    """
    target_path = Path(csv_path) if csv_path else get_default_websites_path()

    if not target_path.exists() or not target_path.is_file():
        raise FileNotFoundError(f"Website dataset CSV not found at: {target_path}")

    websites: List[Dict[str, str]] = []
    seen_ids: Set[str] = set()
    seen_domains: Set[str] = set()

    with open(target_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_id = str(row.get("test_id", "")).strip()
            domain = normalize_field_domain(str(row.get("domain", "")).strip())
            category = str(row.get("category", "")).strip()

            if not test_id or not domain or not category:
                raise ValueError(f"Malformed row in website dataset: {row}")

            if test_id in seen_ids:
                raise ValueError(f"Duplicate test_id in dataset: {test_id}")
            seen_ids.add(test_id)

            if domain in seen_domains:
                raise ValueError(f"Duplicate domain in dataset: {domain}")
            seen_domains.add(domain)

            websites.append(
                {"test_id": test_id, "domain": domain, "category": category}
            )

    return websites


def add_field_observation(
    target: str,
    db_path: Optional[Union[str, Path]] = None,
    category: Optional[str] = None,
    lookup_res: Optional[LookupResult] = None,
) -> Tuple[bool, str, Optional[FieldObservation]]:
    """
    Add an intentionally selected website observation to the 50-Site Field Study.

    Workflow:
    1. Normalize domain string.
    2. Check duplicate policy: same normalized domain can count only once.
    3. Execute full intelligence analysis if lookup_res not provided.
    4. Validate observation data (meaningful IP, valid timestamp).
    5. Construct FieldObservation model with 26 research attributes.
    6. Persist to field_study_observations in SQLite database.

    Returns:
    - (success: bool, message: str, observation: Optional[FieldObservation])
    """
    norm_dom = normalize_field_domain(target)
    if not norm_dom:
        return False, "Target domain is empty or invalid.", None

    init_db(db_path)

    # 1. Duplicate Policy Check
    existing_obs = get_field_observation_by_domain(norm_dom, db_path=db_path)
    if existing_obs:
        return (
            False,
            f"Domain '{norm_dom}' is already recorded in the 50-Site Field Study.",
            existing_obs,
        )

    # 2. Category mapping
    cat = category
    if not cat:
        try:
            websites = load_test_websites()
            cat_map = {w["domain"]: w["category"] for w in websites}
            cat = cat_map.get(norm_dom, "General Web")
        except Exception:
            cat = "General Web"

    # 3. Perform or use Lookup / Intelligence Scan
    if lookup_res is not None:
        if hasattr(lookup_res, "base_lookup"):
            base = lookup_res.base_lookup
            sec = getattr(lookup_res, "security", None)
            intel = getattr(lookup_res, "ip_intel", None)
            risk = getattr(lookup_res, "risk", None)
        else:
            base = lookup_res
            sec = None
            intel = None
            risk = None
    else:
        from services.risk_analysis_service import perform_full_intelligence_scan

        try:
            full_res = perform_full_intelligence_scan(
                norm_dom, save_to_db=True, db_path=db_path
            )
            base = full_res.base_lookup
            sec = full_res.security
            intel = full_res.ip_intel
            risk = full_res.risk
        except Exception as e:
            logger.error(f"Intelligence scan failed for {norm_dom}: {e}")
            base = perform_lookup(norm_dom, save_to_db=True, db_path=db_path)
            sec = None
            intel = None
            risk = None

    # 4. Observation Validation Rule
    is_valid, reason = validate_observation(base)
    if not is_valid:
        return False, reason, None

    # 5. Determine next test_id
    current_obs_list = get_field_observations(db_path=db_path)
    next_test_id = len(current_obs_list) + 1

    # 6. Assemble 26-attribute FieldObservation
    ip_val = base.selected_ip or "Unknown"
    ip_ver = base.ip_version or "IPv4"

    country = base.country if base.country and base.country != "N/A" else "Unknown"
    region = base.region if base.region and base.region != "N/A" else "Unknown"
    city = base.city if base.city and base.city != "N/A" else "Unknown"
    geo_conf = "HIGH" if (base.country and base.city and base.country != "N/A" and base.city != "N/A") else ("MEDIUM" if country != "Unknown" else "UNKNOWN")

    asn_val = base.asn if base.asn and base.asn != "N/A" else "Unknown"
    org_val = base.organization if base.organization and base.organization != "N/A" else "Unknown"
    isp_val = base.isp if base.isp and base.isp != "N/A" else "Unknown"
    net_type = getattr(intel, "network_type", "Unknown") if intel else "Unknown"
    infra_type = getattr(intel, "infrastructure_type", "Unknown") if intel else "Unknown"

    https_stat = "Unknown"
    tls_stat = "Unknown"
    if sec:
        https_stat = "Enabled" if getattr(sec, "https_enabled", False) else "Disabled"
        tls_stat = "Valid" if getattr(sec, "ssl_valid", getattr(sec, "certificate_valid", False)) else "Invalid"

    vpn_stat = getattr(intel, "vpn_status", "Unknown") if intel else "Unknown"
    proxy_stat = getattr(intel, "proxy_status", "Unknown") if intel else "Unknown"
    tor_stat = getattr(intel, "tor_status", "Unknown") if intel else "Unknown"

    trust_score = getattr(risk, "trust_score", None) if risk else None
    trust_class = "Unknown"
    risk_score = getattr(risk, "risk_score", None) if risk else None
    risk_class = "Unknown"
    score_conf = "Unknown"
    evidence_cov = 0.0

    if risk and hasattr(risk, "trust") and risk.trust:
        trust_score = float(risk.trust.score)
        trust_class = risk.trust.classification
        score_conf = risk.trust.confidence
        if hasattr(risk.trust, "available_signals_count") and hasattr(risk.trust, "total_signals_count") and risk.trust.total_signals_count > 0:
            evidence_cov = round(risk.trust.available_signals_count / risk.trust.total_signals_count, 2)
    elif trust_score is not None:
        trust_score = float(trust_score)
        trust_class = "LIKELY SAFE" if trust_score >= 80 else ("GENERALLY SAFE" if trust_score >= 60 else "REVIEW RECOMMENDED")

    if risk and hasattr(risk, "ip_risk") and risk.ip_risk:
        risk_score = float(risk.ip_risk.score)
        risk_class = risk.ip_risk.classification
    elif risk_score is not None:
        risk_score = float(risk_score)
        risk_class = "LOW RISK" if risk_score < 20 else ("MODERATE" if risk_score < 40 else "HIGH RISK")

    obs = FieldObservation(
        test_id=next_test_id,
        domain=norm_dom,
        category=cat or "General Web",
        resolved_ip=ip_val,
        ip_version=ip_ver,
        country=country,
        region=region,
        city=city,
        latitude=base.latitude,
        longitude=base.longitude,
        geolocation_confidence=geo_conf,
        asn=asn_val,
        organization=org_val,
        isp=isp_val,
        network_type=net_type,
        infrastructure_type=infra_type,
        https_status=https_stat,
        tls_status=tls_stat,
        vpn_status=vpn_stat,
        proxy_status=proxy_stat,
        tor_status=tor_stat,
        website_trust_score=trust_score,
        website_trust_classification=trust_class,
        ip_risk_score=risk_score,
        ip_risk_classification=risk_class,
        score_confidence=score_conf,
        evidence_coverage=evidence_cov,
        observation_status="RECORDED",
        observed_at=base.timestamp,
        raw_history_id=None,
        dns_response_time_ms=base.dns_response_time_ms,
        api_response_time_ms=base.api_response_time_ms,
        country_code=base.country_code or "N/A",
        timezone=base.timezone or "N/A",
        error_message=base.error_message,
    )

    saved_id = save_field_observation(obs, db_path=db_path)
    if saved_id is None:
        return (
            False,
            f"Failed to record '{norm_dom}' in Field Study database.",
            None,
        )

    obs.id = saved_id
    msg = f"Added '{norm_dom}' to Field Study ({next_test_id} / 50)."
    return True, msg, obs


def get_field_project_status(
    db_path: Optional[Union[str, Path]] = None,
    target_count: int = 50,
) -> Dict[str, Any]:
    """
    Evaluate the manual-first 50-site field study status from SQLite database.

    Calculates:
    - Current sample size (available_count) and progress percentage
    - Target (50) and remaining needed count
    - Progress status ('TARGET_REACHED' or 'INCOMPLETE')
    - Real, dynamically computed research summary metrics:
      - sample_size
      - https_adoption_pct
      - avg_trust_score
      - avg_risk_score
      - most_common_infrastructure
      - vpn_count, proxy_count, tor_count
      - data quality metrics

    Returns:
    - Dict with status, summary, unique_records, records
    """
    init_db(db_path)

    # Automatically backfill from history if field_study_observations is completely empty
    migrate_historical_to_field_study(db_path=db_path)

    records = get_field_observations(db_path=db_path)
    available_count = len(records)
    remaining = max(target_count - available_count, 0)
    pct = round((available_count / target_count) * 100, 1) if target_count > 0 else 0.0
    status_str = "TARGET_REACHED" if available_count >= target_count else "INCOMPLETE"

    # Category mapping
    category_map: Dict[str, str] = {}
    try:
        websites = load_test_websites()
        category_map = {w["domain"]: w["category"] for w in websites}
    except Exception:
        pass

    # Dynamically compute Research Summary Metrics
    if available_count > 0:
        https_enabled_count = sum(
            1 for r in records if r.https_status in ("Enabled", "Active", "Valid", "SUCCESS")
        )
        https_pct = round((https_enabled_count / available_count) * 100, 1)

        valid_trust = [r.website_trust_score for r in records if r.website_trust_score is not None]
        avg_trust = round(sum(valid_trust) / len(valid_trust), 1) if valid_trust else 0.0

        valid_risk = [r.ip_risk_score for r in records if r.ip_risk_score is not None]
        avg_risk = round(sum(valid_risk) / len(valid_risk), 1) if valid_risk else 0.0

        infra_counts: Dict[str, int] = {}
        for r in records:
            inf = r.infrastructure_type or "Unknown"
            if inf != "Unknown":
                infra_counts[inf] = infra_counts.get(inf, 0) + 1

        if infra_counts:
            most_common_infra = max(infra_counts.items(), key=lambda x: x[1])[0]
        else:
            most_common_infra = "Unknown"

        vpn_c = sum(1 for r in records if r.vpn_status == "Detected")
        proxy_c = sum(1 for r in records if r.proxy_status == "Detected")
        tor_c = sum(1 for r in records if r.tor_status == "Detected")
    else:
        https_pct = 0.0
        avg_trust = 0.0
        avg_risk = 0.0
        most_common_infra = "Unknown"
        vpn_c = 0
        proxy_c = 0
        tor_c = 0

    summary = {
        "sample_size": available_count,
        "target_size": target_count,
        "https_adoption_pct": https_pct,
        "avg_trust_score": avg_trust,
        "avg_risk_score": avg_risk,
        "most_common_infrastructure": most_common_infra,
        "vpn_count": vpn_c,
        "proxy_count": proxy_c,
        "tor_count": tor_c,
        "valid_observations_count": available_count,
        "incomplete_observations_count": 0,
        "target_reached": available_count >= target_count,
    }

    return {
        "available_count": available_count,
        "manual_count": available_count,
        "auto_count": 0,
        "target": target_count,
        "remaining": remaining,
        "progress_percentage": pct,
        "status": status_str,
        "unique_records": records,
        "category_map": category_map,
        "summary": summary,
        "records": [r.to_dict() for r in records],
    }


def export_field_dataset_from_history(
    db_path: Optional[Union[str, Path]] = None,
    output_csv_path: Optional[Union[str, Path]] = None,
    target_count: int = 50,
) -> List[Dict[str, Any]]:
    """
    Export formal 50-site field study dataset CSV.

    Selects up to target_count valid observations from field_study_observations.
    Writes full 26-attribute research data to data/field_test/field_test_results.csv.
    """
    status = get_field_project_status(db_path=db_path, target_count=target_count)
    records = status["unique_records"][:target_count]

    out_path = Path(output_csv_path) if output_csv_path else get_default_output_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results_data: List[Dict[str, Any]] = []

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_TEST_HEADERS)
        writer.writeheader()

        for idx, rec in enumerate(records, start=1):
            row_data = {
                "test_id": str(rec.test_id or idx),
                "domain": rec.domain,
                "category": rec.category or "General Web",
                "resolved_ip": rec.resolved_ip or "",
                "ip_version": rec.ip_version or "IPv4",
                "country": rec.country or "Unknown",
                "country_code": rec.country_code or "N/A",
                "region": rec.region or "Unknown",
                "city": rec.city or "Unknown",
                "latitude": rec.latitude if rec.latitude is not None else "",
                "longitude": rec.longitude if rec.longitude is not None else "",
                "geolocation_confidence": rec.geolocation_confidence or "Unknown",
                "organization": rec.organization or "Unknown",
                "isp": rec.isp or "Unknown",
                "asn": rec.asn or "Unknown",
                "network_type": rec.network_type or "Unknown",
                "infrastructure_type": rec.infrastructure_type or "Unknown",
                "https_status": rec.https_status or "Unknown",
                "tls_status": rec.tls_status or "Unknown",
                "vpn_status": rec.vpn_status or "Unknown",
                "proxy_status": rec.proxy_status or "Unknown",
                "tor_status": rec.tor_status or "Unknown",
                "website_trust_score": rec.website_trust_score if rec.website_trust_score is not None else "",
                "website_trust_classification": rec.website_trust_classification or "Unknown",
                "ip_risk_score": rec.ip_risk_score if rec.ip_risk_score is not None else "",
                "ip_risk_classification": rec.ip_risk_classification or "Unknown",
                "score_confidence": rec.score_confidence or "Unknown",
                "evidence_coverage": rec.evidence_coverage if rec.evidence_coverage is not None else "",
                "dns_response_time_ms": rec.dns_response_time_ms,
                "api_response_time_ms": rec.api_response_time_ms,
                "total_response_time_ms": round(
                    rec.dns_response_time_ms + rec.api_response_time_ms, 2
                ),
                "overall_status": rec.observation_status or "RECORDED",
                "observed_at": rec.observed_at,
                "error_message": rec.error_message or "",
            }

            writer.writerow(row_data)
            results_data.append(row_data)

    return results_data


def run_automatic_completion(
    db_path: Optional[Union[str, Path]] = None,
    output_csv_path: Optional[Union[str, Path]] = None,
    progress_callback: Optional[Callable[[int, int, str, Any], None]] = None,
    stop_event: Optional[threading.Event] = None,
    delay_seconds: float = 0.5,
    target_count: int = 50,
) -> List[Dict[str, Any]]:
    """
    Execute controlled automatic completion ONLY for remaining observations needed to reach 50.

    Rules:
    1. Checks current field project status in field_study_observations.
    2. Calculates remaining = max(50 - available, 0).
    3. Never executes more lookups than remaining.
    4. Executes scan and adds directly to 50-site Field Study via add_field_observation().
    5. Saves entries to both SQLite History and field_study_observations.
    6. Exports updated field dataset to CSV.
    """
    status = get_field_project_status(db_path=db_path, target_count=target_count)
    remaining_needed = status["remaining"]

    if remaining_needed <= 0:
        logger.info("Field project target of 50 observations already reached.")
        return export_field_dataset_from_history(
            db_path=db_path, output_csv_path=output_csv_path, target_count=target_count
        )

    # Load predefined websites dataset
    all_websites = load_test_websites()
    existing_domains = {r.domain.lower() for r in status["unique_records"]}

    # Filter websites not yet recorded in Field Study
    missing_websites = [
        w for w in all_websites if normalize_field_domain(w["domain"]) not in existing_domains
    ]

    # Select exactly remaining_needed websites
    websites_to_run = missing_websites[:remaining_needed]
    total_to_run = len(websites_to_run)

    for idx, site in enumerate(websites_to_run, start=1):
        if stop_event and stop_event.is_set():
            logger.info("Automatic completion stopped early by user request.")
            break

        domain = site["domain"]
        category = site.get("category", "General Web")

        # Execute addition to Field Study
        success, msg, obs = add_field_observation(
            target=domain, db_path=db_path, category=category
        )

        if progress_callback:
            progress_callback(idx, total_to_run, domain, obs)

        if delay_seconds > 0 and idx < total_to_run:
            time.sleep(delay_seconds)

    # Export updated field dataset
    return export_field_dataset_from_history(
        db_path=db_path, output_csv_path=output_csv_path, target_count=target_count
    )


# Backward-compatibility alias
def run_field_test(
    websites: Optional[List[Dict[str, str]]] = None,
    output_csv_path: Optional[Union[str, Path]] = None,
    progress_callback: Optional[Callable[[int, int, str, Any], None]] = None,
    stop_event: Optional[threading.Event] = None,
    delay_seconds: float = 0.5,
) -> List[Dict[str, Any]]:
    """Legacy runner alias wrapping automatic completion."""
    return run_automatic_completion(
        output_csv_path=output_csv_path,
        progress_callback=progress_callback,
        stop_event=stop_event,
        delay_seconds=delay_seconds,
    )
