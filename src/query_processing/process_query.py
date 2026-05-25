from src.query_processing.normalize import Normalize_Query,normalized_query_quality
from src.query_processing.query_rewriter import rewrite_query
from src.query_processing.query_router import route_query

def process_query(query:str)->str:
    
    normalized = normalized_query_quality(query,512)

    if not normalized.is_valid:
        return {
            "status":"invalid query",
            "message":"Please ensure your query valid"
        }
    
    rewritten_query = rewrite_query(normalized.normalized_query)

    route_result = route_query(
        query= rewritten_query.rewritten_query,
        search_queries= rewritten_query.search_queries,
        sub_questions= rewritten_query.sub_questions,
        need_decomposition= rewritten_query.need_decomposition
    )

    return {
        "original_query": normalized.original_query,
        "normalized_query": normalized.normalized_query,
        "rewritten_query": rewritten_query.rewritten_query,
        "search_queries": rewritten_query.search_queries,
        "keywords": rewritten_query.keywords,
        "sub_questions": rewritten_query.sub_questions,
        "rewrite_method": rewritten_query.rewrite_method,
        "query_type": route_result.query_type,
        "need_retrieval": route_result.need_retrieval,
        "retrieval_mode": route_result.retrieval_mode,
        "top_k": route_result.top_k,
        "need_rerank": route_result.need_rerank,
        "use_sub_questions": route_result.use_sub_questions,
        "route_reason": route_result.reason,
    }

