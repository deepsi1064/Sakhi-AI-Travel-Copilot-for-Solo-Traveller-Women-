"""Thin wrapper around the Hugging Face Inference Providers chat API.

We use Hugging Face instead of a paid provider (Anthropic/OpenAI) purely for
cost: the free tier is enough to build and demo this project without a
bill. See docs/decisions.md. This wrapper is the ONLY place that talks to
the model, so swapping providers later means changing this file, not the
orchestrator.
"""
from __future__ import annotations

from dataclasses import dataclass

from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings


@dataclass
class ChatMessage:
    role: str
    content: str


class LLMError(RuntimeError):
    pass


def _is_retryable(exc: BaseException) -> bool:
    # Retry transient failures (5xx, 429, connection issues) — not 4xx client
    # errors like a bad/unsupported model name, which will never succeed on
    # retry and shouldn't cost 3x the latency before failing.
    if not isinstance(exc, HfHubHTTPError):
        return False
    status = exc.response.status_code if exc.response is not None else None
    return status is None or status >= 500 or status == 429


class HuggingFaceLLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.hf_token:
            raise LLMError("HF_TOKEN is not configured")
        self._client = InferenceClient(model=settings.hf_model, token=settings.hf_token, timeout=settings.hf_timeout_seconds)
        self._model = settings.hf_model

    def chat(self, messages: list[ChatMessage], max_tokens: int = 512, temperature: float = 0.3) -> str:
        # Every failure path must surface as LLMError — the orchestrator only
        # catches that type to degrade gracefully instead of a 500.
        try:
            response = self._chat_with_retry(messages, max_tokens, temperature)
        except Exception as exc:
            raise LLMError(f"LLM call failed: {exc}") from exc
        return response.choices[0].message.content or ""

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception(_is_retryable),
    )
    def _chat_with_retry(self, messages: list[ChatMessage], max_tokens: int, temperature: float):
        return self._client.chat_completion(
            messages=[{"role": m.role, "content": m.content} for m in messages],
            max_tokens=max_tokens,
            temperature=temperature,
        )
