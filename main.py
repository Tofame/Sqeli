"""
main.py — Sqeli entry point.
"""

import sys
import os

# Ensure the project root is on sys.path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import SqeliApp

if __name__ == "__main__":
    app = SqeliApp()
    sys.exit(app.run())
