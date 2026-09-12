"""
IP PULSE - REST API Layer Package
Provides HTTP/JSON endpoints and static asset delivery for the Stitch web interface.
"""
from api.server import create_server, run_api_server

__all__ = ["create_server", "run_api_server"]
