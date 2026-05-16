"""Start both backend and frontend servers with a single command.

Usage:
    python start.py
"""

import subprocess
import sys
import os
import signal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def main():
    processes = []

    try:
        # Start FastAPI backend
        print("🚀 Starting backend on http://localhost:8000 ...")
        backend = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
            cwd=str(PROJECT_ROOT),
        )
        processes.append(backend)

        # Start Vite frontend
        print("🚀 Starting frontend on http://localhost:5173 ...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        frontend = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=str(FRONTEND_DIR),
        )
        processes.append(frontend)

        print("\n✅ Both servers running!")
        print("   → Frontend: http://localhost:5173")
        print("   → Backend:  http://localhost:8000")
        print("   → API Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop both.\n")

        # Wait for either process to exit
        for p in processes:
            p.wait()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
        print("Done.")


if __name__ == "__main__":
    main()
