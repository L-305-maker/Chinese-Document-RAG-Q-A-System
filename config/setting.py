import os

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

load_dotenv()


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError:
        return default


class Settings:
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_TIMEOUT_SECONDS: int = _get_int("LLM_TIMEOUT_SECONDS", 60)
    LLM_MAX_RETRIES: int = _get_int("LLM_MAX_RETRIES", 2)
    LLM_RETRY_DELAY_SECONDS: float = _get_float("LLM_RETRY_DELAY_SECONDS", 1.0)

    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "rag_docs")

    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "auto").lower()

    RERANK_ENABLED: bool = _get_bool("RERANK_ENABLED", True)
    RERANK_ALLOW_DOWNLOAD: bool = _get_bool("RERANK_ALLOW_DOWNLOAD", False)
    RERANK_MODEL: str = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-base")
    RERANK_CANDIDATE_MULTIPLIER: int = _get_int("RERANK_CANDIDATE_MULTIPLIER", 3)
    RERANK_MAX_CANDIDATES: int = _get_int("RERANK_MAX_CANDIDATES", 30)

    MULTI_QUERY_MAX_QUERIES: int = _get_int("MULTI_QUERY_MAX_QUERIES", 5)


settings = Settings()
