import sys
import os

# Add backend to path so Vercel serverless function can find it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scratch', 'paisa', 'backend'))

from main import app  # noqa: F401 — Vercel uses this `app` ASGI object
