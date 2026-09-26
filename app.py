"""
IP PULSE — Root Launcher Wrapper
Delegates to backend.app.main() in deployment-ready architecture.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(1, str(ROOT_DIR))

from backend.app import app, handler, main

if __name__ == "__main__":
    main()