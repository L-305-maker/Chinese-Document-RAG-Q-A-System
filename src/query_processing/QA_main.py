from src.build_answer.answer_builder import build_answer_prompt
from src.llm.llm_client import call_llm
from src.query_processing.process_query import process_query
from src.retrieval.retriever import VectorRetriever
from src.vectorstore.chroma_store import ChromaVectorStore


def _error_result(
    prompt: str,
    stage: str,
    exc: Exception,
    query_info: dict | None = None,
    retrieval_result: dict | None = None,
):
    sources = []
    if retrieval_result:
        sources = retrieval_result.get("documents", [])

    return {
        "status": "error",
        "answer": f"QA failed at stage: {stage}",
        "stage": stage,
        "error_type": type(exc).__name__,
        "error": str(exc),
        "query_info": query_info or {"original_query": prompt},
        "retrieval_result": retrieval_result,
        "sources": sources,
    }


def QA(prompt: str):
    stage = "start"
    query_info = None
    retrieval_result = None

    try:
        stage = "process_query"
        query_info = process_query(prompt)

        if query_info.get("status") == "invalid query":
            return {
                "status": "error",
                "answer": query_info.get("message", "Invalid user query."),
                "stage": stage,
                "query_info": query_info,
                "sources": [],
            }

        if not query_info.get("need_retrieval", True):
            return {
                "status": "success",
                "answer": query_info.get("route_reason", "This query does not need retrieval."),
                "stage": stage,
                "query_info": query_info,
                "sources": [],
            }

        stage = "init_vector_store"
        vector_store = ChromaVectorStore()

        stage = "init_retriever"
        retriever = VectorRetriever(
            vector_store=vector_store,
            top_k=query_info.get("top_k", 5),
        )

        stage = "retrieve"
        retrieval_result = retriever.retrieve_with_route(query_info)

        if retrieval_result.get("status") != "success":
            return {
                "status": "error",
                "answer": "Failed to retrieve knowledge base documents.",
                "stage": stage,
                "query_info": query_info,
                "retrieval_result": retrieval_result,
                "sources": [],
            }

        documents = retrieval_result.get("documents", [])

        stage = "build_answer_prompt"
        answer_prompt = build_answer_prompt(
            question=prompt,
            documents=documents,
        )

        stage = "call_llm"
        answer = call_llm(answer_prompt)

        return {
            "status": "success",
            "answer": answer,
            "stage": "done",
            "query_info": query_info,
            "retrieval_result": retrieval_result,
            "sources": documents,
        }

    except Exception as exc:
        return _error_result(
            prompt=prompt,
            stage=stage,
            exc=exc,
            query_info=query_info,
            retrieval_result=retrieval_result,
        )
