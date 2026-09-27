"""
Core Response Normalizer Module for IP Address Tracker & Geolocation Tool.

Responsible for:
- Mapping provider-specific JSON responses into standard internal GeoResult dataclass
- Handling missing fields gracefully by populating "N/A" (or None for coordinates)
- Preserving accurate IP version classification
- Insulating application logic from geolocation provider response schema differences
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import ipaddress
from typing import Any, Dict, Optional


class GeoStatus(Enum):
    """Enumeration of Geolocation lookup status outcomes."""

    SUCCESS = "SUCCESS"
    API_TIMEOUT = "API_TIMEOUT"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    API_AUTH_ERROR = "API_AUTH_ERROR"
    API_HTTP_ERROR = "API_HTTP_ERROR"
    API_NO_DATA = "API_NO_DATA"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    NETWORK_ERROR = "NETWORK_ERROR"
    INVALID_IP = "INVALID_IP"


# Known Anycast / Global Edge CDN Autonomous Systems
ANYCAST_ASNS = {
    "AS8075",   # Microsoft Corporation
    "AS15169",  # Google LLC
    "AS13335",  # Cloudflare, Inc.
    "AS54113",  # Fastly, Inc.
    "AS16509",  # Amazon.com, Inc. / AWS
    "AS20940",  # Akamai Technologies
    "AS22822",  # Limelight Networks
    "AS14618",  # Amazon.com
}


@dataclass
class CanonicalGeo:
    """Canonical Geolocation Data Model (Independent of provider schema)."""

    ip: str
    country: str = "N/A"
    country_code: str = "N/A"
    region: str = "N/A"
    city: str = "N/A"
    postal: str = "N/A"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = "N/A"
    confidence: str = "UNKNOWN"  # HIGH, MEDIUM, LOW, APPROXIMATE, UNKNOWN
    provider: str = "Unknown"
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    is_anycast: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Return clean canonical dictionary representation."""
        return {
            "ip": self.ip,
            "country": self.country,
            "country_code": self.country_code,
            "region": self.region,
            "city": self.city,
            "postal": self.postal,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "confidence": self.confidence,
            "provider": self.provider,
            "retrieved_at": self.retrieved_at,
            "is_anycast": self.is_anycast,
        }


@dataclass
class GeoResult:
    """Standardized internal representation of IP Geolocation and Network data."""

    ip: str
    ip_version: str = "N/A"
    country: str = "N/A"
    country_code: str = "N/A"
    region: str = "N/A"
    city: str = "N/A"
    postal: str = "N/A"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = "N/A"
    organization: str = "N/A"
    isp: str = "N/A"
    asn: str = "N/A"
    provider: str = "Unknown"
    confidence: str = "UNKNOWN"
    is_anycast: bool = False
    retrieved_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    status: GeoStatus = GeoStatus.SUCCESS
    error_message: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_canonical_geo(self) -> CanonicalGeo:
        """Convert into canonical geolocation model."""
        return CanonicalGeo(
            ip=self.ip,
            country=self.country,
            country_code=self.country_code,
            region=self.region,
            city=self.city,
            postal=self.postal,
            latitude=self.latitude,
            longitude=self.longitude,
            timezone=self.timezone,
            confidence=self.confidence,
            provider=self.provider,
            retrieved_at=self.retrieved_at,
            is_anycast=self.is_anycast,
        )

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Convert to canonical dictionary format."""
        return self.to_canonical_geo().to_dict()


def detect_ip_version(ip_str: str) -> str:
    """Helper to identify whether an IP string is IPv4 or IPv6."""
    if not ip_str:
        return "N/A"
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        if isinstance(ip_obj, ipaddress.IPv4Address):
            return "IPv4"
        elif isinstance(ip_obj, ipaddress.IPv6Address):
            return "IPv6"
    except ValueError:
        pass
    return "N/A"


def normalize_geo_response(
    raw_data: Optional[Dict[str, Any]],
    queried_ip: str,
    status: GeoStatus = GeoStatus.SUCCESS,
    error_message: Optional[str] = None,
    provider: str = "Unknown",
    retrieved_at: Optional[str] = None,
) -> GeoResult:
    """
    Convert raw provider JSON dictionary into standard internal GeoResult format.

    - If raw_data is None or status is not SUCCESS, return error GeoResult.
    - Missing string fields default to "N/A".
    - Missing or invalid coordinate fields default to None.
    - Accurately classifies Anycast / CDN infrastructure and evaluates confidence.
    """
    ip_version = detect_ip_version(queried_ip)
    fetch_time = retrieved_at or datetime.now(timezone.utc).isoformat()

    if status != GeoStatus.SUCCESS or not raw_data:
        return GeoResult(
            ip=queried_ip,
            ip_version=ip_version,
            provider=provider,
            confidence="UNKNOWN",
            retrieved_at=fetch_time,
            status=status,
            error_message=error_message or "Geolocation lookup failed",
        )

    # Handle provider-reported errors in payload (e.g. ipapi.co {"error": true, "reason": "..."})
    if raw_data.get("error") is True:
        reason = raw_data.get("reason", "API error response")
        err_status = (
            GeoStatus.API_RATE_LIMIT
            if "rate limit" in str(reason).lower()
            else GeoStatus.API_NO_DATA
        )
        return GeoResult(
            ip=queried_ip,
            ip_version=ip_version,
            provider=provider,
            confidence="UNKNOWN",
            retrieved_at=fetch_time,
            status=err_status,
            error_message=f"Geolocation service error: {reason}",
        )

    # Extract fields with safe fallbacks
    ip = str(raw_data.get("ip") or queried_ip).strip()
    extracted_version = str(raw_data.get("version") or "").strip()
    if extracted_version in ("IPv4", "IPv6"):
        ip_version = extracted_version

    country = str(
        raw_data.get("country_name") or raw_data.get("country") or "N/A"
    ).strip()
    country_code = str(
        raw_data.get("country_code") or raw_data.get("countryCode") or raw_data.get("country") or "N/A"
    ).strip()
    region = str(
        raw_data.get("region_name") or raw_data.get("regionName") or raw_data.get("region") or "N/A"
    ).strip()
    city = str(raw_data.get("city") or "N/A").strip()
    postal = str(raw_data.get("postal") or raw_data.get("zip") or "N/A").strip()

    # Safely convert latitude and longitude with physical Earth bounds validation
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    raw_lat = raw_data.get("latitude") or raw_data.get("lat")
    raw_lon = raw_data.get("longitude") or raw_data.get("lon")

    if raw_lat is not None:
        try:
            val = float(raw_lat)
            if -90.0 <= val <= 90.0:
                latitude = val
        except (ValueError, TypeError):
            latitude = None

    if raw_lon is not None:
        try:
            val = float(raw_lon)
            if -180.0 <= val <= 180.0:
                longitude = val
        except (ValueError, TypeError):
            longitude = None

    # Null Island check (0.0, 0.0 is almost always a provider placeholder, not a physical server location)
    if latitude == 0.0 and longitude == 0.0:
        latitude = None
        longitude = None

    timezone_str = str(raw_data.get("timezone") or "N/A").strip()
    org_str = str(
        raw_data.get("org") or raw_data.get("organization") or "N/A"
    ).strip()
    isp_str = str(raw_data.get("isp") or org_str or "N/A").strip()
    asn_str = str(raw_data.get("asn") or raw_data.get("as") or "N/A").strip()

    # Anycast / CDN detection
    is_anycast = bool(raw_data.get("anycast") is True)
    upper_asn = asn_str.upper().split()[0] if asn_str else ""
    if upper_asn in ANYCAST_ASNS:
        is_anycast = True
    elif any(term in org_str.lower() or term in isp_str.lower() for term in ("cloudflare", "fastly", "akamai", "anycast", "front door", "edge")):
        is_anycast = True

    # Accuracy / Confidence calculation
    if is_anycast:
        # Anycast routes traffic to nearest edge pop; physical server location is dynamic/approximate
        confidence = "APPROXIMATE"
    elif latitude is not None and longitude is not None and city not in ("N/A", "Unknown", "") and country not in ("N/A", "Unknown", ""):
        confidence = "HIGH"
    elif country not in ("N/A", "Unknown", ""):
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return GeoResult(
        ip=ip,
        ip_version=ip_version,
        country=country if country else "N/A",
        country_code=country_code if country_code else "N/A",
        region=region if region else "N/A",
        city=city if city else "N/A",
        postal=postal if postal else "N/A",
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_str if timezone_str else "N/A",
        organization=org_str if org_str else "N/A",
        isp=isp_str if isp_str else "N/A",
        asn=asn_str if asn_str else "N/A",
        provider=provider,
        confidence=confidence,
        is_anycast=is_anycast,
        retrieved_at=fetch_time,
        status=GeoStatus.SUCCESS,
        error_message=None,
    )
