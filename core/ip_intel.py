"""
IP Intelligence Engine Module for IP PULSE Platform.

Provides:
- Infrastructure classification (CDN/Edge, Cloud Hosting, Commercial ISP, Enterprise)
- Heuristic detection for Datacenter IPs, VPNs, Proxies, and Tor Exit Nodes
- Network threat level evaluation (Low, Moderate, High, Critical)
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass
class IPIntelligence:
    """Dataclass holding IP Intelligence signals and infrastructure analysis."""

    ip_address: str = ""
    asn: str = "N/A"
    organization: str = "N/A"
    isp: str = "N/A"
    infrastructure_type: str = "Unknown"  # CDN / Edge Hub, Cloud Hosting, Commercial ISP, Enterprise / Org
    is_datacenter: bool = False
    is_vpn: bool = False
    is_proxy: bool = False
    is_tor: bool = False
    hosting_provider: str = "N/A"
    threat_level: str = "Low"  # Low, Moderate, High, Critical


# Known CDN Provider Signatures (ASN / Org Keywords)
CDN_KEYWORDS = [
    "cloudflare",
    "fastly",
    "akamai",
    "cloudfront",
    "imperva",
    "incapsula",
    "edgecast",
    "limelight",
    "cdn77",
    "bunnycdn",
    "sucuri",
    "stackpath",
]

# Known Cloud / Datacenter Hosting Providers
CLOUD_HOSTING_KEYWORDS = [
    "amazon",
    "aws",
    "google cloud",
    "google llc",
    "microsoft",
    "azure",
    "digitalocean",
    "linode",
    "hetzner",
    "ovh",
    "vultr",
    "oracle",
    "alibaba",
    "scaleway",
    "contabo",
    "choopa",
    "leaseweb",
    "rackspace",
]

# Known Commercial Residential / Telecom ISPs
ISP_KEYWORDS = [
    "comcast",
    "at&t",
    "verizon",
    "deutsche telekom",
    "airtel",
    "jio",
    "reliance",
    "vodafone",
    "charter",
    "spectrum",
    "bt",
    "orange",
    "telefónica",
    "t-mobile",
]

# Known Anonymous Proxy / VPN / Tor Signatures
ANONYMIZER_KEYWORDS = [
    "vpn",
    "proxy",
    "tor exit",
    "tor node",
    "mullvad",
    "nordvpn",
    "expressvpn",
    "protonvpn",
    "surfshark",
    "cyberghost",
    "private internet access",
    "anonymizer",
    "exit node",
]


def classify_infrastructure(org: str, isp: str, asn: str) -> Tuple[str, str]:
    """
    Classify network infrastructure category and detect specific hosting provider.

    Returns:
    - Tuple: (infrastructure_type: str, hosting_provider: str)
    """
    text = f"{org} {isp} {asn}".lower()

    # Check CDN / Edge Hub
    for kw in CDN_KEYWORDS:
        if kw in text:
            return "CDN / Edge Hub", kw.title()

    # Check Cloud / Datacenter Hosting
    for kw in CLOUD_HOSTING_KEYWORDS:
        if kw in text:
            return "Cloud Hosting", kw.title()

    # Check Commercial Telecom / ISP
    for kw in ISP_KEYWORDS:
        if kw in text:
            return "Commercial ISP", "N/A"

    # Default to Enterprise / Organization or General Network
    if any(term in text for term in ["university", "college", "bank", "government", "inc", "ltd", "corp"]):
        return "Enterprise Network", "N/A"

    return "General Network", "N/A"


def analyze_ip_intelligence(ip_address: str, asn: str = "", org: str = "", isp: str = "") -> IPIntelligence:
    """
    Perform complete IP Intelligence classification and risk indicator heuristic analysis.

    Args:
    - ip_address: IP address string
    - asn: Autonomous System Number string (e.g. 'AS15169')
    - org: Organization string
    - isp: ISP string

    Returns:
    - IPIntelligence dataclass instance
    """
    intel = IPIntelligence(
        ip_address=ip_address,
        asn=asn or "N/A",
        organization=org or "N/A",
        isp=isp or "N/A",
    )

    combined_text = f"{org} {isp} {asn}".lower()

    # Infrastructure & Provider Classification
    infra_type, host_prov = classify_infrastructure(org, isp, asn)
    intel.infrastructure_type = infra_type
    intel.hosting_provider = host_prov

    # Datacenter Detection
    if infra_type in ["Cloud Hosting", "CDN / Edge Hub"] or any(
        kw in combined_text for kw in ["hosting", "datacenter", "colocation", "server", "vps"]
    ):
        intel.is_datacenter = True

    # VPN / Proxy / Tor Detection
    for kw in ANONYMIZER_KEYWORDS:
        if kw in combined_text:
            if "tor" in kw:
                intel.is_tor = True
            elif "vpn" in kw:
                intel.is_vpn = True
            else:
                intel.is_proxy = True

    # Threat Level Evaluation
    if intel.is_tor:
        intel.threat_level = "High"
    elif intel.is_vpn or intel.is_proxy:
        intel.threat_level = "Moderate"
    elif intel.is_datacenter and infra_type == "Unknown":
        intel.threat_level = "Moderate"
    else:
        intel.threat_level = "Low"

    return intel
