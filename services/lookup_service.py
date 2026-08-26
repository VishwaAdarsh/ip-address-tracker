"""
Core Integrated Lookup Engine for IP Address Tracker & Geolocation Tool.

Orchestrates:
- Input validation (core.validator)
- DNS resolution for domains (core.dns_resolver)
- Deterministic IP selection (IPv4 priority over IPv6)
- IP Geolocation retrieval (core.geo_service)
- Response normalization (core.normalizer)
- Complete pipeline timing and stage error handling
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import time
from typing import List, Optional

from core.dns_resolver import DNSStatus, resolve_domain
from core.geo_service import get_geolocation
from core.normalizer import GeoStatus
from core.validator import InputType, validate_input


class LookupStatus(Enum):
    """Enumeration of overall integrated lookup statuses."""

    SUCCESS = "SUCCESS"
    INVALID_INPUT = "INVALID_INPUT"
    DNS_FAILED = "DNS_FAILED"
    GEO_FAILED = "GEO_FAILED"


@dataclass
class LookupResult:
    """Structured result returned by the integrated lookup engine."""

    input: str
    normalized_input: str
    input_type: str
    resolved_addresses: List[str] = field(default_factory=list)
    ipv4_addresses: List[str] = field(default_factory=list)
    ipv6_addresses: List[str] = field(default_factory=list)
    selected_ip: Optional[str] = None
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
    total_response_time_ms: float = 0.0
    dns_status: str = "NOT_ATTEMPTED"
    geolocation_status: str = "NOT_ATTEMPTED"
    overall_status: LookupStatus = LookupStatus.INVALID_INPUT
    error_message: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def select_primary_ip(
    ipv4_addresses: List[str], ipv6_addresses: List[str]
) -> Optional[str]:
    """
    Deterministic IP Selection Rule:
    1. Prefer the first valid IPv4 address returned by DNS.
    2. If no IPv4 address exists, use the first valid IPv6 address.
    3. Return None if both lists are empty.
    """
    if ipv4_addresses:
        return ipv4_addresses[0]
    if ipv6_addresses:
        return ipv6_addresses[0]
    return None


def perform_lookup(raw_input: str) -> LookupResult:
    """
    Execute the integrated lookup workflow for a domain or IP address.

    Workflow:
    1. Validate raw input
    2. If domain: resolve DNS and select primary IP
    3. If IP: skip DNS resolution
    4. Query geolocation service for selected IP
    5. Measure component & total timing
    6. Return unified LookupResult with stage-specific statuses
    """
    start_total_time = time.perf_counter()

    # Step 1: Validate input
    val_res = validate_input(raw_input)
    if not val_res.is_valid:
        elapsed_total = round((time.perf_counter() - start_total_time) * 1000, 2)
        return LookupResult(
            input=raw_input if raw_input is not None else "",
            normalized_input=val_res.normalized_input,
            input_type=val_res.input_type.value,
            dns_status="NOT_ATTEMPTED",
            geolocation_status="NOT_ATTEMPTED",
            overall_status=LookupStatus.INVALID_INPUT,
            error_message=val_res.error_message or "Invalid input format",
            total_response_time_ms=elapsed_total,
        )

    norm_input = val_res.normalized_input
    input_type_str = val_res.input_type.value

    ipv4_addresses: List[str] = []
    ipv6_addresses: List[str] = []
    resolved_addresses: List[str] = []
    selected_ip: Optional[str] = None
    dns_status_str = "NOT_ATTEMPTED"
    dns_time_ms = 0.0

    # Step 2: Route pipeline based on input type
    if val_res.input_type in (InputType.IPV4, InputType.IPV6):
        dns_status_str = "SKIPPED"
        selected_ip = norm_input
        if val_res.input_type == InputType.IPV4:
            ipv4_addresses = [selected_ip]
        else:
            ipv6_addresses = [selected_ip]
        resolved_addresses = [selected_ip]

    elif val_res.input_type == InputType.DOMAIN:
        dns_res = resolve_domain(norm_input)
        dns_status_str = dns_res.status.value
        dns_time_ms = dns_res.resolution_time_ms
        ipv4_addresses = dns_res.ipv4_addresses
        ipv6_addresses = dns_res.ipv6_addresses
        resolved_addresses = dns_res.all_addresses

        if dns_res.status != DNSStatus.SUCCESS or not resolved_addresses:
            elapsed_total = round(
                (time.perf_counter() - start_total_time) * 1000, 2
            )
            return LookupResult(
                input=raw_input,
                normalized_input=norm_input,
                input_type=input_type_str,
                resolved_addresses=resolved_addresses,
                ipv4_addresses=ipv4_addresses,
                ipv6_addresses=ipv6_addresses,
                selected_ip=None,
                dns_response_time_ms=dns_time_ms,
                total_response_time_ms=elapsed_total,
                dns_status=dns_status_str,
                geolocation_status="NOT_ATTEMPTED",
                overall_status=LookupStatus.DNS_FAILED,
                error_message=dns_res.error_message or "DNS resolution failed",
            )

        selected_ip = select_primary_ip(ipv4_addresses, ipv6_addresses)

    if not selected_ip:
        elapsed_total = round((time.perf_counter() - start_total_time) * 1000, 2)
        return LookupResult(
            input=raw_input,
            normalized_input=norm_input,
            input_type=input_type_str,
            resolved_addresses=resolved_addresses,
            ipv4_addresses=ipv4_addresses,
            ipv6_addresses=ipv6_addresses,
            selected_ip=None,
            dns_response_time_ms=dns_time_ms,
            total_response_time_ms=elapsed_total,
            dns_status=dns_status_str,
            geolocation_status="NOT_ATTEMPTED",
            overall_status=LookupStatus.DNS_FAILED,
            error_message="No valid target IP could be selected",
        )

    # Step 3: Perform Geolocation lookup for selected IP
    start_geo = time.perf_counter()
    geo_res = get_geolocation(selected_ip)
    api_time_ms = round((time.perf_counter() - start_geo) * 1000, 2)
    elapsed_total = round((time.perf_counter() - start_total_time) * 1000, 2)

    overall_status = (
        LookupStatus.SUCCESS
        if geo_res.status == GeoStatus.SUCCESS
        else LookupStatus.GEO_FAILED
    )

    return LookupResult(
        input=raw_input,
        normalized_input=norm_input,
        input_type=input_type_str,
        resolved_addresses=resolved_addresses,
        ipv4_addresses=ipv4_addresses,
        ipv6_addresses=ipv6_addresses,
        selected_ip=selected_ip,
        ip_version=geo_res.ip_version,
        country=geo_res.country,
        country_code=geo_res.country_code,
        region=geo_res.region,
        city=geo_res.city,
        latitude=geo_res.latitude,
        longitude=geo_res.longitude,
        timezone=geo_res.timezone,
        organization=geo_res.organization,
        isp=geo_res.isp,
        asn=geo_res.asn,
        dns_response_time_ms=dns_time_ms,
        api_response_time_ms=api_time_ms,
        total_response_time_ms=elapsed_total,
        dns_status=dns_status_str,
        geolocation_status=geo_res.status.value,
        overall_status=overall_status,
        error_message=geo_res.error_message,
    )
