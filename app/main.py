import os

# Small containers (e.g. Render 512MB): cap BLAS/thread pools before numpy/onnx load.
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_k, "1")

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from src.rag.vector_store import load_index


def _artifacts_exist() -> bool:
    root = Path("artifacts/faiss_index")
    return (root / "index.faiss").is_file() and (root / "docs.pkl").is_file()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    catalog = Path("data/SHL_catalogue.json")
    if not _artifacts_exist():
        if not catalog.is_file():
            raise FileNotFoundError(
                "Missing vector index and catalog. Add data/SHL_catalogue.json or build artifacts/faiss_index/"
            )
        from src.rag.ingestion import build_index

        build_index()
    load_index()
    yield


app = FastAPI(lifespan=lifespan)


def _parse_cors_origins() -> list[str]:
    """Comma-separated list, or '*' for any origin (dev only). Empty = disable CORS."""
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if not raw:
        return []
    if raw == "*":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


_cors = _parse_cors_origins()
if _cors:
    wildcard = _cors == ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors,
        allow_credentials=not wildcard,
        allow_methods=["*"],
        allow_headers=["*"],
    )

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app.include_router(chat_router)
app.include_router(health_router)

if WEB_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(WEB_DIR)), name="assets")


@app.get("/", include_in_schema=False)
def serve_chat_ui():
    index = WEB_DIR / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="UI not found (web/index.html missing).")
    return FileResponse(index)