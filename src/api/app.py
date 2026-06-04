from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="Chinese Document RAG Q&A System")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    status: str
    answer: Any = None
    stage: str | None = None
    query_info: dict[str, Any] | None = None
    answer_validation: dict[str, Any] | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    error_type: str | None = None
    error: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> dict[str, Any]:
    from src.query_processing.QA_main import QA

    result = QA(request.question)

    return {
        "status": result.get("status", "error"),
        "answer": result.get("answer"),
        "stage": result.get("stage"),
        "query_info": result.get("query_info"),
        "answer_validation": result.get("answer_validation"),
        "sources": _format_sources(result.get("sources", [])),
        "error_type": result.get("error_type"),
        "error": result.get("error"),
    }


def _format_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source": (source.get("metadata") or {}).get("source"),
            "chunk_index": (source.get("metadata") or {}).get("chunk_index"),
            "score": _to_float(source.get("rerank_score", source.get("score"))),
            "preview": _preview(source.get("content", "")),
        }
        for source in sources
    ]


def _preview(text: str, max_length: int = 160) -> str:
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= max_length else text[:max_length] + "..."


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
