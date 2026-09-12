"""
Core Input Validation Module for IP Address Tracker & Geolocation Tool.

Responsible for:
- Input normalization (whitespace trimming, scheme stripping)
- Input type classification (DOMAIN, IPV4, IPV6, UNKNOWN)
- Format validation using standard Python libraries
- Returning structured ValidationResult instances
"""
from dataclasses import dataclass
from enum import Enum
import ipaddress
import re
from typing import Optional

# Regex pattern for validating individual domain labels (RFC 1035 / RFC 1123)
# - Length: 1 to 63 characters
# - Allowed characters: ASCII alphanumeric and hyphens
# - Must not start or end with a hyphen
_LABEL_REGEX = re.compile(r"^(?!-)[a-zA-Z0-9-]{1,63}(?<!-)$")


class InputType(Enum):
    """Enumeration of supported input types."""

    DOMAIN = "DOMAIN"
    IPV4 = "IPV4"
    IPV6 = "IPV6"
    UNKNOWN = "UNKNOWN"


@dataclass
class ValidationResult:
    """Structured result returned by the validator."""

    original_input: str
    normalized_input: str
    input_type: InputType
    is_valid: bool
    error_message: Optional[str] = None


def normalize_input(raw_input: str) -> str:
    """
    Clean and normalize user input.

    - Trims leading and trailing whitespace
    - Strips http:// or https:// scheme prefix if present
    - Strips trailing slash if present
    - Converts input to lowercase
    """
    if not raw_input:
        return ""

    cleaned = raw_input.strip()

    # Remove optional scheme prefix
    if cleaned.lower().startswith("https://"):
        cleaned = cleaned[8:]
    elif cleaned.lower().startswith("http://"):
        cleaned = cleaned[7:]

    # Remove trailing slash if it's just path separator (e.g. google.com/)
    if cleaned.endswith("/") and cleaned.count("/") == 1:
        cleaned = cleaned[:-1]

    return cleaned.lower()


def is_valid_ipv4(ip_str: str) -> bool:
    """Check if string is a valid IPv4 address using standard library."""
    if not ip_str:
        return False
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return isinstance(ip_obj, ipaddress.IPv4Address)
    except ValueError:
        return False


def is_valid_ipv6(ip_str: str) -> bool:
    """Check if string is a valid IPv6 address using standard library."""
    if not ip_str:
        return False
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return isinstance(ip_obj, ipaddress.IPv6Address)
    except ValueError:
        return False


def is_valid_domain(domain_str: str) -> bool:
    """
    Check if string is a valid domain name.

    - Total length must be between 1 and 253 characters
    - Labels separated by dots
    - Each label 1-63 characters, alphanumeric + hyphens
    - Top-Level Domain (TLD) must not be purely numeric
    """
    if not domain_str or len(domain_str) > 253:
        return False

    # Disallow invalid URI/email characters
    if any(char in domain_str for char in ("@", ":", "/", " ", "\\", "?", "#")):
        return False

    labels = domain_str.split(".")
    
    # Require at least two labels for a standard internet domain (e.g., domain.com)
    # or one valid label if hostnames are allowed. For public lookups, 2+ labels is standard.
    if len(labels) < 2:
        return False

    # Validate each label
    for label in labels:
        if not _LABEL_REGEX.match(label):
            return False

    # Top-Level Domain (last label) must not be purely numeric (e.g., to prevent invalid IPv4s like 256.0.0.1)
    tld = labels[-1]
    if tld.isdigit():
        return False

    return True


def validate_input(raw_input: str) -> ValidationResult:
    """
    Validate user input and return a structured ValidationResult.

    Flow:
    1. Check for empty/None input
    2. Normalize input string
    3. Check for IPv4 address
    4. Check for IPv6 address
    5. Check for Domain name
    6. Return result with appropriate InputType and error message if invalid
    """
    if raw_input is None or not raw_input.strip():
        return ValidationResult(
            original_input=raw_input if raw_input is not None else "",
            normalized_input="",
            input_type=InputType.UNKNOWN,
            is_valid=False,
            error_message="Input cannot be empty",
        )

    normalized = normalize_input(raw_input)

    # 1. Test IPv4
    if is_valid_ipv4(normalized):
        return ValidationResult(
            original_input=raw_input,
            normalized_input=normalized,
            input_type=InputType.IPV4,
            is_valid=True,
            error_message=None,
        )

    # 2. Test IPv6
    if is_valid_ipv6(normalized):
        return ValidationResult(
            original_input=raw_input,
            normalized_input=normalized,
            input_type=InputType.IPV6,
            is_valid=True,
            error_message=None,
        )

    # 3. Test Domain
    if is_valid_domain(normalized):
        return ValidationResult(
            original_input=raw_input,
            normalized_input=normalized,
            input_type=InputType.DOMAIN,
            is_valid=True,
            error_message=None,
        )

    # 4. Unknown / Invalid input
    return ValidationResult(
        original_input=raw_input,
        normalized_input=normalized,
        input_type=InputType.UNKNOWN,
        is_valid=False,
        error_message="Invalid domain or IP address",
    )
