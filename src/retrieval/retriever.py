from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from config.setting import settings
from src.query_processing.query_router import RetrievalMode
from src.rerank.reranker import Reranker, get_reranker
from src.validation.prompt_validator import PromptValidator

if TYPE_CHECKING:
    from src.vectorstore.chroma_store import ChromaVectorStore


class VectorRetriever:
    def __init__(
        self,
        vector_store: "ChromaVectorStore",
        top_k: int = 5,
        reranker: Reranker | None = None,
    ):
        self.vector_store = vector_store
        self.top_k = top_k
        self.prompt_validator = PromptValidator()
        self.reranker = reranker or get_reranker()

    def retrieve(
        self,
        prompt: str,
        top_k: int | None = None,
        candidate_k: int | None = None,
        need_rerank: bool = False,
        rerank_query: str | None = None,
    ) -> Dict[str, Any]:
        validation = self.prompt_validator.validate(prompt)
        if not validation["is_valid"]:
            return {
                "status": "error",
                "message": "Invalid query for retrieval.",
                "validation": validation,
                "documents": [],
            }

        normalized_prompt = validation["normalized_prompt"]
        final_top_k = self._resolve_top_k(top_k)
        search_k = self._resolve_candidate_k(final_top_k, candidate_k, need_rerank)

        results = self.vector_store.similarity_search_with_score(
            query=normalized_prompt,
            k=search_k,
        )
        documents = self._format_results(results, source_query=normalized_prompt)

        documents, rerank_info = self._maybe_rerank(
            query=rerank_query or normalized_prompt,
            documents=documents,
            top_k=final_top_k,
            need_rerank=need_rerank,
        )

        return {
            "status": "success",
            "query": normalized_prompt,
            "retrieval_mode": RetrievalMode.DENSE,
            "top_k": final_top_k,
            "candidate_k": search_k,
            "rerank": rerank_info,
            "documents": documents,
        }

    def multi_retrieve(
        self,
        queries: List[str],
        top_k: int | None = None,
        candidate_k: int | None = None,
        need_rerank: bool = False,
        rerank_query: str | None = None,
    ) -> Dict[str, Any]:
        route_queries = self._clean_queries(queries)
        if not route_queries:
            return {
                "status": "error",
                "message": "No valid queries for multi-query retrieval.",
                "documents": [],
            }

        final_top_k = self._resolve_top_k(top_k)
        candidate_budget = self._resolve_candidate_k(
            final_top_k,
            candidate_k,
            need_rerank,
        )
        per_query_k = max(
            1,
            min(
                candidate_budget,
                max(final_top_k, candidate_budget // len(route_queries)),
            ),
        )

        all_documents: List[Dict[str, Any]] = []
        successful_queries: List[str] = []
        errors: List[Dict[str, Any]] = []

        for query in route_queries:
            result = self.retrieve(
                prompt=query,
                top_k=per_query_k,
                candidate_k=per_query_k,
                need_rerank=False,
            )

            if result["status"] != "success":
                errors.append({"query": query, "message": result.get("message")})
                continue

            successful_queries.append(result["query"])
            all_documents.extend(result.get("documents", []))

        if not all_documents:
            return {
                "status": "error",
                "message": "No documents retrieved by any query.",
                "queries": route_queries,
                "errors": errors,
                "documents": [],
            }

        unique_documents = self._deduplicate_documents(all_documents)
        unique_documents.sort(key=self._dense_sort_key)
        candidate_documents = unique_documents[:candidate_budget]

        documents, rerank_info = self._maybe_rerank(
            query=rerank_query or route_queries[0],
            documents=candidate_documents,
            top_k=final_top_k,
            need_rerank=need_rerank,
        )

        return {
            "status": "success",
            "query": rerank_query or route_queries[0],
            "queries": successful_queries,
            "retrieval_mode": RetrievalMode.MULTI_QUERY,
            "top_k": final_top_k,
            "candidate_k": candidate_budget,
            "per_query_k": per_query_k,
            "rerank": rerank_info,
            "documents": documents,
            "errors": errors,
        }

    def retrieve_with_route(self, query_info: Dict[str, Any]) -> Dict[str, Any]:
        retrieval_mode = query_info.get("retrieval_mode", RetrievalMode.DENSE)
        top_k = self._resolve_top_k(query_info.get("top_k"))
        need_rerank = bool(query_info.get("need_rerank", False))
        rewritten_query = (
            query_info.get("rewritten_query")
            or query_info.get("normalized_query")
            or query_info.get("original_query")
            or ""
        )

        if retrieval_mode == RetrievalMode.NONE:
            return {
                "status": "success",
                "query": rewritten_query,
                "retrieval_mode": RetrievalMode.NONE,
                "documents": [],
                "rerank": {"status": "skipped", "reason": "retrieval_disabled"},
            }

        if retrieval_mode == RetrievalMode.MULTI_QUERY:
            queries = self._queries_from_route(query_info, rewritten_query)
            return self.multi_retrieve(
                queries=queries,
                top_k=top_k,
                need_rerank=need_rerank,
                rerank_query=rewritten_query,
            )

        if retrieval_mode in {RetrievalMode.BM25, RetrievalMode.HYBRID}:
            result = self.retrieve(
                prompt=rewritten_query,
                top_k=top_k,
                need_rerank=need_rerank,
                rerank_query=rewritten_query,
            )
            result["requested_retrieval_mode"] = retrieval_mode
            result["fallback_reason"] = (
                f"{retrieval_mode} is not implemented yet; used dense retrieval."
            )
            return result

        return self.retrieve(
            prompt=rewritten_query,
            top_k=top_k,
            need_rerank=need_rerank,
            rerank_query=rewritten_query,
        )

    def _maybe_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int,
        need_rerank: bool,
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not need_rerank:
            return documents[:top_k], {"status": "skipped", "reason": "route_disabled"}

        rerank_result = self.reranker.rerank(
            query=query,
            documents=documents,
            top_k=top_k,
        )

        return rerank_result.get("documents", documents[:top_k]), {
            key: value
            for key, value in rerank_result.items()
            if key != "documents"
        }

    def _queries_from_route(
        self,
        query_info: Dict[str, Any],
        rewritten_query: str,
    ) -> List[str]:
        queries = [rewritten_query]

        if query_info.get("use_sub_questions"):
            queries.extend(query_info.get("sub_questions") or [])

        queries.extend(query_info.get("search_queries") or [])

        return self._clean_queries(queries)[: settings.MULTI_QUERY_MAX_QUERIES]

    def _format_results(self, results, source_query: str) -> List[Dict[str, Any]]:
        retrieved_docs = []

        for doc, score in results:
            retrieved_docs.append(
                {
                    "content": doc.page_content,
                    "metadata": dict(doc.metadata),
                    "score": float(score),
                    "source_query": source_query,
                    "matched_queries": [source_query],
                }
            )

        return retrieved_docs

    def _deduplicate_documents(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        unique_by_id: Dict[str, Dict[str, Any]] = {}

        for doc in documents:
            metadata = doc.get("metadata") or {}
            doc_id = (
                metadata.get("chunk_id")
                or metadata.get("content_hash")
                or doc.get("content")
                or str(id(doc))
            )

            doc_copy = dict(doc)
            doc_copy["metadata"] = dict(metadata)
            doc_copy["matched_queries"] = list(doc.get("matched_queries") or [])

            existing = unique_by_id.get(doc_id)
            if existing is None:
                unique_by_id[doc_id] = doc_copy
                continue

            existing_queries = set(existing.get("matched_queries") or [])
            existing_queries.update(doc_copy.get("matched_queries") or [])
            existing["matched_queries"] = list(existing_queries)

            if self._dense_sort_key(doc_copy) < self._dense_sort_key(existing):
                doc_copy["matched_queries"] = existing["matched_queries"]
                unique_by_id[doc_id] = doc_copy

        return list(unique_by_id.values())

    def _resolve_top_k(self, top_k: Any = None) -> int:
        try:
            value = int(top_k) if top_k is not None else int(self.top_k)
        except (TypeError, ValueError):
            value = int(self.top_k)
        return max(1, value)

    def _resolve_candidate_k(
        self,
        top_k: int,
        candidate_k: int | None = None,
        need_rerank: bool = False,
    ) -> int:
        if candidate_k is not None:
            try:
                return max(top_k, int(candidate_k))
            except (TypeError, ValueError):
                pass

        if not need_rerank:
            return top_k

        candidate_k = top_k * max(1, settings.RERANK_CANDIDATE_MULTIPLIER)
        return max(top_k, min(candidate_k, settings.RERANK_MAX_CANDIDATES))

    @staticmethod
    def _clean_queries(queries: List[str]) -> List[str]:
        cleaned = []
        seen = set()

        for query in queries:
            if query is None:
                continue
            query = str(query).strip()
            if not query or query in seen:
                continue
            seen.add(query)
            cleaned.append(query)

        return cleaned

    @staticmethod
    def _dense_sort_key(document: Dict[str, Any]) -> float:
        score = document.get("score")
        if score is None:
            return float("inf")
        return float(score)
