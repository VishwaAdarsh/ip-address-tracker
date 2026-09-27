from abc import ABC, abstractmethod
import http.client
import json
import logging
import socket
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request

from backend.config.settings import GEO_API_BASE_URL, GEO_API_KEY, GEO_API_TIMEOUT, GEO_PROVIDER_NAME
from backend.providers.normalizer import GeoResult, GeoStatus, normalize_geo_response
from backend.utils.validator import is_valid_ipv4, is_valid_ipv6

logger = logging.getLogger("ip_pulse.geo_service")

# -----------------------------------------------------------------------------
# In-Memory Geolocation Cache with Explicit TTL (Requirement 11)
# -----------------------------------------------------------------------------
# Maps clean_ip -> (GeoResult, expiry_epoch_timestamp)
_GEO_CACHE: Dict[str, Tuple[GeoResult, float]] = {}
DEFAULT_CACHE_TTL_SECONDS = 3600.0  # 1 hour standard TTL
ERROR_CACHE_TTL_SECONDS = 30.0      # 30 seconds for transient errors


def get_cached_geo(ip: str) -> Optional[GeoResult]:
    """Retrieve cached GeoResult if present and not expired."""
    clean_ip = ip.strip()
    if clean_ip in _GEO_CACHE:
        result, expiry = _GEO_CACHE[clean_ip]
        if time.time() < expiry:
            return result
        else:
            _GEO_CACHE.pop(clean_ip, None)
    return None


def cache_geo(ip: str, result: GeoResult, ttl: float = DEFAULT_CACHE_TTL_SECONDS) -> None:
    """Store GeoResult in in-memory cache with explicit expiry."""
    clean_ip = ip.strip()
    # Cache management: keep cache bounded to avoid unbound memory growth
    if len(_GEO_CACHE) > 5000:
        # Purge expired entries
        now = time.time()
        expired = [k for k, (_, exp) in _GEO_CACHE.items() if exp <= now]
        for k in expired:
            _GEO_CACHE.pop(k, None)
        if len(_GEO_CACHE) > 5000:
            # Drop oldest 500 items if still over capacity
            for k in list(_GEO_CACHE.keys())[:500]:
                _GEO_CACHE.pop(k, None)

    _GEO_CACHE[clean_ip] = (result, time.time() + ttl)


def clear_geo_cache() -> None:
    """Flush all cached geolocation entries."""
    _GEO_CACHE.clear()


# -----------------------------------------------------------------------------
# Geolocation Provider Abstraction (Requirement 12)
# -----------------------------------------------------------------------------
class BaseGeoProvider(ABC):
    """Abstract base class for external IP geolocation providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier name (e.g. 'ipapi.co')."""
        pass

    @abstractmethod
    def lookup(
        self, ip_address: str, timeout: float
    ) -> Tuple[Optional[Dict[str, Any]], GeoStatus, Optional[str]]:
        """
        Execute provider lookup.
        Returns: (raw_json_dict, status, error_message)
        """
        pass


class IPAPICoProvider(BaseGeoProvider):
    """Primary Geolocation Provider: ipapi.co."""

    def __init__(self, base_url: str = GEO_API_BASE_URL, api_key: str = GEO_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "ipapi.co"

    def lookup(
        self, ip_address: str, timeout: float
    ) -> Tuple[Optional[Dict[str, Any]], GeoStatus, Optional[str]]:
        request_url = f"{self.base_url}/{ip_address}/json/"
        if self.api_key:
            request_url += f"?key={self.api_key}"

        # Standard, accepted User-Agent that avoids bot-impersonation triggers
        headers = {
            "User-Agent": "IP-Pulse/2.0 (Cyber-Intelligence-Platform; +https://ip-pulse.local)",
            "Accept": "application/json",
        }

        try:
            req = urllib.request.Request(request_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                response_bytes = response.read()

                if status_code != 200:
                    return None, GeoStatus.API_HTTP_ERROR, f"HTTP Status {status_code} returned by ipapi.co"

                try:
                    raw_json = json.loads(response_bytes.decode("utf-8"))
                    if raw_json.get("error") is True:
                        reason = raw_json.get("reason", "Unknown API error")
                        stat = GeoStatus.API_RATE_LIMIT if "rate limit" in str(reason).lower() else GeoStatus.API_NO_DATA
                        return raw_json, stat, f"ipapi.co reported error: {reason}"
                    return raw_json, GeoStatus.SUCCESS, None
                except json.JSONDecodeError:
                    return None, GeoStatus.INVALID_RESPONSE, "Invalid JSON received from ipapi.co"

        except urllib.error.HTTPError as e:
            if e.code == 429:
                return None, GeoStatus.API_RATE_LIMIT, "ipapi.co rate limit exceeded (HTTP 429)"
            elif e.code in (401, 403):
                return None, GeoStatus.API_AUTH_ERROR, f"ipapi.co authentication / access error (HTTP {e.code})"
            elif e.code == 404:
                return None, GeoStatus.API_NO_DATA, f"No geolocation data found on ipapi.co for {ip_address}"
            else:
                return None, GeoStatus.API_HTTP_ERROR, f"ipapi.co HTTP error {e.code}: {e.reason}"
        except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
            return None, GeoStatus.API_TIMEOUT, f"ipapi.co request timeout or connection error: {str(e)}"
        except Exception as e:
            return None, GeoStatus.NETWORK_ERROR, f"Unexpected error querying ipapi.co: {str(e)}"


class IPAPIComProvider(BaseGeoProvider):
    """Secondary Fallback Geolocation Provider: ip-api.com."""

    def __init__(self, base_url: str = "http://ip-api.com"):
        self.base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return "ip-api.com"

    def lookup(
        self, ip_address: str, timeout: float
    ) -> Tuple[Optional[Dict[str, Any]], GeoStatus, Optional[str]]:
        fields = "status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
        request_url = f"{self.base_url}/json/{ip_address}?fields={fields}"

        headers = {
            "User-Agent": "IP-Pulse/2.0 (Cyber-Intelligence-Platform; +https://ip-pulse.local)",
            "Accept": "application/json",
        }

        try:
            req = urllib.request.Request(request_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                response_bytes = response.read()

                if status_code != 200:
                    return None, GeoStatus.API_HTTP_ERROR, f"HTTP Status {status_code} returned by ip-api.com"

                try:
                    raw_json = json.loads(response_bytes.decode("utf-8"))
                    if raw_json.get("status") == "fail":
                        msg = raw_json.get("message", "Lookup failed")
                        return raw_json, GeoStatus.API_NO_DATA, f"ip-api.com reported: {msg}"
                    return raw_json, GeoStatus.SUCCESS, None
                except json.JSONDecodeError:
                    return None, GeoStatus.INVALID_RESPONSE, "Invalid JSON received from ip-api.com"

        except urllib.error.HTTPError as e:
            if e.code == 429:
                return None, GeoStatus.API_RATE_LIMIT, "ip-api.com rate limit exceeded (HTTP 429)"
            elif e.code in (401, 403):
                return None, GeoStatus.API_AUTH_ERROR, f"ip-api.com authentication / access error (HTTP {e.code})"
            elif e.code == 404:
                return None, GeoStatus.API_NO_DATA, f"No geolocation data found on ip-api.com for {ip_address}"
            return None, GeoStatus.API_HTTP_ERROR, f"ip-api.com HTTP error {e.code}: {e.reason}"
        except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
            return None, GeoStatus.API_TIMEOUT, f"ip-api.com request timeout: {str(e)}"
        except Exception as e:
            return None, GeoStatus.NETWORK_ERROR, f"Unexpected error querying ip-api.com: {str(e)}"


# -----------------------------------------------------------------------------
# Main Geolocation Dispatcher
# -----------------------------------------------------------------------------
def get_geolocation(
    ip_address: str,
    timeout: Optional[float] = None,
    bypass_cache: bool = False,
    preferred_provider: Optional[str] = None,
) -> GeoResult:
    """
    Retrieve canonical geolocation and network telemetry for a public IP address.

    Workflow:
    1. Validate IP address
    2. Check in-memory TTL cache (unless bypass_cache=True)
    3. Query Primary Provider (configured via GEO_PROVIDER_NAME, default ipapi.co)
    4. If primary fails or is rate-limited, query Secondary Provider (ip-api.com)
    5. Normalize into CanonicalGeo structure, record exact provider name and timestamp
    6. Cache and return standardized GeoResult
    """
    if not ip_address:
        return normalize_geo_response(
            None, "", GeoStatus.INVALID_IP, "IP address cannot be empty", provider="None"
        )

    clean_ip = ip_address.strip()
    if not (is_valid_ipv4(clean_ip) or is_valid_ipv6(clean_ip)):
        return normalize_geo_response(
            None,
            clean_ip,
            GeoStatus.INVALID_IP,
            f"Invalid IPv4 or IPv6 address: '{clean_ip}'",
            provider="None",
        )

    # Check cache
    if not bypass_cache:
        cached = get_cached_geo(clean_ip)
        if cached:
            return cached

    req_timeout = timeout if timeout is not None else GEO_API_TIMEOUT

    # Setup provider chain
    p_name = (preferred_provider or GEO_PROVIDER_NAME).lower()
    primary_provider: BaseGeoProvider
    secondary_provider: BaseGeoProvider

    if p_name == "ip-api.com":
        primary_provider = IPAPIComProvider()
        secondary_provider = IPAPICoProvider()
    else:
        primary_provider = IPAPICoProvider()
        secondary_provider = IPAPIComProvider()

    providers_chain: List[BaseGeoProvider] = [primary_provider, secondary_provider]
    last_result: Optional[GeoResult] = None

    for provider in providers_chain:
        raw_json, status, err_msg = provider.lookup(clean_ip, timeout=req_timeout)

        if status == GeoStatus.SUCCESS and raw_json:
            result = normalize_geo_response(
                raw_json,
                clean_ip,
                status=GeoStatus.SUCCESS,
                provider=provider.name,
            )
            # Store in cache
            cache_geo(clean_ip, result, ttl=DEFAULT_CACHE_TTL_SECONDS)
            return result
        else:
            logger.info(
                f"Geolocation provider {provider.name} failed for {clean_ip}: {err_msg} ({status.value})"
            )
            last_result = normalize_geo_response(
                raw_json,
                clean_ip,
                status=status,
                error_message=err_msg,
                provider=provider.name,
            )

    # If all providers failed, cache error briefly to prevent hammering
    final_error = last_result or normalize_geo_response(
        None, clean_ip, GeoStatus.NETWORK_ERROR, "All geolocation provider endpoints failed", provider="None"
    )
    cache_geo(clean_ip, final_error, ttl=ERROR_CACHE_TTL_SECONDS)
    return final_error
