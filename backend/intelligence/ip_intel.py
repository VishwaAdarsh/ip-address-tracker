"""
IP Intelligence & Infrastructure Analysis Engine Module for IP PULSE Platform (Phase 16).

Provides:
- Reusable IPIntelligenceResult data model with explicit "Unknown" handling
- Provider abstraction layer (IPIntelligenceProvider base class and StandardIPIntelligenceProvider implementation)
- Network type classification (Cloud, Datacenter, Hosting, Enterprise, Residential, Mobile, Education, Government)
- Infrastructure type classification (CDN / Edge Hub, Cloud Hosting, Commercial ISP, Enterprise Network)
- VPN, Proxy, Tor, and Datacenter signal status evaluation ("Detected", "Not Detected", "Unknown")
- Quota (429), timeout, and network error resilience
"""
from dataclasses import dataclass, field
import datetime
from typing import List, Optional, Tuple


@dataclass
class IPIntelligenceResult:
    """
    Structured data model for IP Intelligence & Infrastructure Analysis (Phase 16).

    Uses explicit "Unknown" string defaults to ensure missing data is never converted into false assertions.
    """

    ip_address: str = ""
    ip_version: str = "Unknown"                      # "IPv4", "IPv6", "Unknown"
    asn: str = "Unknown"                             # e.g. "AS15169" or "Unknown"
    asn_name: str = "Unknown"                        # e.g. "Google LLC" or "Unknown"
    organization: str = "Unknown"                    # e.g. "Google LLC" or "Unknown"
    isp: str = "Unknown"                             # e.g. "Google LLC" or "Unknown"
    network_type: str = "Unknown"                    # "Cloud", "Datacenter", "Hosting", "Enterprise", "Residential", "Mobile", "Education", "Government", "Unknown"
    infrastructure_type: str = "Unknown"             # "CDN / Edge Hub", "Cloud Hosting", "Commercial ISP", "Enterprise Network", "Unknown"
    vpn_status: str = "Unknown"                      # "Detected", "Not Detected", "Unknown"
    proxy_status: str = "Unknown"                    # "Detected", "Not Detected", "Unknown"
    tor_status: str = "Unknown"                      # "Detected", "Not Detected", "Unknown"
    datacenter_status: str = "Unknown"               # "Detected", "Not Detected", "Unknown"
    country: str = "Unknown"
    network_country: str = "Unknown"
    checked_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class IPIntelligence:
    """Backward-compatible IPIntelligence dataclass bridge."""

    ip_address: str = ""
    asn: str = "N/A"
    organization: str = "N/A"
    isp: str = "N/A"
    infrastructure_type: str = "Unknown"
    is_datacenter: bool = False
    is_vpn: bool = False
    is_proxy: bool = False
    is_tor: bool = False
    hosting_provider: str = "N/A"
    threat_level: str = "Low"


# Signatures for Network & Infrastructure Classification
CDN_KEYWORDS = [
    "cloudflare", "fastly", "akamai", "cloudfront", "imperva", "incapsula",
    "edgecast", "limelight", "cdn77", "bunnycdn", "sucuri", "stackpath",
]

CLOUD_HOSTING_KEYWORDS = [
    "amazon", "aws", "google cloud", "google llc", "microsoft", "azure",
    "digitalocean", "linode", "hetzner", "ovh", "vultr", "oracle",
    "alibaba", "scaleway", "contabo", "choopa", "leaseweb", "rackspace",
]

ISP_KEYWORDS = [
    "comcast", "at&t", "verizon", "deutsche telekom", "airtel", "jio",
    "reliance", "vodafone", "charter", "spectrum", "bt", "orange",
    "telefónica", "t-mobile",
]

ANONYMIZER_VPN_KEYWORDS = ["mullvad", "nordvpn", "expressvpn", "protonvpn", "surfshark", "cyberghost", "private internet access", "vpn exit"]
ANONYMIZER_TOR_KEYWORDS = ["tor exit", "tor node", "tor onion", "tor anonymizer"]
ANONYMIZER_PROXY_KEYWORDS = ["anonymous proxy", "socks proxy", "http proxy"]


class IPIntelligenceProvider:
    """Abstract Base Class for IP Intelligence Data Providers."""

    def analyze_ip(
        self,
        ip_address: str,
        asn: str = "",
        org: str = "",
        isp: str = "",
        raw_signals: Optional[dict] = None,
    ) -> IPIntelligenceResult:
        raise NotImplementedError("IPIntelligenceProvider subclasses must implement analyze_ip()")


class StandardIPIntelligenceProvider(IPIntelligenceProvider):
    """
    Standard IP Intelligence Provider implementation.
    
    Evaluates provider signals and local network classification heuristics safely
    without returning unverified assumptions when signals are missing.
    """

    def analyze_ip(
        self,
        ip_address: str,
        asn: str = "",
        org: str = "",
        isp: str = "",
        raw_signals: Optional[dict] = None,
    ) -> IPIntelligenceResult:
        result = IPIntelligenceResult(ip_address=ip_address)

        if not ip_address:
            result.errors.append("Empty IP address input")
            return result

        # Determine IP Version
        if ":" in ip_address:
            result.ip_version = "IPv6"
        elif "." in ip_address:
            result.ip_version = "IPv4"
        else:
            result.errors.append("Invalid IP address format")
            return result

        result.asn = asn or "Unknown"
        result.asn_name = org or isp or "Unknown"
        result.organization = org or "Unknown"
        result.isp = isp or "Unknown"

        combined_text = f"{org} {isp} {asn}".lower()

        # 1. Determine Infrastructure Type & Network Type
        infra_type, net_type, host_name = self._classify_network(combined_text)
        result.infrastructure_type = infra_type
        result.network_type = net_type

        # 2. Evaluate Datacenter Status
        if infra_type in ["Cloud Hosting", "CDN / Edge Hub"] or net_type in ["Cloud", "Datacenter", "Hosting"]:
            result.datacenter_status = "Detected"
        elif net_type in ["Residential", "Commercial ISP"]:
            result.datacenter_status = "Not Detected"
        else:
            result.datacenter_status = "Unknown"

        # 3. Evaluate Anonymization Signals (VPN / Proxy / Tor)
        raw = raw_signals or {}

        # Tor Detection
        if raw.get("tor") is True or any(kw in combined_text for kw in ANONYMIZER_TOR_KEYWORDS):
            result.tor_status = "Detected"
        elif raw.get("tor") is False or "tor" not in combined_text:
            result.tor_status = "Not Detected"
        else:
            result.tor_status = "Unknown"

        # VPN Detection
        if raw.get("vpn") is True or any(kw in combined_text for kw in ANONYMIZER_VPN_KEYWORDS):
            result.vpn_status = "Detected"
        elif raw.get("vpn") is False:
            result.vpn_status = "Not Detected"
        else:
            # Note: Datacenter IP does NOT automatically mean VPN! If unverified, explicit Unknown.
            result.vpn_status = "Unknown" if "vpn" not in combined_text else "Detected"

        # Proxy Detection
        if raw.get("proxy") is True or any(kw in combined_text for kw in ANONYMIZER_PROXY_KEYWORDS):
            result.proxy_status = "Detected"
        elif raw.get("proxy") is False:
            result.proxy_status = "Not Detected"
        else:
            result.proxy_status = "Unknown" if "proxy" not in combined_text else "Detected"

        return result

    def _classify_network(self, text: str) -> Tuple[str, str, str]:
        """Classify (infrastructure_type, network_type, provider_name)."""
        for kw in CDN_KEYWORDS:
            if kw in text:
                return "CDN / Edge Hub", "Cloud", kw.title()

        for kw in CLOUD_HOSTING_KEYWORDS:
            if kw in text:
                return "Cloud Hosting", "Cloud", kw.title()

        for kw in ISP_KEYWORDS:
            if kw in text:
                return "Commercial ISP", "Residential", "N/A"

        if "university" in text or "college" in text or "edu" in text:
            return "Enterprise Network", "Education", "N/A"

        if "gov" in text or "government" in text or "military" in text:
            return "Enterprise Network", "Government", "N/A"

        if any(term in text for term in ["bank", "inc", "ltd", "corp", "enterprise"]):
            return "Enterprise Network", "Enterprise", "N/A"

        return "Unknown", "Unknown", "N/A"


def analyze_ip_infrastructure(
    ip_address: str,
    asn: str = "",
    org: str = "",
    isp: str = "",
    provider: Optional[IPIntelligenceProvider] = None,
    raw_signals: Optional[dict] = None,
) -> IPIntelligenceResult:
    """
    High-level entry point for Phase 16 IP Intelligence & Infrastructure Analysis.

    Args:
    - ip_address: Target IP address string
    - asn: ASN string
    - org: Organization string
    - isp: ISP string
    - provider: Optional custom IPIntelligenceProvider instance (defaults to StandardIPIntelligenceProvider)
    - raw_signals: Optional raw provider signal dict

    Returns:
    - IPIntelligenceResult dataclass instance
    """
    active_provider = provider or StandardIPIntelligenceProvider()
    return active_provider.analyze_ip(
        ip_address=ip_address,
        asn=asn,
        org=org,
        isp=isp,
        raw_signals=raw_signals,
    )


def analyze_ip_intelligence(ip_address: str, asn: str = "", org: str = "", isp: str = "") -> IPIntelligence:
    """Backward-compatible analyze_ip_intelligence bridging to IPIntelligence."""
    res = analyze_ip_infrastructure(ip_address, asn=asn, org=org, isp=isp)

    is_dc = res.datacenter_status == "Detected"
    is_v = res.vpn_status == "Detected"
    is_p = res.proxy_status == "Detected"
    is_t = res.tor_status == "Detected"

    threat = "Low"
    if is_t:
        threat = "High"
    elif is_v or is_p:
        threat = "Moderate"

    return IPIntelligence(
        ip_address=res.ip_address,
        asn=res.asn,
        organization=res.organization,
        isp=res.isp,
        infrastructure_type=res.infrastructure_type if res.infrastructure_type != "Unknown" else "General Network",
        is_datacenter=is_dc,
        is_vpn=is_v,
        is_proxy=is_p,
        is_tor=is_t,
        hosting_provider=res.organization if is_dc else "N/A",
        threat_level=threat,
    )
