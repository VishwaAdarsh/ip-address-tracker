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


@dataclass
class GeoResult:
    """Standardized internal representation of IP Geolocation data."""

    ip: str
    ip_version: str = "N/A"
    country: str = "N/A"
    country_code: str = "N/A"
    region: str = "N/A"
    city: str = "N/A"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: str = "N/A"
    organization: str = "N/A"
    isp: str = "N/A"
    asn: str = "N/A"
    status: GeoStatus = GeoStatus.SUCCESS
    error_message: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


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
) -> GeoResult:
    """
    Convert raw provider JSON dictionary into standard internal GeoResult format.

    - If raw_data is None or status is not SUCCESS, return error GeoResult.
    - Missing string fields default to "N/A".
    - Missing coordinate fields default to None.
    """
    ip_version = detect_ip_version(queried_ip)

    if status != GeoStatus.SUCCESS or not raw_data:
        return GeoResult(
            ip=queried_ip,
            ip_version=ip_version,
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
        raw_data.get("country_code") or raw_data.get("country") or "N/A"
    ).strip()
    region = str(
        raw_data.get("region") or raw_data.get("region_name") or "N/A"
    ).strip()
    city = str(raw_data.get("city") or "N/A").strip()

    # Safely convert latitude and longitude
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    raw_lat = raw_data.get("latitude") or raw_data.get("lat")
    raw_lon = raw_data.get("longitude") or raw_data.get("lon")

    if raw_lat is not None:
        try:
            latitude = float(raw_lat)
        except (ValueError, TypeError):
            latitude = None

    if raw_lon is not None:
        try:
            longitude = float(raw_lon)
        except (ValueError, TypeError):
            longitude = None

    timezone_str = str(raw_data.get("timezone") or "N/A").strip()
    org_str = str(
        raw_data.get("org") or raw_data.get("organization") or "N/A"
    ).strip()
    isp_str = str(raw_data.get("isp") or org_str or "N/A").strip()
    asn_str = str(raw_data.get("asn") or raw_data.get("as") or "N/A").strip()

    return GeoResult(
        ip=ip,
        ip_version=ip_version,
        country=country if country else "N/A",
        country_code=country_code if country_code else "N/A",
        region=region if region else "N/A",
        city=city if city else "N/A",
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_str if timezone_str else "N/A",
        organization=org_str if org_str else "N/A",
        isp=isp_str if isp_str else "N/A",
        asn=asn_str if asn_str else "N/A",
        status=GeoStatus.SUCCESS,
        error_message=None,
    )
