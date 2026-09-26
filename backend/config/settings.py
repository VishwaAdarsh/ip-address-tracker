"""
Configuration settings for IP Address Tracker & Geolocation Tool.

Loads configuration from environment variables and local .env file.
"""
import os
from pathlib import Path

# Project root and backend directories
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
BASE_DIR = PROJECT_ROOT


def load_env_file(env_path: Path = PROJECT_ROOT / ".env") -> None:
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

# AI Explanation Configuration (Phase 22)
AI_PROVIDER = os.environ.get("AI_PROVIDER", "rule_based").lower()
AI_API_KEY = os.environ.get("AI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
AI_MODEL = os.environ.get("AI_MODEL", "gemini-2.5-flash")
AI_TIMEOUT = float(os.environ.get("AI_TIMEOUT", "10.0"))
AI_ENABLED = os.environ.get("AI_ENABLED", "true").lower() in ("true", "1", "yes")

# Server Network Configuration
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))

# CORS Configuration
DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
env_origins = os.environ.get("ALLOWED_ORIGINS", "")
if env_origins:
    ALLOWED_ORIGINS = [o.strip() for o in env_origins.split(",") if o.strip()]
else:
    ALLOWED_ORIGINS = DEFAULT_ALLOWED_ORIGINS

ALLOW_ORIGIN_REGEX = os.environ.get("ALLOW_ORIGIN_REGEX", r"^https:\/\/.*\.vercel\.app$")
