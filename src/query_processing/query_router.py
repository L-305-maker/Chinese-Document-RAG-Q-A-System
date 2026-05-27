from dataclasses import dataclass


#定义问题类型
class QueryType:
    CHITCHAT = "chitchat"
    FACT_QA = "fact_qa"
    SUMMARY = "summary"
    COMPARE = "compare"
    HOW_TO = "how_to"
    MULTI_HOP = "multi_hop"
    OUT_OF_SCOPE = "out_of_scope"


#定义向量匹配的类型，全局匹配/关键词匹配
class RetrievalMode:
    NONE = "none"
    DENSE = "dense"
    BM25 = "bm25"
    HYBRID = "hybrid"
    MULTI_QUERY = "multi_query"


#进行route之后的结果
@dataclass
class RouteResult:
    query_type: str
    need_retrieval: bool
    retrieval_mode: str
    top_k: int
    need_rerank: bool
    use_sub_questions: bool
    reason: str = ""

#各个模式的关键词
CHITCHAT_PATTERNS = [
    "你好",
    "您好",
    "hello",
    "hi",
    "你是谁",
    "你能做什么",
    "谢谢",
    "感谢",
]
SUMMARY_KEYWORDS = [
    "总结",
    "概括",
    "归纳",
    "梳理",
    "提炼",
    "summary",
    "summarize",
]
COMPARE_KEYWORDS = [
    "区别",
    "对比",
    "比较",
    "异同",
    "差异",
    "优缺点",
    "vs",
    "versus",
    "compare",
    "difference",
]
HOW_TO_KEYWORDS = [
    "怎么",
    "如何",
    "怎样",
    "步骤",
    "流程",
    "方法",
    "实现",
    "搭建",
    "配置",
    "安装",
    "使用",
    "how to",
]
MULTI_HOP_KEYWORDS = [
    "分别",
    "同时",
    "以及",
    "并且",
    "然后",
    "各自",
    "之间的关系",
]
OUT_OF_SCOPE_KEYWORDS = [
    "写一首诗",
    "讲个笑话",
    "生成小说",
    "角色扮演",
]



# 将关键词进行拆分
def _contains_any(query: str, keywords: list[str]) -> bool:
    query_lower = query.lower()
    return any(keyword.lower() in query_lower for keyword in keywords)


#判断是否为闲聊，有无回答需要
def is_chitchat(query: str) -> bool:
    query_lower = query.lower().strip()

    # 很短的问候语可以直接判为闲聊
    if query_lower in CHITCHAT_PATTERNS:
        return True

    # 短句中包含问候词，也可以判为闲聊
    if len(query_lower) <= 10 and _contains_any(query_lower, CHITCHAT_PATTERNS):
        return True

    return False


# 判断问题类型
def classify_query_type(
    query: str,
    has_sub_questions: bool = False,
    need_decomposition: bool = False,
) -> str:
    if not query or not query.strip():
        return QueryType.OUT_OF_SCOPE

    query = query.strip()

    if is_chitchat(query):
        return QueryType.CHITCHAT

    if _contains_any(query, OUT_OF_SCOPE_KEYWORDS):
        return QueryType.OUT_OF_SCOPE

    if _contains_any(query, SUMMARY_KEYWORDS):
        return QueryType.SUMMARY

    if _contains_any(query, COMPARE_KEYWORDS):
        return QueryType.COMPARE

    if _contains_any(query, HOW_TO_KEYWORDS):
        return QueryType.HOW_TO

    if _contains_any(query, MULTI_HOP_KEYWORDS):
        return QueryType.MULTI_HOP

    return QueryType.FACT_QA


# 选择检索方式
def decide_route_by_type(query_type: str) -> RouteResult:
    if query_type == QueryType.CHITCHAT:
        return RouteResult(
            query_type=query_type,
            need_retrieval=False,
            retrieval_mode=RetrievalMode.NONE,
            top_k=0,
            need_rerank=False,
            use_sub_questions=False,
            reason="闲聊类问题，不需要进入知识库检索。",
        )

    if query_type == QueryType.OUT_OF_SCOPE:
        return RouteResult(
            query_type=query_type,
            need_retrieval=False,
            retrieval_mode=RetrievalMode.NONE,
            top_k=0,
            need_rerank=False,
            use_sub_questions=False,
            reason="该问题不适合基于知识库进行回答。",
        )

    if query_type == QueryType.SUMMARY:
        return RouteResult(
            query_type=query_type,
            need_retrieval=True,
            retrieval_mode=RetrievalMode.DENSE,
            top_k=10,
            need_rerank=True,
            use_sub_questions=False,
            reason="总结类问题需要覆盖更多上下文，因此提高 top_k。",
        )

    if query_type == QueryType.COMPARE:
        return RouteResult(
            query_type=query_type,
            need_retrieval=True,
            retrieval_mode=RetrievalMode.MULTI_QUERY,
            top_k=8,
            need_rerank=True,
            use_sub_questions=True,
            reason="对比类问题通常涉及多个概念，适合多 query 检索。",
        )

    if query_type == QueryType.HOW_TO:
        return RouteResult(
            query_type=query_type,
            need_retrieval=True,
            retrieval_mode=RetrievalMode.MULTI_QUERY,
            top_k=6,
            need_rerank=True,
            use_sub_questions=True,
            reason="方法步骤类问题适合召回流程性和解释性内容。",
        )

    if query_type == QueryType.MULTI_HOP:
        return RouteResult(
            query_type=query_type,
            need_retrieval=True,
            retrieval_mode=RetrievalMode.MULTI_QUERY,
            top_k=8,
            need_rerank=True,
            use_sub_questions=True,
            reason="多跳问题需要使用多个子问题或多个 search query 进行检索。",
        )

    return RouteResult(
        query_type=QueryType.FACT_QA,
        need_retrieval=True,
        retrieval_mode=RetrievalMode.DENSE,
        top_k=5,
        need_rerank=True,
        use_sub_questions=False,
        reason="默认事实问答类问题，使用向量检索。",
    )


# 根据rewrite的结果判断采取何种检索策略
def route_query(query: str,search_queries: list[str] | None = None,sub_questions: list[str] | None = None,need_decomposition: bool = False,) -> RouteResult:


    search_queries = search_queries or []
    sub_questions = sub_questions or []

    has_sub_questions = len(sub_questions) > 0

    query_type = classify_query_type(
        query=query,
        has_sub_questions=has_sub_questions,
        need_decomposition=need_decomposition,
    )

    route_result = decide_route_by_type(query_type)

    return route_result
