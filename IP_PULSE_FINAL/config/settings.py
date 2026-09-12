"""
Configuration settings for IP Address Tracker & Geolocation Tool.

Loads configuration from environment variables and local .env file.
"""
import os
from pathlib import Path

# Base directory of project
BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(env_path: Path = BASE_DIR / ".env") -> None:
    """
    Simple parser for local .env file.
    Does not overwrite existing environment variables.
    """
    if not env_path.exists() or not env_path.is_file():
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


# Load .env file on module import
load_env_file()

# Geolocation API Configuration
GEO_PROVIDER_NAME = os.environ.get("GEO_PROVIDER_NAME", "ipapi.co")
GEO_API_BASE_URL = os.environ.get("GEO_API_BASE_URL", "https://ipapi.co")
GEO_API_KEY = os.environ.get("GEO_API_KEY", "")
GEO_API_TIMEOUT = float(os.environ.get("GEO_API_TIMEOUT", "5.0"))
