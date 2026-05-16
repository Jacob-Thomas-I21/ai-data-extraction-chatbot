"""Convenience entry point for seeding the database.

Usage:
    python seed.py
"""

import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.seed import seed, print_summary

if __name__ == "__main__":
    seed()
    print_summary()
