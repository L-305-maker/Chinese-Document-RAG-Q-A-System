from dataclasses import dataclass

@dataclass
class QueryState():
    original_query: str = ""
    normalized_query: str = ""
    rewritten_query: str = ""

    need_rerank: bool = True
    need_retrieval: bool = True

    retrieval_mode : str = "dense"

    top_k: int = 5

