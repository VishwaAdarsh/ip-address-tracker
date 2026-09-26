"""
IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform
Backend Application Entry Point
"""
import argparse
import logging
import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(1, str(PROJECT_ROOT))

try:
    from backend.api.server import IPPulseRequestHandler, create_server
    from backend.database.db import init_db
except ImportError:
    from backend.api.server import IPPulseRequestHandler, create_server
    from backend.database.db import init_db

# Top-level serverless and WSGI/handler entrypoint export
app = IPPulseRequestHandler
handler = IPPulseRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("IPPulse")


def main() -> None:
    default_host = os.environ.get("HOST", "127.0.0.1")
    default_port = int(os.environ.get("PORT", "8000"))

    parser = argparse.ArgumentParser(
        description="IP PULSE - IP Intelligence, Geolocation & Website Risk Analysis Platform"
    )
    parser.add_argument("--host", default=default_host, help=f"Host interface to bind (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port to listen on (default: {default_port})")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically launch web browser")
    args = parser.parse_args()

    init_db()

    url = f"http://{args.host}:{args.port}/"
    banner = f"""
================================================================================
   IP PULSE - IP Intelligence, Geolocation & Website Risk Analysis Platform
   Stitch Web Interface & Multi-Threaded Python REST API Engine
================================================================================
   * Web Application:  {url}
   * System Telemetry: {url}api/status
   * Local Database:   data/ip_tracker.db
   * Primary Protocol: Manual-First Field Study & Multi-Layered Intelligence

   Press Ctrl+C to safely shutdown the server.
================================================================================
"""
    print(banner, flush=True)

    try:
        server = create_server(host=args.host, port=args.port)
    except OSError as e:
        logger.error(f"Could not bind to {args.host}:{args.port}: {e}")
        logger.info("Try specifying an alternate port using: python backend/app.py --port 8080")
        sys.exit(1)

    is_headless = args.no_browser or "RENDER" in os.environ or "PORT" in os.environ
    if not is_headless:
        def open_browser():
            time.sleep(0.6)
            try:
                webbrowser.open(url)
            except Exception as e:
                logger.warning(f"Could not automatically launch browser: {e}")

        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Gracefully shutting down IP PULSE Platform...", flush=True)
    finally:
        server.server_close()
        logger.info("Server terminated cleanly.")


if __name__ == "__main__":
    main()