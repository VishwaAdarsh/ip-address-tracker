"""
Analytics Service Module for IP PULSE Platform (Phase 20).

Provides deterministic, reproducible, and verifiable research analytics
derived strictly from empirical observations in SQLite field_study_observations:
1. Field Study Overview (sample size, valid vs failed, progress, remaining to 50)
2. Trust Score Statistical Analysis (min, mean, max, std dev, 5-bracket histogram, classifications)
3. IP Risk Statistical Analysis (min, mean, max, std dev, 5-bracket histogram, classifications)
4. Network & Infrastructure Distribution (IPv4/IPv6, Network Type, Cloud vs Traditional, ASNs, Orgs)
5. Security Analysis (HTTPS adoption, TLS validity, unknown handling)
6. Comparison Analytics (top/bottom trust, top/bottom risk, cloud vs other, flagged threats)
7. Research Insights Layer (deterministic factual statements with zero speculation)
8. Chart Data Payloads (structured JSON suitable for Stitch frontend visualization)
"""
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from database.db import get_field_observations, init_db
from database.models import FieldObservation

logger = logging.getLogger("ip_pulse.analytics_service")


def compute_field_study_analytics(
    db_path: Optional[Union[str, Path]] = None,
    target_count: int = 50,
) -> Dict[str, Any]:
    """
    Compute comprehensive research analytics across the 50-site Field Study dataset.

    Args:
    - db_path: Optional custom SQLite database path.
    - target_count: Study target quota (default: 50).

    Returns:
    - Dict with structured keys:
      overview, trust_analysis, risk_analysis, network_analysis,
      security_analysis, comparison_analytics, research_insights,
      chart_data, export_summary
    """
    init_db(db_path)
    records: List[FieldObservation] = get_field_observations(db_path=db_path)

    total_n = len(records)
    remaining_needed = max(target_count - total_n, 0)
    progress_pct = round((total_n / target_count) * 100, 1) if target_count > 0 else 0.0
    status_str = "TARGET_REACHED" if total_n >= target_count else "INCOMPLETE"

    # Separate valid vs invalid observations
    # A valid observation must resolve to an IP address and not have an INVALID_INPUT status
    valid_records: List[FieldObservation] = []
    invalid_records: List[FieldObservation] = []

    for r in records:
        ip = (r.resolved_ip or r.ip_address or "").strip()
        stat = (r.observation_status or r.status or "").strip()
        if stat == "INVALID_INPUT" or not ip or ip in ("Unknown", "N/A", "None"):
            invalid_records.append(r)
        else:
            valid_records.append(r)

    valid_n = len(valid_records)
    invalid_n = len(invalid_records)

    # If completely empty
    if total_n == 0:
        return _build_empty_analytics_response(target_count)

    # -------------------------------------------------------------------------
    # 1. Trust Score Statistics & Distribution (0-100 scale)
    # -------------------------------------------------------------------------
    trust_scores = [
        float(r.website_trust_score)
        for r in valid_records
        if r.website_trust_score is not None
    ]
    trust_stats = _compute_univariate_stats(trust_scores)
    trust_distribution = _compute_histogram_brackets(trust_scores)

    # Classifications
    trust_class_counts: Dict[str, int] = {}
    for r in valid_records:
        tc = r.website_trust_classification or "Unknown"
        trust_class_counts[tc] = trust_class_counts.get(tc, 0) + 1

    trust_classifications = [
        {"classification": k, "count": v, "pct": round((v / valid_n) * 100, 1)}
        for k, v in sorted(trust_class_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # -------------------------------------------------------------------------
    # 2. IP Risk Statistics & Distribution (0-100 scale)
    # -------------------------------------------------------------------------
    risk_scores = [
        float(r.ip_risk_score)
        for r in valid_records
        if r.ip_risk_score is not None
    ]
    risk_stats = _compute_univariate_stats(risk_scores)
    risk_distribution = _compute_histogram_brackets(risk_scores)

    risk_class_counts: Dict[str, int] = {}
    for r in valid_records:
        rc = r.ip_risk_classification or "Unknown"
        risk_class_counts[rc] = risk_class_counts.get(rc, 0) + 1

    risk_classifications = [
        {"classification": k, "count": v, "pct": round((v / valid_n) * 100, 1)}
        for k, v in sorted(risk_class_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    # -------------------------------------------------------------------------
    # 3. Security Analysis (HTTPS & TLS Validity)
    # -------------------------------------------------------------------------
    https_enabled_count = sum(
        1 for r in valid_records
        if r.https_status in ("Enabled", "Active", "Valid", "SUCCESS")
    )
    https_disabled_count = sum(
        1 for r in valid_records
        if r.https_status in ("Disabled", "Inactive", "Failed", "ERROR")
    )
    https_unknown_count = valid_n - (https_enabled_count + https_disabled_count)

    https_adoption_pct = round((https_enabled_count / valid_n) * 100, 1) if valid_n > 0 else 0.0
    https_disabled_pct = round((https_disabled_count / valid_n) * 100, 1) if valid_n > 0 else 0.0
    https_unknown_pct = round((https_unknown_count / valid_n) * 100, 1) if valid_n > 0 else 0.0

    tls_valid_count = sum(
        1 for r in valid_records
        if r.tls_status in ("Valid", "SUCCESS")
    )
    tls_invalid_count = sum(
        1 for r in valid_records
        if r.tls_status in ("Invalid", "Expired", "Self-Signed", "Failed")
    )
    tls_unknown_count = valid_n - (tls_valid_count + tls_invalid_count)
    tls_valid_pct = round((tls_valid_count / valid_n) * 100, 1) if valid_n > 0 else 0.0

    security_analysis = {
        "https_enabled_count": https_enabled_count,
        "https_enabled_pct": https_adoption_pct,
        "https_disabled_count": https_disabled_count,
        "https_disabled_pct": https_disabled_pct,
        "https_unknown_count": https_unknown_count,
        "https_unknown_pct": https_unknown_pct,
        "tls_valid_count": tls_valid_count,
        "tls_valid_pct": tls_valid_pct,
        "tls_invalid_count": tls_invalid_count,
        "tls_invalid_pct": round((tls_invalid_count / valid_n) * 100, 1) if valid_n > 0 else 0.0,
        "tls_unknown_count": tls_unknown_count,
        "tls_unknown_pct": round((tls_unknown_count / valid_n) * 100, 1) if valid_n > 0 else 0.0,
        "https_status": {
            "enabled": https_enabled_count,
            "disabled": https_disabled_count,
            "unknown": https_unknown_count,
            "adoption_pct": https_adoption_pct,
        },
        "tls_status": {
            "valid": tls_valid_count,
            "invalid_or_expired": tls_invalid_count,
            "unknown": tls_unknown_count,
            "valid_pct": tls_valid_pct,
        },
    }

    # -------------------------------------------------------------------------
    # 4. Network & Infrastructure Distribution
    # -------------------------------------------------------------------------
    ipv4_count = sum(1 for r in valid_records if "4" in (r.ip_version or "IPv4"))
    ipv6_count = sum(1 for r in valid_records if "6" in (r.ip_version or ""))
    unknown_ip_count = valid_n - (ipv4_count + ipv6_count)

    ipv4_pct = round((ipv4_count / valid_n) * 100, 1) if valid_n > 0 else 0.0
    ipv6_pct = round((ipv6_count / valid_n) * 100, 1) if valid_n > 0 else 0.0

    # Network types breakdown
    net_type_counts: Dict[str, int] = {}
    infra_type_counts: Dict[str, int] = {}
    for r in valid_records:
        nt = r.network_type or "Unknown"
        net_type_counts[nt] = net_type_counts.get(nt, 0) + 1

        it = r.infrastructure_type or "Unknown"
        infra_type_counts[it] = infra_type_counts.get(it, 0) + 1

    # Hosting vs Traditional
    cloud_dc_count = sum(
        v for k, v in infra_type_counts.items()
        if any(w in k.lower() for w in ("cloud", "datacenter", "hosting", "cdn", "vps"))
    )
    cloud_dc_pct = round((cloud_dc_count / valid_n) * 100, 1) if valid_n > 0 else 0.0
    unknown_infra_count = infra_type_counts.get("Unknown", 0)
    other_infra_count = max(valid_n - cloud_dc_count - unknown_infra_count, 0)
    other_infra_pct = round((other_infra_count / valid_n) * 100, 1) if valid_n > 0 else 0.0

    # Threat detections (VPN, Proxy, Tor)
    vpn_count = sum(1 for r in valid_records if r.vpn_status == "DETECTED")
    proxy_count = sum(1 for r in valid_records if r.proxy_status == "DETECTED")
    tor_count = sum(1 for r in valid_records if r.tor_status == "DETECTED")
    clean_threat_count = sum(
        1 for r in valid_records
        if r.vpn_status != "DETECTED" and r.proxy_status != "DETECTED" and r.tor_status != "DETECTED"
    )

    # Top ASNs & Organizations
    asn_counts: Dict[str, Dict[str, Any]] = {}
    for r in valid_records:
        asn = (r.asn or "Unknown").strip()
        if asn in ("Unknown", "N/A", ""):
            asn = "Unknown ASN"
        if asn not in asn_counts:
            asn_counts[asn] = {
                "asn": asn,
                "org": r.organization if r.organization and r.organization != "N/A" else (r.isp or "Unknown"),
                "count": 0,
            }
        asn_counts[asn]["count"] += 1

    top_asns = sorted(asn_counts.values(), key=lambda x: x["count"], reverse=True)[:6]
    for item in top_asns:
        item["pct"] = round((item["count"] / valid_n) * 100, 1) if valid_n > 0 else 0.0

    # Top Organizations
    org_counts: Dict[str, int] = {}
    for r in valid_records:
        org = (r.organization or r.isp or "Unknown").strip()
        if org in ("Unknown", "N/A", ""):
            continue
        org_counts[org] = org_counts.get(org, 0) + 1

    top_orgs = [
        {"organization": k, "count": v, "pct": round((v / valid_n) * 100, 1)}
        for k, v in sorted(org_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    ]

    # Top Countries
    country_counts: Dict[str, int] = {}
    for r in valid_records:
        c = (r.country or "Unknown").strip()
        if not c or c in ("N/A", ""):
            c = "Unknown"
        country_counts[c] = country_counts.get(c, 0) + 1

    top_countries = [
        {"country": k, "count": v, "pct": round((v / valid_n) * 100, 1)}
        for k, v in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    ]

    # Latency Telemetry
    dns_times = [
        float(r.dns_response_time_ms)
        for r in valid_records
        if r.dns_response_time_ms and r.dns_response_time_ms > 0
    ]
    api_times = [
        float(r.api_response_time_ms)
        for r in valid_records
        if r.api_response_time_ms and r.api_response_time_ms > 0
    ]
    avg_dns = round(sum(dns_times) / len(dns_times), 1) if dns_times else 0.0
    avg_api = round(sum(api_times) / len(api_times), 1) if api_times else 0.0

    network_analysis = {
        "ipv4_count": ipv4_count,
        "ipv4_pct": ipv4_pct,
        "ipv6_count": ipv6_count,
        "ipv6_pct": ipv6_pct,
        "unknown_ip_count": unknown_ip_count,
        "network_types": [
            {"type": k, "count": v, "pct": round((v / valid_n) * 100, 1)}
            for k, v in sorted(net_type_counts.items(), key=lambda x: x[1], reverse=True)
        ],
        "infrastructure_types": [
            {"type": k, "count": v, "pct": round((v / valid_n) * 100, 1)}
            for k, v in sorted(infra_type_counts.items(), key=lambda x: x[1], reverse=True)
        ],
        "cloud_vs_traditional": {
            "cloud_datacenter_count": cloud_dc_count,
            "cloud_datacenter_pct": cloud_dc_pct,
            "traditional_other_count": other_infra_count,
            "traditional_other_pct": other_infra_pct,
            "unknown_count": unknown_infra_count,
        },
        "threat_detections": {
            "vpn_count": vpn_count,
            "proxy_count": proxy_count,
            "tor_count": tor_count,
            "clean_count": clean_threat_count,
        },
        "top_asns": top_asns,
        "top_organizations": top_orgs,
        "top_countries": top_countries,
        "mean_dns_latency_ms": avg_dns,
        "mean_api_latency_ms": avg_api,
        # Structured nested dictionaries for clean UI access
        "ip_versions": {
            "ipv4": ipv4_count,
            "ipv6": ipv6_count,
            "unknown": unknown_ip_count,
            "ipv4_pct": ipv4_pct,
            "ipv6_pct": ipv6_pct,
        },
        "infrastructure": {
            "cloud_datacenter": cloud_dc_count,
            "traditional_other": other_infra_count,
            "unknown": unknown_infra_count,
            "cloud_pct": cloud_dc_pct,
        },
        "threat_indicators": {
            "vpn": vpn_count,
            "proxy": proxy_count,
            "tor": tor_count,
            "clean": clean_threat_count,
            "any_threat_flag": vpn_count + proxy_count + tor_count,
        },
        "query_latency": {
            "mean_dns_ms": avg_dns,
            "mean_api_ms": avg_api,
        },
    }

    # -------------------------------------------------------------------------
    # 5. Comparison Analytics (Top / Bottom, Grouped Comparisons)
    # -------------------------------------------------------------------------
    # Top & Bottom Trust Sites
    sites_with_trust = [
        r for r in valid_records if r.website_trust_score is not None
    ]
    sites_sorted_by_trust = sorted(
        sites_with_trust, key=lambda x: float(x.website_trust_score or 0), reverse=True
    )
    highest_trust_sites = [
        _serialize_site_summary(r, score_key="trust")
        for r in sites_sorted_by_trust[:5]
    ]
    lowest_trust_sites = [
        _serialize_site_summary(r, score_key="trust")
        for r in reversed(sites_sorted_by_trust[-5:])
    ]

    # Top & Bottom Risk Sites
    sites_with_risk = [
        r for r in valid_records if r.ip_risk_score is not None
    ]
    sites_sorted_by_risk = sorted(
        sites_with_risk, key=lambda x: float(x.ip_risk_score or 0), reverse=True
    )
    highest_risk_sites = [
        _serialize_site_summary(r, score_key="risk")
        for r in sites_sorted_by_risk[:5]
    ]
    lowest_risk_sites = [
        _serialize_site_summary(r, score_key="risk")
        for r in reversed(sites_sorted_by_risk[-5:])
    ]

    # Comparative Group Means: HTTPS vs Non-HTTPS
    https_records = [
        r for r in valid_records
        if r.https_status in ("Enabled", "Active", "Valid", "SUCCESS")
    ]
    non_https_records = [
        r for r in valid_records
        if r.https_status not in ("Enabled", "Active", "Valid", "SUCCESS")
    ]

    https_trust_vals = [float(r.website_trust_score) for r in https_records if r.website_trust_score is not None]
    non_https_trust_vals = [float(r.website_trust_score) for r in non_https_records if r.website_trust_score is not None]

    # Cloud vs Other Risk Comparison
    cloud_records = [
        r for r in valid_records
        if any(w in (r.infrastructure_type or "").lower() for w in ("cloud", "datacenter", "hosting", "cdn"))
    ]
    other_records = [
        r for r in valid_records
        if not any(w in (r.infrastructure_type or "").lower() for w in ("cloud", "datacenter", "hosting", "cdn"))
    ]

    cloud_risk_vals = [float(r.ip_risk_score) for r in cloud_records if r.ip_risk_score is not None]
    other_risk_vals = [float(r.ip_risk_score) for r in other_records if r.ip_risk_score is not None]

    # Flagged Threat Entities
    flagged_threat_sites = [
        {
            "domain": r.domain,
            "ip": r.resolved_ip or r.ip_address or "Unknown",
            "vpn": r.vpn_status,
            "proxy": r.proxy_status,
            "tor": r.tor_status,
            "infrastructure": r.infrastructure_type or "Unknown",
            "risk_score": r.ip_risk_score,
            "risk_classification": r.ip_risk_classification or "Unknown",
        }
        for r in valid_records
        if r.vpn_status == "DETECTED" or r.proxy_status == "DETECTED" or r.tor_status == "DETECTED"
    ]

    comparison_analytics = {
        "highest_trust_sites": highest_trust_sites,
        "lowest_trust_sites": lowest_trust_sites,
        "highest_risk_sites": highest_risk_sites,
        "lowest_risk_sites": lowest_risk_sites,
        "https_vs_non_https": {
            "https_sample_count": len(https_records),
            "https_avg_trust": round(sum(https_trust_vals) / len(https_trust_vals), 1) if https_trust_vals else None,
            "non_https_sample_count": len(non_https_records),
            "non_https_avg_trust": round(sum(non_https_trust_vals) / len(non_https_trust_vals), 1) if non_https_trust_vals else None,
        },
        "cloud_vs_other_infrastructure": {
            "cloud_sample_count": len(cloud_records),
            "cloud_avg_risk": round(sum(cloud_risk_vals) / len(cloud_risk_vals), 1) if cloud_risk_vals else None,
            "other_sample_count": len(other_records),
            "other_avg_risk": round(sum(other_risk_vals) / len(other_risk_vals), 1) if other_risk_vals else None,
        },
        "flagged_threat_entities": flagged_threat_sites,
    }

    # -------------------------------------------------------------------------
    # 6. Research Insights Layer (Deterministic & Factual)
    # -------------------------------------------------------------------------
    insights: List[Dict[str, Any]] = []

    # Insight 1: Sample Quota State
    if total_n >= target_count:
        insights.append({
            "id": "insight-quota",
            "category": "reputation",
            "title": "Study Quota Completed",
            "finding": f"Study target completed: exactly {total_n} standardized website observations have been collected and verified.",
            "text": f"Study target completed: exactly {total_n} standardized website observations have been collected and verified.",
            "metric": f"{total_n} / {target_count} ({progress_pct}%)",
            "type": "success",
        })
    else:
        insights.append({
            "id": "insight-quota",
            "category": "reputation",
            "title": "Sample Quota Progress",
            "finding": f"Field study in progress: {total_n} of {target_count} target observations recorded ({remaining_needed} remaining to fulfill quota).",
            "text": f"Field study in progress: {total_n} of {target_count} target observations recorded ({remaining_needed} remaining to fulfill quota).",
            "metric": f"{total_n} / {target_count} ({progress_pct}%)",
            "type": "info",
        })

    # Insight 2: Transport Layer HTTPS Security
    insights.append({
        "id": "insight-security",
        "category": "security",
        "title": "Transport Layer HTTPS Adoption",
        "finding": f"{https_enabled_count} of {valid_n} valid observed websites ({https_adoption_pct}%) operate with active HTTPS transport encryption.",
        "text": f"{https_enabled_count} of {valid_n} valid observed websites ({https_adoption_pct}%) operate with active HTTPS transport encryption.",
        "metric": f"{https_adoption_pct}% Encrypted",
        "type": "positive" if (https_adoption_pct or 0) >= 80 else "warning",
    })

    # Insight 3: Infrastructure Classification
    insights.append({
        "id": "insight-infrastructure",
        "category": "infrastructure",
        "title": "Cloud & Datacenter Concentration",
        "finding": f"{cloud_dc_count} of {valid_n} observations ({cloud_dc_pct}%) were classified as large-scale Cloud or Datacenter infrastructure.",
        "text": f"{cloud_dc_count} of {valid_n} observations ({cloud_dc_pct}%) were classified as large-scale Cloud or Datacenter infrastructure.",
        "metric": f"{cloud_dc_pct}% Cloud / DC",
        "type": "info",
    })

    # Insight 4: Scoring Central Tendency
    mean_trust_str = f"{trust_stats['mean']}/100" if trust_stats["mean"] is not None else "N/A"
    mean_risk_str = f"{risk_stats['mean']}/100" if risk_stats["mean"] is not None else "N/A"
    insights.append({
        "id": "insight-scoring",
        "category": "reputation",
        "title": "Cohort Mean Scores",
        "finding": f"Cohort mean Website Trust Score is {mean_trust_str}, paired with an average IP Risk Score of {mean_risk_str}.",
        "text": f"Cohort mean Website Trust Score is {mean_trust_str}, paired with an average IP Risk Score of {mean_risk_str}.",
        "metric": f"Trust {mean_trust_str} | Risk {mean_risk_str}",
        "type": "info",
    })

    # Insight 5: Anonymization & Egress Nodes
    total_threats = vpn_count + proxy_count + tor_count
    if total_threats == 0:
        insights.append({
            "id": "insight-anonymization",
            "category": "network",
            "title": "Anonymization Telemetry",
            "finding": "Zero anonymization egress indicators (VPN, Proxy, or Tor exit relays) were detected across the observed endpoints.",
            "text": "Zero anonymization egress indicators (VPN, Proxy, or Tor exit relays) were detected across the observed endpoints.",
            "metric": "0 Detections",
            "type": "positive",
        })
    else:
        insights.append({
            "id": "insight-anonymization",
            "category": "network",
            "title": "Anonymization Telemetry",
            "finding": f"Anonymization egress indicators were detected on {len(flagged_threat_sites)} endpoints (VPN: {vpn_count}, Proxy: {proxy_count}, Tor: {tor_count}).",
            "text": f"Anonymization egress indicators were detected on {len(flagged_threat_sites)} endpoints (VPN: {vpn_count}, Proxy: {proxy_count}, Tor: {tor_count}).",
            "metric": f"{total_threats} Flagged",
            "type": "warning",
        })

    # Insight 6: Autonomous Systems
    if top_asns:
        leading_asn = top_asns[0]
        insights.append({
            "id": "insight-asn",
            "category": "network",
            "title": "Leading Autonomous System",
            "finding": f"Network routing was led by {leading_asn['asn']} ({leading_asn['org']}), routing {leading_asn['count']} endpoints ({leading_asn['pct']}% of cohort).",
            "text": f"Network routing was led by {leading_asn['asn']} ({leading_asn['org']}), routing {leading_asn['count']} endpoints ({leading_asn['pct']}% of cohort).",
            "metric": f"{leading_asn['asn']} ({leading_asn['pct']}%)",
            "type": "info",
        })

    # -------------------------------------------------------------------------
    # 7. Chart Data Payloads (Pre-formatted for Stitch Frontend Charts)
    # -------------------------------------------------------------------------
    chart_data = {
        "trust_histogram": trust_distribution,
        "risk_histogram": risk_distribution,
        "security_breakdown": [
            {"label": "HTTPS Enabled", "count": https_enabled_count, "pct": https_adoption_pct, "color": "#00f0ff"},
            {"label": "HTTPS Disabled", "count": https_disabled_count, "pct": https_disabled_pct, "color": "#ff0055"},
            {"label": "Unknown / N/A", "count": https_unknown_count, "pct": https_unknown_pct, "color": "#8892b0"},
        ],
        "protocol_breakdown": [
            {"label": "IPv4", "count": ipv4_count, "pct": ipv4_pct, "color": "#00f0ff"},
            {"label": "IPv6", "count": ipv6_count, "pct": ipv6_pct, "color": "#7928ca"},
        ],
        "infrastructure_breakdown": network_analysis["infrastructure_types"][:5],
        "top_countries": top_countries,
        "top_asns": top_asns,
    }

    # High-level overview card data
    overview = {
        "total_observations": total_n,
        "valid_observations": valid_n,
        "invalid_observations": invalid_n,
        "target": target_count,
        "sample_target": target_count,
        "remaining": remaining_needed,
        "remaining_to_target": remaining_needed,
        "target_reached": total_n >= target_count,
        "progress_percentage": progress_pct,
        "collection_progress_pct": progress_pct,
        "status": status_str,
        "study_status": status_str,
        "https_adoption_pct": https_adoption_pct,
        "ipv4_pct": ipv4_pct,
        "ipv6_pct": ipv6_pct,
        "vpn_detections": vpn_count,
        "proxy_detections": proxy_count,
        "tor_detections": tor_count,
        "cloud_datacenter_pct": cloud_dc_pct,
        "avg_trust_score": trust_stats["mean"],
        "mean_trust_score": trust_stats["mean"],
        "avg_risk_score": risk_stats["mean"],
        "mean_risk_score": risk_stats["mean"],
    }

    return {
        "success": True,
        "insufficient_data": False,
        "overview": overview,
        "trust_analysis": {
            "statistics": trust_stats,
            "distribution": trust_distribution,
            "histogram": trust_distribution,
            "classifications": trust_classifications,
            "min": trust_stats["min"],
            "max": trust_stats["max"],
            "mean": trust_stats["mean"],
            "std_dev": trust_stats["std_dev"],
            "count": trust_stats["count"],
        },
        "risk_analysis": {
            "statistics": risk_stats,
            "distribution": risk_distribution,
            "histogram": risk_distribution,
            "classifications": risk_classifications,
            "min": risk_stats["min"],
            "max": risk_stats["max"],
            "mean": risk_stats["mean"],
            "std_dev": risk_stats["std_dev"],
            "count": risk_stats["count"],
        },
        "security_analysis": security_analysis,
        "network_analysis": network_analysis,
        "comparison_analytics": comparison_analytics,
        "research_insights": insights,
        "chart_data": chart_data,
        "export_summary": {
            "sample_size": total_n,
            "target_quota": target_count,
            "status": status_str,
            "completeness_pct": progress_pct,
            "timestamp": valid_records[-1].observed_at if valid_records else None,
        },
    }


def _compute_univariate_stats(values: List[float]) -> Dict[str, Optional[float]]:
    """Compute mean, min, max, std dev for a list of floats."""
    if not values:
        return {"mean": None, "min": None, "max": None, "std_dev": None, "count": 0}

    n = len(values)
    mean_val = round(sum(values) / n, 1)
    min_val = round(min(values), 1)
    max_val = round(max(values), 1)

    variance = sum((x - mean_val) ** 2 for x in values) / n if n > 1 else 0.0
    std_dev = round(math.sqrt(variance), 1)

    return {
        "mean": mean_val,
        "min": min_val,
        "max": max_val,
        "std_dev": std_dev,
        "count": n,
    }


def _compute_histogram_brackets(values: List[float]) -> List[Dict[str, Any]]:
    """Partition continuous 0-100 scores into 5 standardized brackets."""
    brackets = [
        {"bracket": "0–20", "count": 0, "pct": 0.0, "color": "#ff0055"},
        {"bracket": "21–40", "count": 0, "pct": 0.0, "color": "#ff9900"},
        {"bracket": "41–60", "count": 0, "pct": 0.0, "color": "#ffcc00"},
        {"bracket": "61–80", "count": 0, "pct": 0.0, "color": "#00f0ff"},
        {"bracket": "81–100", "count": 0, "pct": 0.0, "color": "#00ff66"},
    ]
    if not values:
        return brackets

    total_n = len(values)
    for v in values:
        if v <= 20:
            brackets[0]["count"] += 1
        elif v <= 40:
            brackets[1]["count"] += 1
        elif v <= 60:
            brackets[2]["count"] += 1
        elif v <= 80:
            brackets[3]["count"] += 1
        else:
            brackets[4]["count"] += 1

    for b in brackets:
        b["pct"] = round((b["count"] / total_n) * 100, 1)

    return brackets


def _serialize_site_summary(
    r: FieldObservation, score_key: str = "trust"
) -> Dict[str, Any]:
    """Extract a concise site summary dict for ranking tables."""
    score_val = r.website_trust_score if score_key == "trust" else r.ip_risk_score
    class_val = (
        r.website_trust_classification
        if score_key == "trust"
        else r.ip_risk_classification
    )
    score_num = round(float(score_val), 1) if score_val is not None else None
    trust_val = round(float(r.website_trust_score), 1) if r.website_trust_score is not None else None
    risk_val = round(float(r.ip_risk_score), 1) if r.ip_risk_score is not None else None
    return {
        "test_id": r.test_id,
        "domain": r.domain,
        "category": r.category or "General Web",
        "ip": r.resolved_ip or r.ip_address or "Unknown",
        "country": r.country or "Unknown",
        "infrastructure": r.infrastructure_type or "Unknown",
        "https_status": r.https_status or "Unknown",
        "score": score_num,
        "trust_score": trust_val,
        "risk_score": risk_val,
        "trust_level": r.website_trust_classification or "Unknown",
        "risk_level": r.ip_risk_classification or "Unknown",
        "classification": class_val or "Unknown",
    }


def _build_empty_analytics_response(target_count: int = 50) -> Dict[str, Any]:
    """Construct an empty dataset analytics response without divide-by-zero or misleading 0% values."""
    empty_brackets = _compute_histogram_brackets([])
    return {
        "success": True,
        "insufficient_data": True,
        "overview": {
            "total_observations": 0,
            "valid_observations": 0,
            "invalid_observations": 0,
            "target": target_count,
            "sample_target": target_count,
            "remaining": target_count,
            "remaining_to_target": target_count,
            "target_reached": False,
            "progress_percentage": 0.0,
            "collection_progress_pct": 0.0,
            "status": "INCOMPLETE",
            "study_status": "INCOMPLETE",
            "https_adoption_pct": None,
            "ipv4_pct": None,
            "ipv6_pct": None,
            "vpn_detections": 0,
            "proxy_detections": 0,
            "tor_detections": 0,
            "cloud_datacenter_pct": None,
            "avg_trust_score": None,
            "mean_trust_score": None,
            "avg_risk_score": None,
            "mean_risk_score": None,
        },
        "trust_analysis": {
            "statistics": {"mean": None, "min": None, "max": None, "std_dev": None, "count": 0},
            "distribution": empty_brackets,
            "histogram": empty_brackets,
            "classifications": [],
            "min": None,
            "max": None,
            "mean": None,
            "std_dev": None,
            "count": 0,
        },
        "risk_analysis": {
            "statistics": {"mean": None, "min": None, "max": None, "std_dev": None, "count": 0},
            "distribution": empty_brackets,
            "histogram": empty_brackets,
            "classifications": [],
            "min": None,
            "max": None,
            "mean": None,
            "std_dev": None,
            "count": 0,
        },
        "security_analysis": {
            "https_enabled_count": 0, "https_enabled_pct": None,
            "https_disabled_count": 0, "https_disabled_pct": None,
            "https_unknown_count": 0, "https_unknown_pct": None,
            "tls_valid_count": 0, "tls_valid_pct": None,
            "tls_invalid_count": 0, "tls_invalid_pct": None,
            "tls_unknown_count": 0, "tls_unknown_pct": None,
            "https_status": {"enabled": 0, "disabled": 0, "unknown": 0, "adoption_pct": None},
            "tls_status": {"valid": 0, "invalid_or_expired": 0, "unknown": 0, "valid_pct": None},
        },
        "network_analysis": {
            "ipv4_count": 0, "ipv4_pct": None, "ipv6_count": 0, "ipv6_pct": None,
            "unknown_ip_count": 0, "network_types": [], "infrastructure_types": [],
            "cloud_vs_traditional": {
                "cloud_datacenter_count": 0, "cloud_datacenter_pct": None,
                "traditional_other_count": 0, "traditional_other_pct": None,
                "unknown_count": 0,
            },
            "threat_detections": {"vpn_count": 0, "proxy_count": 0, "tor_count": 0, "clean_count": 0},
            "top_asns": [], "top_organizations": [], "top_countries": [],
            "mean_dns_latency_ms": None, "mean_api_latency_ms": None,
            "ip_versions": {"ipv4": 0, "ipv6": 0, "unknown": 0, "ipv4_pct": 0.0, "ipv6_pct": 0.0},
            "infrastructure": {"cloud_datacenter": 0, "traditional_other": 0, "unknown": 0, "cloud_pct": 0.0},
            "threat_indicators": {"vpn": 0, "proxy": 0, "tor": 0, "clean": 0, "any_threat_flag": 0},
            "query_latency": {"mean_dns_ms": 0.0, "mean_api_ms": 0.0},
        },
        "comparison_analytics": {
            "highest_trust_sites": [], "lowest_trust_sites": [],
            "highest_risk_sites": [], "lowest_risk_sites": [],
            "https_vs_non_https": {
                "https_sample_count": 0, "https_avg_trust": None,
                "non_https_sample_count": 0, "non_https_avg_trust": None,
            },
            "cloud_vs_other_infrastructure": {
                "cloud_sample_count": 0, "cloud_avg_risk": None,
                "other_sample_count": 0, "other_avg_risk": None,
            },
            "flagged_threat_entities": [],
        },
        "research_insights": [],
        "chart_data": {
            "trust_histogram": empty_brackets,
            "risk_histogram": empty_brackets,
            "security_breakdown": [],
            "protocol_breakdown": [],
            "infrastructure_breakdown": [],
            "top_countries": [],
            "top_asns": [],
        },
        "export_summary": {
            "sample_size": 0,
            "target_quota": target_count,
            "status": "INCOMPLETE",
            "completeness_pct": 0.0,
            "timestamp": None,
        },
    }