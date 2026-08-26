"""
Core package for validation, resolution, geolocation, and normalization services.
"""
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
]
