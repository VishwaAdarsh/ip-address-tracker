"""
Database models for IP Address Tracker & Geolocation Tool.

Provides simple dataclass representations for SQLite lookup history records.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class LookupRecord:
    """Dataclass representing a stored lookup history record in SQLite."""

    id: Optional[int] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    input_value: str = ""
    input_type: str = ""
    domain: str = ""
    ip_address: str = ""
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
    dns_response_time_ms: float = 0.0
    api_response_time_ms: float = 0.0
    status: str = ""
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to a dictionary format."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "input_value": self.input_value,
            "input_type": self.input_type,
            "domain": self.domain,
            "ip_address": self.ip_address,
            "ip_version": self.ip_version,
            "country": self.country,
            "country_code": self.country_code,
            "region": self.region,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timezone": self.timezone,
            "organization": self.organization,
            "isp": self.isp,
            "asn": self.asn,
            "dns_response_time_ms": self.dns_response_time_ms,
            "api_response_time_ms": self.api_response_time_ms,
            "status": self.status,
            "error_message": self.error_message,
        }
