"""Vendor-neutral LLM integration interfaces for RepoMosaic."""
from __future__ import annotations

from typing import Any


class LLMIntegration:
    """Base class for embedding, summarisation and question-answering providers."""

    def __init__(self, model_name: str | None = None, **kwargs: Any) -> None:
        self.model_name = model_name or "unknown"
        self.options = kwargs

    def embed(self, texts: list[str]) -> list[Any]:
        """Return embeddings for source snippets or graph node summaries."""
        raise NotImplementedError("Implement embed() in a concrete provider class.")

    def summarise(self, texts: list[str]) -> list[str]:
        """Return natural language summaries. Defaults to identity behaviour."""
        return texts

    def answer(self, question: str, context: str) -> str:
        """Answer a repository question using supplied context."""
        raise NotImplementedError("Implement answer() in a concrete provider class.")
