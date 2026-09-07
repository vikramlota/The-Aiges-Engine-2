"""
Developer Launcher Script for The Aiges Engine.

Starts backend (FastAPI :8000).

Run:
    python3 scripts/run_dev.py
"""
import sys
import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def run():
    print("=" * 60)
    print("🚀 Starting The Aiges Engine Development Server")
    print("=" * 60)
    print("[*] Host: 0.0.0.0")
    print("[*] Port: 8000")
    print("[*] Docs: http://localhost:8000/docs")
    print("=" * 60)

    try:
        import uvicorn
        uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")


if __name__ == "__main__":
    run()
