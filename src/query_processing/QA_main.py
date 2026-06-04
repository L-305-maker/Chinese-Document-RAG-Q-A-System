from functools import lru_cache

from src.build_answer.answer_builder import build_answer_prompt
from src.llm.llm_client import call_llm
from src.query_processing.process_query import process_query
from src.retrieval.retriever import VectorRetriever
from src.validation.answer_validator import validate_answer
from src.vectorstore.chroma_store import ChromaVectorStore


@lru_cache(maxsize=1)
def get_retriever() -> VectorRetriever:
    return VectorRetriever(vector_store=ChromaVectorStore())


def _qa_result(
    status: str,
    answer: str | None,
    stage: str,
    query_info: dict | None = None,
    retrieval_result: dict | None = None,
    sources: list[dict] | None = None,
    answer_validation: dict | None = None,
    **extra,
) -> dict:
    sources = sources or []
    result = {
        "status": status,
        "answer": answer,
        "stage": stage,
        "query_info": query_info,
        "retrieval_result": retrieval_result,
        "answer_validation": answer_validation,
        "sources": sources,
    }
    result.update(extra)
    return result


def _failed_validation(answer: str | None, reason: str, sources: list[dict] | None = None) -> dict:
    text = "" if answer is None else str(answer).strip()
    return {
        "answer_status": "failed",
        "source_cited": False,
        "answer_length": len(text),
        "document_count": len(sources or []),
        "cited_sources": [],
        "warnings": [],
        "errors": [reason],
    }


def _error_result(
    prompt: str,
    stage: str,
    exc: Exception,
    query_info: dict | None = None,
    retrieval_result: dict | None = None,
) -> dict:
    answer = f"QA failed at stage: {stage}"
    sources = retrieval_result.get("documents", []) if retrieval_result else []
    return _qa_result(
        status="error",
        answer=answer,
        stage=stage,
        query_info=query_info or {"original_query": prompt},
        retrieval_result=retrieval_result,
        sources=sources,
        answer_validation=_failed_validation(answer, type(exc).__name__, sources),
        error_type=type(exc).__name__,
        error=str(exc),
    )


def QA(prompt: str) -> dict:
    stage = "start"
    query_info = None
    retrieval_result = None

    try:
        stage = "process_query"
        query_info = process_query(prompt)

        if query_info.get("status") == "invalid query":
            answer = query_info.get("message", "Invalid user query.")
            return _qa_result(
                status="error",
                answer=answer,
                stage=stage,
                query_info=query_info,
                answer_validation=_failed_validation(answer, "invalid_query"),
            )

        if not query_info.get("need_retrieval", True):
            answer = query_info.get("route_reason", "This query does not need retrieval.")
            return _qa_result(
                status="success",
                answer=answer,
                stage=stage,
                query_info=query_info,
                answer_validation=validate_answer(answer, [], require_sources=False),
            )

        stage = "init_retriever"
        retriever = get_retriever()

        stage = "retrieve"
        retrieval_result = retriever.retrieve_with_route(query_info)
        documents = retrieval_result.get("documents", [])

        if retrieval_result.get("status") != "success":
            answer = "Failed to retrieve knowledge base documents."
            return _qa_result(
                status="error",
                answer=answer,
                stage=stage,
                query_info=query_info,
                retrieval_result=retrieval_result,
                sources=[],
                answer_validation=_failed_validation(answer, "retrieval_failed"),
            )

        stage = "build_answer_prompt"
        answer_prompt = build_answer_prompt(
            question=prompt,
            documents=documents,
        )

        stage = "call_llm"
        answer = call_llm(answer_prompt)

        stage = "validate_answer"
        answer_validation = validate_answer(answer, documents)

        return _qa_result(
            status="success",
            answer=answer,
            stage="done",
            query_info=query_info,
            retrieval_result=retrieval_result,
            sources=documents,
            answer_validation=answer_validation,
        )

    except Exception as exc:
        return _error_result(
            prompt=prompt,
            stage=stage,
            exc=exc,
            query_info=query_info,
            retrieval_result=retrieval_result,
        )
