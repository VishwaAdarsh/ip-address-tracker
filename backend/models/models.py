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


@dataclass
class FieldObservation:
    """
    Dataclass representing a structured 50-site field study observation (Phase 19).
    Holds 26 research attributes across Identity, Geolocation, Network, Security, Scoring, and Metadata.
    """

    id: Optional[int] = None
    test_id: int = 0
    domain: str = ""
    category: str = "General Web"
    resolved_ip: str = ""
    ip_version: str = "IPv4"

    # Geolocation
    country: str = "Unknown"
    region: str = "Unknown"
    city: str = "Unknown"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geolocation_confidence: str = "Unknown"

    # Network
    asn: str = "Unknown"
    organization: str = "Unknown"
    isp: str = "Unknown"
    network_type: str = "Unknown"
    infrastructure_type: str = "Unknown"

    # Security
    https_status: str = "Unknown"
    tls_status: str = "Unknown"
    vpn_status: str = "Unknown"
    proxy_status: str = "Unknown"
    tor_status: str = "Unknown"

    # Scoring
    website_trust_score: Optional[float] = None
    website_trust_classification: str = "Unknown"
    ip_risk_score: Optional[float] = None
    ip_risk_classification: str = "Unknown"
    score_confidence: str = "Unknown"
    evidence_coverage: Optional[float] = None

    # Metadata
    searched_by: str = "Anonymous"
    observation_status: str = "RECORDED"
    observed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    raw_history_id: Optional[int] = None

    # Legacy / GUI compatibility fields & aliases
    dns_response_time_ms: float = 0.0
    api_response_time_ms: float = 0.0
    error_message: Optional[str] = None
    country_code: str = "N/A"
    timezone: str = "N/A"

    @property
    def ip_address(self) -> str:
        return self.resolved_ip

    @property
    def input_value(self) -> str:
        return self.domain

    @property
    def input_type(self) -> str:
        return "DOMAIN"

    @property
    def status(self) -> str:
        return self.observation_status

    @property
    def timestamp(self) -> str:
        return self.observed_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert observation to a serializable dictionary format."""
        return {
            "id": self.id,
            "test_id": self.test_id,
            "domain": self.domain,
            "category": self.category,
            "resolved_ip": self.resolved_ip,
            "ip_address": self.resolved_ip,
            "ip_version": self.ip_version,
            "country": self.country,
            "country_code": self.country_code,
            "region": self.region,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "geolocation_confidence": self.geolocation_confidence,
            "asn": self.asn,
            "organization": self.organization,
            "isp": self.isp,
            "network_type": self.network_type,
            "infrastructure_type": self.infrastructure_type,
            "https_status": self.https_status,
            "tls_status": self.tls_status,
            "vpn_status": self.vpn_status,
            "proxy_status": self.proxy_status,
            "tor_status": self.tor_status,
            "website_trust_score": self.website_trust_score,
            "website_trust_classification": self.website_trust_classification,
            "ip_risk_score": self.ip_risk_score,
            "ip_risk_classification": self.ip_risk_classification,
            "score_confidence": self.score_confidence,
            "evidence_coverage": self.evidence_coverage,
            "searched_by": self.searched_by,
            "observation_status": self.observation_status,
            "status": self.observation_status,
            "observed_at": self.observed_at,
            "timestamp": self.observed_at,
            "raw_history_id": self.raw_history_id,
            "dns_response_time_ms": self.dns_response_time_ms,
            "api_response_time_ms": self.api_response_time_ms,
            "error_message": self.error_message,
            "input_value": self.domain,
            "input_type": "DOMAIN",
        }

