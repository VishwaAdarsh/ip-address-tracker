"""
Configuration package for IP Address Tracker & Geolocation Tool.
"""
from config.settings import (
    BASE_DIR,
    GEO_API_BASE_URL,
    GEO_API_KEY,
    GEO_API_TIMEOUT,
    GEO_PROVIDER_NAME,
)

__all__ = [
    "BASE_DIR",
    "GEO_PROVIDER_NAME",
    "GEO_API_BASE_URL",
    "GEO_API_KEY",
    "GEO_API_TIMEOUT",
]
