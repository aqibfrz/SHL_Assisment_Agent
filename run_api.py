"""
Run API from repo root with a sane default bind (helps some Windows setups).

Examples:
  .\\.myev\\Scripts\\python.exe run_api.py
  $env:PORT=8765; .\\.myev\\Scripts\\python.exe run_api.py

Cross-origin UI: set `CORS_ORIGINS` (comma-separated, or *) and point the meta
`api-base` in web/index.html to this server (see comment there). Use `.env` for
secrets (e.g. GROQ_API_KEY).
"""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("HOST", "127.0.0.1")
    reload_env = os.environ.get("UVICORN_RELOAD", "").lower()
    reload = reload_env in ("1", "true", "yes")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
