# api/index.py — Vercel entry point
import sys
import os

# Make sure backend/ is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app