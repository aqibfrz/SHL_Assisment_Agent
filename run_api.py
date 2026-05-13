"""
Run API from repo root with a sane default bind (helps some Windows setups).

Examples:
  .\\.myev\\Scripts\\python.exe run_api.py
  $env:PORT=8765; .\\.myev\\Scripts\\python.exe run_api.py

Cross-origin UI: set `CORS_ORIGINS` (comma-separated, or *) and point the meta
`api-base` in web/index.html to this server (see comment there). Use `.env` for
secrets (e.g. GROQ_API_KEY).

Render: set Build Command to build the FAISS index during the image build (fast
bind on $PORT), e.g.
  pip install -r requirements.txt && python build_faiss.py
Otherwise startup runs ingestion inside lifespan and Render may log "No open
ports detected" until the index finishes.
"""
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("HOST", "0.0.0.0")
    reload_env = os.environ.get("UVICORN_RELOAD", "").lower()
    reload = reload_env in ("1", "true", "yes")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
