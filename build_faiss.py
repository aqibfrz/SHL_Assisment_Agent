"""
Build artifacts/faiss_index from data/SHL_catalogue.json.

Run during deploy (Render build step) so the web process starts quickly and
binds $PORT before health checks time out. Local dev can still rely on
app lifespan to build on first run if artifacts are missing.

Usage (repo root):
  python build_faiss.py
"""
from __future__ import annotations

from pathlib import Path

from src.rag.ingestion import build_index


def main() -> None:
    catalog = Path("data/SHL_catalogue.json")
    if not catalog.is_file():
        raise SystemExit(f"Missing {catalog} — add the SHL catalog JSON before building.")
    build_index()
    print(
        "Done. On Render: use this script only in the BUILD command, not Start. "
        "Start command must be: python run_api.py"
    )


if __name__ == "__main__":
    main()
