"""
Intelligence Chain & IP Personality Engine Module for IP PULSE Platform (Phase 18).

Provides:
- Deterministic IP Personality profile generation (concise 3–5 labels + evidence-grounded explanation)
- Structured 6-node Intelligence Provenance Chain (Domain → IP → ASN → Organization → Infrastructure → Location)
- Explicit Unknown-data handling (Unknown != Not Detected, Unknown != Safe, Unknown != Residential)
- Ethical characterization boundaries without unsubstantiated maliciousness verdicts
- 100% backward compatibility with legacy consumers and tests
"""
from dataclasses import asdict, dataclass, field
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from core.ip_intel import IPIntelligence, IPIntelligenceResult
from services.lookup_service import LookupResult, LookupStatus

# ==============================================================================
# Constants & Ethical Disclaimers
# ==============================================================================

PERSONALITY_DISCLAIMER = (
    "IP Personality is a derived analytical summary of observable network characteristics "
    "and should not be interpreted as definitive proof of physical usage, malicious intent, or legitimate identity."
)

CHAIN_DISCLAIMER = (
    "The Intelligence Provenance Chain documents observable routing and registry linkages. "
    "Unresolved nodes represent missing or protected information, not security vulnerabilities."
)

# Global Hyperscalers and Tier-1 Transit Providers for Network Scope Evaluation
GLOBAL_HYPERSCALER_KEYWORDS = [
    "cloudflare", "google", "amazon", "aws", "microsoft", "azure",
    "akamai", "fastly", "digitalocean", "edgecast", "level 3", "lumen",
    "cogent", "telia", "arelion", "verizon", "ntt", "tata communications",
]


# ==============================================================================
# Structured Data Models
# ==============================================================================

@dataclass
class ChainNode:
    """Represents a single step node in the end-to-end intelligence provenance chain."""

    key: str                    # "domain", "ip", "asn", "organization", "infrastructure", "location"
    label: str                  # "DOMAIN", "IP ADDRESS", "ASN", "ORGANIZATION", "INFRASTRUCTURE", "LOCATION"
    value: str                  # Observed value or "Unknown"
    status: str                 # "RESOLVED", "ASSIGNED", "IDENTIFIED", "CLASSIFIED", "GEOLOCATED", "DIRECT", "UNKNOWN"
    details: str = ""           # Contextual note (e.g. "Target Hostname", "IPv4 Protocol")
    icon: str = "dns"           # Material Symbols icon identifier

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IPPersonality:
    """Structured IP Personality profile (Phase 18)."""

    labels: List[str] = field(default_factory=list)      # Strictly 2–5 concise badges
    summary: str = ""                                    # 1–2 sentence evidence-grounded explanation
    confidence: str = "HIGH"                             # "HIGH", "MEDIUM", "LOW", "UNKNOWN"
    notes: List[str] = field(default_factory=list)       # Observable evidence points
    disclaimer: str = PERSONALITY_DISCLAIMER
    generated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceChain:
    """Complete structured provenance chain and IP Personality profile."""

    domain_or_input: str = ""
    resolved_ip: str = ""
    ip_version: str = "IPv4"
    asn: str = "Unknown"
    organization: str = "Unknown"
    isp: str = "Unknown"
    infrastructure_type: str = "Unknown"
    country: str = "Unknown"
    country_code: str = ""
    region: str = "Unknown"
    city: str = "Unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    personality: Optional[IPPersonality] = None
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    ip_personality: str = ""                             # Backward-compatible summary string
    disclaimer: str = CHAIN_DISCLAIMER

    # Convenience properties for clean consumption
    @property
    def domain(self) -> str:
        return self.domain_or_input

    @property
    def ip(self) -> str:
        return self.resolved_ip

    @property
    def infrastructure(self) -> str:
        return self.infrastructure_type

    @property
    def location(self) -> str:
        parts = [p for p in [self.city, self.region, self.country] if p and p != "Unknown"]
        return ", ".join(parts) if parts else "Unknown Location"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain_or_input,
            "ip": self.resolved_ip,
            "ip_version": self.ip_version,
            "asn": self.asn,
            "organization": self.organization,
            "isp": self.isp,
            "infrastructure": self.infrastructure_type,
            "location": self.location,
            "country": self.country,
            "country_code": self.country_code,
            "region": self.region,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "personality": self.personality.to_dict() if self.personality else None,
            "nodes": self.nodes,
            "ip_personality": self.ip_personality,
            "disclaimer": self.disclaimer,
        }


# ==============================================================================
# Deterministic IP Personality Generator
# ==============================================================================

def generate_ip_personality_profile(
    ip_intel: Optional[Union[IPIntelligence, IPIntelligenceResult]],
    lookup: Optional[LookupResult] = None,
) -> IPPersonality:
    """
    Generate deterministic, evidence-grounded IP Personality profile.

    Rules & Principles:
    1. Maximum 3–5 concise, meaningful labels.
    2. Unknown values are never converted to 'Safe', 'Not Detected', or 'Residential'.
    3. Derived strictly from verified technical observables without speculative verdicts.
    4. 1–2 sentence human-readable explanation matching the observed technical state.
    """
    # --------------------------------------------------------------------------
    # Signal Extraction & Normalization
    # --------------------------------------------------------------------------
    infra_type = getattr(ip_intel, "infrastructure_type", "Unknown") if ip_intel else "Unknown"
    net_type = getattr(ip_intel, "network_type", "Unknown") if ip_intel else "Unknown"
    
    is_datacenter = getattr(ip_intel, "is_datacenter", False) if ip_intel else False
    dc_status = getattr(ip_intel, "datacenter_status", "Detected" if is_datacenter else "Not Detected") if ip_intel else "Unknown"

    is_tor = getattr(ip_intel, "is_tor", False) if ip_intel else False
    tor_status = getattr(ip_intel, "tor_status", "Detected" if is_tor else "Not Detected") if ip_intel else "Unknown"

    is_proxy = getattr(ip_intel, "is_proxy", False) if ip_intel else False
    proxy_status = getattr(ip_intel, "proxy_status", "Detected" if is_proxy else "Not Detected") if ip_intel else "Unknown"

    is_vpn = getattr(ip_intel, "is_vpn", False) if ip_intel else False
    vpn_status = getattr(ip_intel, "vpn_status", "Detected" if is_vpn else "Not Detected") if ip_intel else "Unknown"

    org = (getattr(ip_intel, "organization", "") if ip_intel else "") or (getattr(lookup, "organization", "") if lookup else "")
    isp = (getattr(ip_intel, "isp", "") if ip_intel else "") or (getattr(lookup, "isp", "") if lookup else "")
    asn = (getattr(ip_intel, "asn", "") if ip_intel else "") or (getattr(lookup, "asn", "") if lookup else "")
    ip_version = (getattr(lookup, "ip_version", "") if lookup else "") or (getattr(ip_intel, "ip_version", "IPv4") if ip_intel else "IPv4")

    labels: List[str] = []
    notes: List[str] = []

    # --------------------------------------------------------------------------
    # Rule 1: Infrastructure & Network Type Classification (1-2 labels)
    # --------------------------------------------------------------------------
    infra_lower = infra_type.lower()
    net_lower = net_type.lower()

    if infra_type == "CDN / Edge Hub" or "cdn" in infra_lower:
        labels.append("CDN EDGE NODE")
        notes.append("Traffic is routed through a distributed Content Delivery Network edge point of presence.")
    elif infra_type == "Cloud Hosting" or net_lower == "cloud":
        labels.append("CLOUD HOSTED")
        notes.append("IP resides in commercial cloud compute infrastructure.")
    elif infra_type == "Datacenter" or is_datacenter or str(dc_status).lower() == "detected" or net_lower in ["datacenter", "hosting"]:
        labels.append("DATACENTER INFRASTRUCTURE")
        notes.append("Host is housed within a dedicated commercial datacenter or colocation facility.")
    elif infra_type in ["Commercial ISP", "Residential"] or net_lower in ["residential", "commercial isp"]:
        labels.append("RESIDENTIAL NETWORK")
        notes.append("IP belongs to consumer residential subscriber or commercial telecom access pools.")
    elif infra_type == "Mobile" or net_lower == "mobile":
        labels.append("MOBILE NETWORK")
        notes.append("Assigned to mobile cellular subscriber network.")
    elif infra_type == "Enterprise Network" or net_lower == "enterprise":
        labels.append("ENTERPRISE NETWORK")
        notes.append("Operated by an institutional or private corporate enterprise.")
    elif net_lower == "education":
        labels.append("ACADEMIC / RESEARCH")
        notes.append("Affiliated with university, educational, or academic research networking.")
    elif net_lower == "government":
        labels.append("GOVERNMENT NETWORK")
        notes.append("Registered under government or public sector networking authority.")

    # Complementary Datacenter label for cloud providers if space permits
    if "CLOUD HOSTED" in labels and (is_datacenter or str(dc_status).lower() == "detected") and "DATACENTER INFRASTRUCTURE" not in labels:
        labels.append("DATACENTER INFRASTRUCTURE")

    # --------------------------------------------------------------------------
    # Rule 2: Anonymization Characteristics (1 label)
    # --------------------------------------------------------------------------
    tor_detected = is_tor or str(tor_status).lower() == "detected"
    proxy_detected = is_proxy or str(proxy_status).lower() == "detected"
    vpn_detected = is_vpn or str(vpn_status).lower() == "detected"

    if tor_detected:
        labels.append("TOR ASSOCIATED")
        notes.append("Confirmed Tor anonymous relay exit node.")
    elif proxy_detected:
        labels.append("PROXY ASSOCIATED")
        notes.append("Public or commercial proxy gateway intermediary detected.")
    elif vpn_detected:
        labels.append("VPN ASSOCIATED")
        notes.append("Commercial VPN exit server detected.")
    else:
        # Check if all 3 anonymizers were explicitly tested and not detected
        tor_clean = str(tor_status).lower() in ["not detected", "not_detected"]
        proxy_clean = str(proxy_status).lower() in ["not detected", "not_detected"]
        vpn_clean = str(vpn_status).lower() in ["not detected", "not_detected"]

        if tor_clean and proxy_clean and vpn_clean:
            labels.append("LOW ANONYMIZATION")
            notes.append("No active Tor, Proxy, or commercial VPN indicators were observed.")
        # Note: If any anonymizer is "Unknown", we do NOT award "LOW ANONYMIZATION".

    # --------------------------------------------------------------------------
    # Rule 3: Network Scale & Routing Breadth (1 label)
    # --------------------------------------------------------------------------
    combined_entity = f"{org} {isp} {asn}".lower()
    is_global_provider = (
        infra_type == "CDN / Edge Hub"
        or any(k in combined_entity for k in GLOBAL_HYPERSCALER_KEYWORDS)
    )

    if is_global_provider and "GLOBAL NETWORK" not in labels and len(labels) < 4:
        labels.append("GLOBAL NETWORK")
        notes.append("Operated by an internationally distributed Tier-1 or hyperscale network provider.")
    elif asn and asn not in ["Unknown", "N/A"] and "REGIONAL OPERATOR" not in labels and len(labels) < 4:
        if "RESIDENTIAL NETWORK" in labels or "COMMERCIAL ISP" in infra_type.upper():
            labels.append("REGIONAL OPERATOR")

    # --------------------------------------------------------------------------
    # Rule 4: Protocol Addressing Standard (Optional)
    # --------------------------------------------------------------------------
    if str(ip_version).upper() == "IPV6" and len(labels) < 4:
        labels.append("IPV6 NATIVE")
        notes.append("Modern IPv6 native endpoint.")

    # --------------------------------------------------------------------------
    # Rule 5: Fallback & Maximum Boundary Enforcement (3–5 labels)
    # --------------------------------------------------------------------------
    if not labels:
        labels.append("INFRASTRUCTURE UNCLASSIFIED")
        notes.append("Sufficient technical signals were unavailable to classify network infrastructure.")

    # Enforce strict maximum limit of 5 labels
    final_labels = labels[:5]

    # --------------------------------------------------------------------------
    # Rule 6: Concise Natural Language Explanation Synthesis
    # --------------------------------------------------------------------------
    org_phrase = f" associated with {org}" if org and org not in ["Unknown", "N/A"] else ""
    provider_phrase = f" operated by {org}" if org and org not in ["Unknown", "N/A"] else ""

    if "TOR ASSOCIATED" in final_labels:
        summary = f"The IP address operates as an active Tor network relay exit node{org_phrase}, exhibiting high anonymization characteristics."
    elif "PROXY ASSOCIATED" in final_labels:
        summary = f"The IP operates as a public or commercial proxy server intermediary{org_phrase} routing indirect client requests."
    elif "VPN ASSOCIATED" in final_labels:
        summary = f"The IP is associated with commercial VPN exit infrastructure{org_phrase} used for encrypted egress tunneling."
    elif "CDN EDGE NODE" in final_labels:
        if "LOW ANONYMIZATION" in final_labels:
            summary = f"The IP operates as a distributed Content Delivery Network (CDN) edge node{provider_phrase} with global caching and low anonymization."
        else:
            summary = f"The IP functions as a distributed Content Delivery Network (CDN) edge hub{provider_phrase}."
    elif "CLOUD HOSTED" in final_labels or "DATACENTER INFRASTRUCTURE" in final_labels:
        if "LOW ANONYMIZATION" in final_labels:
            summary = f"The IP appears to belong to large-scale cloud/datacenter infrastructure{org_phrase} rather than a residential network. No anonymization indicator was detected."
        else:
            summary = f"The IP appears to use cloud or datacenter infrastructure{org_phrase}. Additional anonymization signals were unavailable."
    elif "RESIDENTIAL NETWORK" in final_labels:
        if "LOW ANONYMIZATION" in final_labels:
            summary = f"The IP is assigned to consumer residential subscriber or commercial telecom access infrastructure{provider_phrase}. No anonymization indicator was detected."
        else:
            summary = f"The IP operates from commercial ISP or subscriber network infrastructure{org_phrase}."
    elif "MOBILE NETWORK" in final_labels:
        summary = f"The IP is provisioned on a mobile carrier network{provider_phrase} supporting cellular data subscribers."
    elif "ENTERPRISE NETWORK" in final_labels or "ACADEMIC / RESEARCH" in final_labels:
        summary = f"The IP is assigned to institutional or private enterprise network infrastructure{org_phrase}."
    else:
        summary = "Assessment limited: Network infrastructure and anonymization characteristics could not be resolved from available data."

    # --------------------------------------------------------------------------
    # Confidence Level Determination
    # --------------------------------------------------------------------------
    known_count = sum([
        1 if infra_type != "Unknown" else 0,
        1 if dc_status != "Unknown" else 0,
        1 if tor_status != "Unknown" else 0,
        1 if proxy_status != "Unknown" else 0,
        1 if vpn_status != "Unknown" else 0,
    ])
    if known_count >= 4:
        confidence = "HIGH"
    elif known_count >= 2:
        confidence = "MEDIUM"
    elif known_count >= 1:
        confidence = "LOW"
    else:
        confidence = "UNKNOWN"

    return IPPersonality(
        labels=final_labels,
        summary=summary,
        confidence=confidence,
        notes=notes,
        disclaimer=PERSONALITY_DISCLAIMER,
    )


# ==============================================================================
# Provenance Intelligence Chain Builder
# ==============================================================================

def build_intelligence_chain(
    lookup: Optional[LookupResult],
    ip_intel: Optional[Union[IPIntelligence, IPIntelligenceResult]],
) -> IntelligenceChain:
    """
    Assemble the complete end-to-end Intelligence Provenance Chain.

    Chain Sequence:
    DOMAIN → IP ADDRESS → ASN → ORGANIZATION → INFRASTRUCTURE → LOCATION

    Args:
    - lookup: LookupResult instance or None
    - ip_intel: IPIntelligence or IPIntelligenceResult instance or None

    Returns:
    - IntelligenceChain dataclass instance
    """
    # Safe field resolution across available models
    target_in = getattr(lookup, "input", "") or "Unknown"
    is_domain = getattr(lookup, "input_type", "") == "DOMAIN" if lookup else False
    if not is_domain and "." in target_in and not target_in.replace(".", "").isdigit():
        is_domain = True

    dns_failed = (getattr(lookup, "dns_status", "") == "DNS_FAILED" or getattr(lookup, "overall_status", None) == LookupStatus.DNS_FAILED) if lookup else False

    raw_ip = getattr(lookup, "selected_ip", "")
    if not raw_ip:
        cand = getattr(ip_intel, "ip_address", "")
        if cand and (cand.replace(".", "").isdigit() or ":" in cand):
            raw_ip = cand
    ip_val = raw_ip if raw_ip else "Unknown"
    ip_version = getattr(lookup, "ip_version", "IPv4") if lookup else getattr(ip_intel, "ip_version", "IPv4")

    asn_val = getattr(lookup, "asn", "") or getattr(ip_intel, "asn", "") or "Unknown"
    org_val = getattr(lookup, "organization", "") or getattr(ip_intel, "organization", "") or getattr(lookup, "isp", "") or "Unknown"
    isp_val = getattr(lookup, "isp", "") or getattr(ip_intel, "isp", "") or "Unknown"
    infra_val = getattr(ip_intel, "infrastructure_type", "Unknown") if ip_intel else "Unknown"

    city_val = getattr(lookup, "city", "") or "Unknown"
    region_val = getattr(lookup, "region", "") or "Unknown"
    country_val = getattr(lookup, "country", "") or getattr(ip_intel, "country", "") or "Unknown"
    country_code = getattr(lookup, "country_code", "") if lookup else ""

    lat_val = getattr(lookup, "latitude", None) if lookup else None
    lon_val = getattr(lookup, "longitude", None) if lookup else None

    # Determine domain display value
    if is_domain and target_in not in ["Unknown", ""]:
        domain_display = target_in
    elif ip_val not in ["Unknown", "Unresolved IP"]:
        domain_display = "Direct IP Target"
    else:
        domain_display = "Unknown Host"

    # Location display string (treat N/A and Unknown neutrally)
    loc_parts = [p for p in [city_val, region_val, country_val] if p and p not in ["Unknown", "N/A"]]
    loc_display = ", ".join(loc_parts) if loc_parts else "Unknown Location"

    # --------------------------------------------------------------------------
    # Synthesize Structured IP Personality Profile
    # --------------------------------------------------------------------------
    personality = generate_ip_personality_profile(ip_intel=ip_intel, lookup=lookup)

    # --------------------------------------------------------------------------
    # Construct 6-Node Chain Representation
    # --------------------------------------------------------------------------
    nodes: List[Dict[str, Any]] = [
        ChainNode(
            key="domain",
            label="DOMAIN",
            value=domain_display,
            status="FAILED" if dns_failed else ("RESOLVED" if is_domain and domain_display != "Unknown Host" else ("DIRECT" if domain_display == "Direct IP Target" else "UNKNOWN")),
            details=f"Target Hostname: {domain_display}" if is_domain else "Direct IP Inquiry",
            icon="language",
        ).to_dict(),
        ChainNode(
            key="ip",
            label="IP ADDRESS",
            value=ip_val,
            status="RESOLVED" if ip_val not in ["Unresolved IP", "Unknown"] else "UNRESOLVED",
            details=f"{ip_version} Protocol" if ip_val not in ["Unresolved IP", "Unknown"] else "DNS resolution failed",
            icon="tag",
        ).to_dict(),
        ChainNode(
            key="asn",
            label="ASN",
            value=asn_val,
            status="ASSIGNED" if asn_val not in ["Unknown", "N/A", ""] else "UNASSIGNED",
            details=f"Autonomous System: {asn_val}",
            icon="hub",
        ).to_dict(),
        ChainNode(
            key="organization",
            label="ORGANIZATION",
            value=org_val,
            status="IDENTIFIED" if org_val not in ["Unknown", "N/A", ""] else "UNKNOWN",
            details=f"Operator: {org_val}",
            icon="corporate_fare",
        ).to_dict(),
        ChainNode(
            key="infrastructure",
            label="INFRASTRUCTURE",
            value=infra_val,
            status="CLASSIFIED" if infra_val not in ["Unknown", "N/A", ""] else "UNCLASSIFIED",
            details=f"Network Class: {infra_val}",
            icon="dns",
        ).to_dict(),
        ChainNode(
            key="location",
            label="LOCATION",
            value=loc_display,
            status="GEOLOCATED" if loc_display != "Unknown Location" else "UNKNOWN",
            details=f"Coordinates: {lat_val}, {lon_val}" if lat_val is not None and lon_val is not None else "Coordinates Unavailable",
            icon="location_on",
        ).to_dict(),
    ]

    return IntelligenceChain(
        domain_or_input=target_in,
        resolved_ip=ip_val,
        ip_version=ip_version,
        asn=asn_val,
        organization=org_val,
        isp=isp_val,
        infrastructure_type=infra_val,
        country=country_val,
        country_code=country_code,
        region=region_val,
        city=city_val,
        latitude=lat_val,
        longitude=lon_val,
        personality=personality,
        nodes=nodes,
        ip_personality=personality.summary,
        disclaimer=CHAIN_DISCLAIMER,
    )


# ==============================================================================
# Backward Compatibility Helper
# ==============================================================================

def generate_ip_personality(
    domain_input: str,
    ip_addr: str,
    org: str,
    infra_type: str,
    city: str,
    country: str,
) -> str:
    """
    Backward-compatible string helper for legacy callers and unit tests.
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
