"""
Thin client for the optional model server (see model_server.py).

Why this exists: every OCR job runs as a brand-new subprocess (main.py),
so the module-level model caches in layout_block_detection.py and
super_resolution.py never actually help - a fresh subprocess means a
fresh Python interpreter means the cache starts empty again every time.

model_server.py is a separate, long-lived process that loads those same
models ONCE and keeps them warm. This module is the client side: it lets
main.py's subprocess call into that warm server instead of loading the
model itself, IF the server is configured and reachable.

Nothing here is required. If OCR_MODEL_SERVER_URL isn't set, or the
server isn't running, every caller falls back to the exact same
in-process loading behavior as before - this is purely an optional
speed-up, never a hard dependency.
"""
from __future__ import annotations

import json
import os
from urllib import error as urllib_error
from urllib import request as urllib_request

MODEL_SERVER_URL = (os.getenv("OCR_MODEL_SERVER_URL") or "").rstrip("/")
MODEL_SERVER_TIMEOUT = float(os.getenv("OCR_MODEL_SERVER_TIMEOUT_SECONDS", "60"))

# Once a call in this process fails (server not running / crashed), stop
# trying it for the rest of this job - otherwise every remaining page
# would pay the full connect-timeout before falling back.
_server_unavailable = False


def is_model_server_configured() -> bool:
    return bool(MODEL_SERVER_URL) and not _server_unavailable


def call_model_server(path: str, payload: dict) -> dict:
    """POST payload to the model server. Raises on any failure - callers
    are expected to catch this and fall back to local execution."""
    global _server_unavailable

    if not MODEL_SERVER_URL:
        raise RuntimeError("OCR_MODEL_SERVER_URL is not set")
    if _server_unavailable:
        raise RuntimeError("Model server already marked unavailable for this run")

    url = f"{MODEL_SERVER_URL}/{path.lstrip('/')}"
    body = json.dumps(payload).encode("utf-8")
    request = urllib_request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib_request.urlopen(request, timeout=MODEL_SERVER_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"[MODEL_SERVER] Call to {url} failed, disabling for this run: {exc}")
        _server_unavailable = True
        raise
