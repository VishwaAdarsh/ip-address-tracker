"""
Core package for validation, resolution, geolocation, and normalization services.
"""
from core.dns_resolver import DNSResult, DNSStatus, resolve_domain
from core.geo_service import get_geolocation
from core.normalizer import GeoResult, GeoStatus, normalize_geo_response
from core.validator import (
    InputType,
    ValidationResult,
    is_valid_domain,
    is_valid_ipv4,
    is_valid_ipv6,
    normalize_input,
    validate_input,
)

__all__ = [
    "InputType",
    "ValidationResult",
    "is_valid_domain",
    "is_valid_ipv4",
    "is_valid_ipv6",
    "normalize_input",
    "validate_input",
    "DNSResult",
    "DNSStatus",
    "resolve_domain",
    "GeoResult",
    "GeoStatus",
    "get_geolocation",
    "normalize_geo_response",
]
