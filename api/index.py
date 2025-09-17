# api/index.py (diagnostic version)
# Use this temporarily to see why your Vercel function is crashing.

from fastapi import FastAPI
import traceback

app = FastAPI()

_error = None
_tb = None
_real_app = None

try:
    from backend.app.main import app as _real_app
except Exception as e:
    _error = repr(e)
    _tb = traceback.format_exc()

if _real_app is not None:
    # If import worked, mount the real app
    app.mount("/", _real_app)
else:
    # If import failed, show error info
    @app.get("/{path:path}")
    async def diag(path: str = ""):
        return {
            "status": "import_failed",
            "error": _error,
            "traceback": _tb,
        }

    @app.get("/health")
    async def health():
        return {"ok": False, "reason": "import_failed"}
