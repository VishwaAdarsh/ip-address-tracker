"""
Core IP Geolocation Service Module for IP Address Tracker & Geolocation Tool.

Responsible for:
- Querying the configured external Geolocation API (default: ipapi.co) over HTTPS
- Enforcing request timeouts and handling HTTP status codes, rate limits, and network errors
- Security: Secrets loaded via settings.py / environment, never hardcoded
- Returning standardized GeoResult objects via core/normalizer.py
"""
import http.client
import json
import socket
import urllib.error
import urllib.request
from typing import Optional

from config.settings import GEO_API_BASE_URL, GEO_API_KEY, GEO_API_TIMEOUT
from core.normalizer import GeoResult, GeoStatus, normalize_geo_response
from core.validator import is_valid_ipv4, is_valid_ipv6


def get_geolocation(
    ip_address: str, timeout: Optional[float] = None
) -> GeoResult:
    """
    Retrieve approximate geolocation and network information for a public IP address.

    Parameters:
    - ip_address: The target IPv4 or IPv6 address string.
    - timeout: Request timeout in seconds (defaults to GEO_API_TIMEOUT from settings).

    Returns:
    - A normalized GeoResult object containing location data or error details.
    """
    if not ip_address:
        return normalize_geo_response(
            None, "", GeoStatus.INVALID_IP, "IP address cannot be empty"
        )

    clean_ip = ip_address.strip()
    if not (is_valid_ipv4(clean_ip) or is_valid_ipv6(clean_ip)):
        return normalize_geo_response(
            None,
            clean_ip,
            GeoStatus.INVALID_IP,
            f"Invalid IPv4 or IPv6 address: '{clean_ip}'",
        )

    # Use specified timeout or fall back to settings
    req_timeout = timeout if timeout is not None else GEO_API_TIMEOUT

    # Construct request URL
    base_url = GEO_API_BASE_URL.rstrip("/")
    request_url = f"{base_url}/{clean_ip}/json/"
    if GEO_API_KEY:
        request_url += f"?key={GEO_API_KEY}"

    headers = {"User-Agent": "IP-Address-Tracker/1.0 (College Project)"}

    try:
        req = urllib.request.Request(request_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=req_timeout) as response:
            status_code = response.getcode()
            response_bytes = response.read()

            if status_code != 200:
                return normalize_geo_response(
                    None,
                    clean_ip,
                    GeoStatus.API_HTTP_ERROR,
                    f"HTTP Status {status_code} returned by geolocation provider",
                )

            try:
                raw_json = json.loads(response_bytes.decode("utf-8"))
                return normalize_geo_response(raw_json, clean_ip)
            except json.JSONDecodeError:
                return normalize_geo_response(
                    None,
                    clean_ip,
                    GeoStatus.INVALID_RESPONSE,
                    "Invalid JSON response received from geolocation provider",
                )

    except urllib.error.HTTPError as e:
        if e.code == 429:
            return normalize_geo_response(
                None,
                clean_ip,
                GeoStatus.API_RATE_LIMIT,
                "Geolocation service rate limit exceeded (HTTP 429)",
            )
        elif e.code in (401, 403):
            return normalize_geo_response(
                None,
                clean_ip,
                GeoStatus.API_AUTH_ERROR,
                f"Geolocation service authentication error (HTTP {e.code})",
            )
        elif e.code == 404:
            return normalize_geo_response(
                None,
                clean_ip,
                GeoStatus.API_NO_DATA,
                "No geolocation data available for specified IP",
            )
        else:
            return normalize_geo_response(
                None,
                clean_ip,
                GeoStatus.API_HTTP_ERROR,
                f"Geolocation service HTTP Error {e.code}: {e.reason}",
            )

    except urllib.error.URLError as e:
        if isinstance(e.reason, socket.timeout):
            return normalize_geo_response(
                None,
                clean_ip,
                GeoStatus.API_TIMEOUT,
                "Geolocation service request timed out",
            )
        return normalize_geo_response(
            None,
            clean_ip,
            GeoStatus.NETWORK_ERROR,
            f"Network error while connecting to geolocation service: {e.reason}",
        )

    except (socket.timeout, TimeoutError):
        return normalize_geo_response(
            None,
            clean_ip,
            GeoStatus.API_TIMEOUT,
            "Geolocation service request timed out",
        )

    except (http.client.HTTPException, ConnectionError) as e:
        return normalize_geo_response(
            None,
            clean_ip,
            GeoStatus.NETWORK_ERROR,
            f"HTTP Connection error: {str(e)}",
        )

    except Exception as e:
        return normalize_geo_response(
            None,
            clean_ip,
            GeoStatus.NETWORK_ERROR,
            f"Unexpected error during geolocation lookup: {str(e)}",
        )
