from __future__ import annotations

from typing import Any, Dict, List

from config.setting import settings


class Reranker:
    def __init__(self, model_name: str | None = None, enabled: bool | None = None):
        self.model_name = model_name or settings.RERANK_MODEL
        self.enabled = settings.RERANK_ENABLED if enabled is None else enabled
        self._model = None
        self._load_attempted = False
        self._load_error: str | None = None

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int | None = None,
    ) -> Dict[str, Any]:
        if not documents:
            return {
                "status": "skipped",
                "reason": "no_documents",
                "documents": [],
            }

        if not self.enabled:
            return {
                "status": "skipped",
                "reason": "rerank_disabled",
                "documents": documents,
            }

        model = self._load_model()
        if model is None:
            return {
                "status": "skipped",
                "reason": "reranker_unavailable",
                "error": self._load_error,
                "documents": documents,
            }

        pairs = [(query, doc.get("content", "")) for doc in documents]

        try:
            scores = model.predict(pairs)
        except Exception as exc:
            return {
                "status": "skipped",
                "reason": "rerank_failed",
                "error": str(exc),
                "documents": documents,
            }

        ranked_documents = []
        for doc, score in zip(documents, scores):
            ranked_doc = dict(doc)
            ranked_doc["original_score"] = doc.get("score")
            ranked_doc["rerank_score"] = float(score)
            ranked_documents.append(ranked_doc)

        ranked_documents.sort(
            key=lambda item: item.get("rerank_score", float("-inf")),
            reverse=True,
        )

        return {
            "status": "success",
            "model": self.model_name,
            "documents": ranked_documents,
        }

    def _load_model(self):
        if self._model is not None:
            return self._model
        if self._load_attempted:
            return None

        try:
            self._load_attempted = True
            from sentence_transformers import CrossEncoder

            if settings.RERANK_ALLOW_DOWNLOAD:
                self._model = CrossEncoder(self.model_name)
            else:
                self._model = CrossEncoder(self.model_name, local_files_only=True)
            return self._model
        except TypeError as exc:
            if "local_files_only" in str(exc):
                self._load_error = (
                    "Current sentence-transformers version does not support "
                    "local_files_only. Set RERANK_ALLOW_DOWNLOAD=true after "
                    "confirming model downloads are acceptable."
                )
                return None
            self._load_error = str(exc)
            return None
        except Exception as exc:
            self._load_error = str(exc)
            return None


_reranker: Reranker | None = None


def get_reranker() -> Reranker:
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker
