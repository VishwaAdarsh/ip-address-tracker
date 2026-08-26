"""
Core DNS Resolution Module for IP Address Tracker & Geolocation Tool.

Responsible for:
- Resolving domain names to public IPv4 and IPv6 addresses using standard socket API
- Categorizing returned IP addresses into IPv4 and IPv6 lists
- Preserving multiple IP addresses without hardcoding or duplicate entries
- Measuring DNS resolution timing in milliseconds
- Handling DNS failures gracefully and returning structured DNSResult objects
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import socket
import time
from typing import List, Optional

from core.validator import InputType, validate_input


class DNSStatus(Enum):
    """Enumeration of DNS resolution statuses."""

    SUCCESS = "SUCCESS"
    DNS_FAILED = "DNS_FAILED"
    INVALID_DOMAIN = "INVALID_DOMAIN"


@dataclass
class DNSResult:
    """Structured result returned by the DNS resolver."""

    domain: str
    ipv4_addresses: List[str] = field(default_factory=list)
    ipv6_addresses: List[str] = field(default_factory=list)
    all_addresses: List[str] = field(default_factory=list)
    resolution_time_ms: float = 0.0
    status: DNSStatus = DNSStatus.DNS_FAILED
    error_message: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


def resolve_domain(domain_input: str) -> DNSResult:
    """
    Resolve a domain name into its available IPv4 and IPv6 addresses.

    Steps:
    1. Validate input using Phase 2 core/validator.py
    2. Measure resolution time using high-precision counter
    3. Query socket.getaddrinfo for AF_UNSPEC (IPv4 and IPv6)
    4. Separate addresses into IPv4 and IPv6 lists, maintaining order without duplicates
    5. Handle socket errors gracefully and return structured DNSResult
    """
    # 1. Validate input first
    validation = validate_input(domain_input)

    # Handle IP address passed directly
    if validation.is_valid and validation.input_type in (
        InputType.IPV4,
        InputType.IPV6,
    ):
        ip = validation.normalized_input
        ipv4_list = [ip] if validation.input_type == InputType.IPV4 else []
        ipv6_list = [ip] if validation.input_type == InputType.IPV6 else []
        return DNSResult(
            domain=domain_input,
            ipv4_addresses=ipv4_list,
            ipv6_addresses=ipv6_list,
            all_addresses=[ip],
            resolution_time_ms=0.0,
            status=DNSStatus.SUCCESS,
            error_message=None,
        )

    if not validation.is_valid or validation.input_type != InputType.DOMAIN:
        return DNSResult(
            domain=domain_input if domain_input is not None else "",
            status=DNSStatus.INVALID_DOMAIN,
            error_message=validation.error_message or "Invalid domain input",
        )

    target_domain = validation.normalized_input
    ipv4_addresses: List[str] = []
    ipv6_addresses: List[str] = []
    all_addresses: List[str] = []

    start_time = time.perf_counter()

    try:
        # Perform DNS lookup for both IPv4 (AF_INET) and IPv6 (AF_INET6)
        addr_info = socket.getaddrinfo(
            target_domain, None, socket.AF_UNSPEC, socket.SOCK_STREAM
        )
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        for item in addr_info:
            family, _, _, _, sockaddr = item
            ip_str = sockaddr[0]

            if ip_str not in all_addresses:
                all_addresses.append(ip_str)

            if family == socket.AF_INET and ip_str not in ipv4_addresses:
                ipv4_addresses.append(ip_str)
            elif family == socket.AF_INET6 and ip_str not in ipv6_addresses:
                ipv6_addresses.append(ip_str)

        if not all_addresses:
            return DNSResult(
                domain=target_domain,
                resolution_time_ms=elapsed_ms,
                status=DNSStatus.DNS_FAILED,
                error_message="No IP addresses returned by DNS resolver",
            )

        return DNSResult(
            domain=target_domain,
            ipv4_addresses=ipv4_addresses,
            ipv6_addresses=ipv6_addresses,
            all_addresses=all_addresses,
            resolution_time_ms=elapsed_ms,
            status=DNSStatus.SUCCESS,
            error_message=None,
        )

    except socket.gaierror as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return DNSResult(
            domain=target_domain,
            resolution_time_ms=elapsed_ms,
            status=DNSStatus.DNS_FAILED,
            error_message=f"Name resolution failed: {e.strerror or str(e)}",
        )
    except Exception as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return DNSResult(
            domain=target_domain,
            resolution_time_ms=elapsed_ms,
            status=DNSStatus.DNS_FAILED,
            error_message=f"DNS resolution error: {str(e)}",
        )
