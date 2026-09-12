"""
Intelligence Chain & IP Personality Engine Module for IP PULSE Platform.

Provides:
- Domain → IP → ASN → Organization → Infrastructure → Location provenance chain assembly
- Human-readable IP Personality natural language summary generation
"""
from dataclasses import dataclass
from typing import Optional

from core.ip_intel import IPIntelligence
from services.lookup_service import LookupResult


@dataclass
class IntelligenceChain:
    """Dataclass holding complete end-to-end intelligence provenance chain."""

    domain_or_input: str = ""
    resolved_ip: str = ""
    ip_version: str = "IPv4"
    asn: str = "N/A"
    organization: str = "N/A"
    isp: str = "N/A"
    infrastructure_type: str = "Unknown"
    country: str = "Unknown"
    country_code: str = ""
    region: str = "Unknown"
    city: str = "Unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ip_personality: str = ""


def generate_ip_personality(
    domain_input: str,
    ip_addr: str,
    org: str,
    infra_type: str,
    city: str,
    country: str,
) -> str:
    """
    Generate human-readable IP Personality natural language synthesis.

    Example outputs:
    - "Cloudflare CDN Edge Hub in San Francisco, United States"
    - "Google Cloud Datacenter Node in Mountain View, United States"
    - "Residential Telecom Infrastructure in Frankfurt, Germany"
    """
    loc_str = f"{city}, {country}".strip(", ") if (city and country) else (country or "Global Location")

    if infra_type == "CDN / Edge Hub":
        return f"{org or 'Content Delivery Network'} Edge Hub serving {domain_input} in {loc_str}"
    elif infra_type == "Cloud Hosting":
        return f"Cloud Hosting Node ({org or 'Datacenter Provider'}) in {loc_str}"
    elif infra_type == "Enterprise Network":
        return f"Institutional Enterprise Server ({org}) located in {loc_str}"
    elif infra_type == "Commercial ISP":
        return f"Commercial Telecom / Residential Network Gateway ({org}) in {loc_str}"
    else:
        return f"Public Network Node ({ip_addr}) operated by {org or 'Unknown Provider'} in {loc_str}"


def build_intelligence_chain(
    lookup: LookupResult,
    ip_intel: IPIntelligence,
) -> IntelligenceChain:
    """
    Assemble the complete end-to-end Intelligence Provenance Chain.

    Args:
    - lookup: LookupResult dataclass from base lookup service
    - ip_intel: IPIntelligence dataclass from IP Intel Engine

    Returns:
    - IntelligenceChain dataclass instance
    """
    target_in = lookup.input or "N/A"
    ip_val = lookup.selected_ip or "N/A"
    org_val = lookup.organization or ip_intel.organization or "N/A"
    city_val = lookup.city or "Unknown"
    country_val = lookup.country or "Unknown"

    personality = generate_ip_personality(
        domain_input=target_in,
        ip_addr=ip_val,
        org=org_val,
        infra_type=ip_intel.infrastructure_type,
        city=city_val,
        country=country_val,
    )

    return IntelligenceChain(
        domain_or_input=target_in,
        resolved_ip=ip_val,
        ip_version=lookup.ip_version or "IPv4",
        asn=lookup.asn or "N/A",
        organization=org_val,
        isp=lookup.isp or ip_intel.isp or "N/A",
        infrastructure_type=ip_intel.infrastructure_type,
        country=country_val,
        country_code=lookup.country_code or "",
        region=lookup.region or "Unknown",
        city=city_val,
        latitude=lookup.latitude,
        longitude=lookup.longitude,
        ip_personality=personality,
    )
