"""Embeddings via Hugging Face's free feature-extraction endpoint.

Same provider as the chat LLM (app/agent/llm_client.py) — no local
sentence-transformers/torch install needed. Tradeoff: a network call per
embed, and subject to the same free-tier availability as the chat model.
See docs/decisions.md.
"""
from __future__ import annotations

from huggingface_hub import InferenceClient

from app.config import get_settings

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    client = InferenceClient(token=settings.hf_token)
    vector = client.feature_extraction(text, model=EMBEDDING_MODEL)
    if vector.ndim == 2:  # some models return per-token embeddings; mean-pool
        vector = vector.mean(axis=0)
    return vector.tolist()
