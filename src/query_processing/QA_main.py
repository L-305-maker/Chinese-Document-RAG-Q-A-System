from src.build_answer.answer_builder import build_answer_prompt
from src.llm.llm_client import call_llm
from src.query_processing.process_query import process_query
from src.retrieval.retriever import VectorRetriever
from src.vectorstore.chroma_store import ChromaVectorStore


def QA(prompt: str):
    query_info = process_query(prompt)

    if query_info.get("status") == "invalid query":
        return {
            "status": "error",
            "answer": query_info.get("message", "Invalid user query."),
            "query_info": query_info,
            "sources": [],
        }

    if not query_info.get("need_retrieval", True):
        return {
            "status": "success",
            "answer": query_info.get("route_reason", "This query does not need retrieval."),
            "query_info": query_info,
            "sources": [],
        }

    vector_store = ChromaVectorStore()
    retriever = VectorRetriever(
        vector_store=vector_store,
        top_k=query_info.get("top_k", 5),
    )

    retrieval_result = retriever.retrieve_with_route(query_info)

    if retrieval_result.get("status") != "success":
        return {
            "status": "error",
            "answer": "Failed to retrieve knowledge base documents.",
            "query_info": query_info,
            "sources": [],
            "retrieval_result": retrieval_result,
        }

    documents = retrieval_result.get("documents", [])

    answer_prompt = build_answer_prompt(
        question=prompt,
        documents=documents,
    )

    answer = call_llm(answer_prompt)

    return {
        "status": "success",
        "answer": answer,
        "query_info": query_info,
        "retrieval_result": retrieval_result,
        "sources": documents,
    }
