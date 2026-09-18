"""
IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform
Main Application Entry Point

Architecture:
- Primary UI: Stitch Obsidian Dark Web Application (frontend/)
- Backend: Multi-Threaded REST API Server (api/server.py)
- Engine: Multi-layered IP Resolution, DNS, Geolocation, Security Scanner,
          IP Intelligence, Dual Risk Engine, and SQLite Persistence.

Usage:
  python app.py                     # Starts server and opens web browser
  python app.py --port 8080         # Custom port
  python app.py --no-browser        # Headless server mode
  python app.py --legacy            # Fallback legacy Tkinter desktop UI
"""
import argparse
import logging
import sys
import threading
import time
import webbrowser

from api.server import IPPulseRequestHandler, create_server
from database.db import init_db

# Vercel detects Python functions by a top-level app/handler export.
app = IPPulseRequestHandler
handler = IPPulseRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("IPPulse")


def main() -> None:
    # 1. Parse Command-Line Options
    parser = argparse.ArgumentParser(
        description="IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform"
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically launch web browser")
    parser.add_argument("--legacy", action="store_true", help="Launch legacy Tkinter desktop UI")
    args = parser.parse_args()

    # 2. Ensure Database Schema Exists
    init_db()

    # 3. Optional Legacy Tkinter Fallback
    if args.legacy:
        logger.info("Launching legacy Tkinter interface as requested by flag --legacy...")
        try:
            from gui.main_window import MainWindow as LegacyWindow
            app = LegacyWindow()
            app.mainloop()
            return
        except Exception as e:
            logger.error(f"Failed to launch legacy Tkinter UI: {e}")
            sys.exit(1)

    # 4. Primary Application: Stitch Web UI + Python REST API Server
    url = f"http://{args.host}:{args.port}/"
    banner = f"""
================================================================================
   IP PULSE — IP Intelligence, Geolocation & Website Risk Analysis Platform
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
        logger.info("Try specifying an alternate port using: python app.py --port 8080")
        sys.exit(1)

    # Automatically launch browser in background after short delay
    if not args.no_browser:
        def open_browser():
            time.sleep(0.6)
            try:
                webbrowser.open(url)
            except Exception as e:
                logger.warning(f"Could not automatically launch browser: {e}")

        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

    # Run Server
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Gracefully shutting down IP PULSE Platform...", flush=True)
    finally:
        server.server_close()
        logger.info("Server terminated cleanly.")


if __name__ == "__main__":
    main()
