"""
Query/document embeddings for all-MiniLM-L6-v2 (384-dim).

Uses FastEmbed + ONNX Runtime instead of PyTorch sentence-transformers so the
app fits small hosts (e.g. Render 512MB). Lazy-loads the model on first use.

If you built artifacts/faiss_index with an older PyTorch pipeline, rebuild the
index once after this change: `python -m src.rag.inges_runner` (or delete
artifacts and let the API lifespan run ingestion).
"""
from __future__ import annotations

import numpy as np
from fastembed import TextEmbedding

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=_MODEL_NAME)
    return _model


def get_embedding(text: str) -> np.ndarray:
    m = _get_model()
    vec = next(m.embed([text]))
    out = np.asarray(vec, dtype=np.float32).reshape(1, -1)
    return out
