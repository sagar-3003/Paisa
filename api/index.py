import sys
import os
import traceback

# Add backend to path so Vercel serverless function can find it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scratch', 'paisa', 'backend'))

try:
    from main import app  # noqa: F401 — Vercel uses this `app` ASGI object
except Exception as e:
    # Surface import errors as a minimal ASGI app for debugging
    import json
    tb = traceback.format_exc()
    async def app(scope, receive, send):
        if scope['type'] == 'http':
            body = json.dumps({"import_error": str(e), "traceback": tb}).encode()
            await send({"type": "http.response.start", "status": 500, "headers": [[b"content-type", b"application/json"]]})
            await send({"type": "http.response.body", "body": body})
