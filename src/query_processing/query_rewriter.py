from src.query_processing.normalize import Normalize_Query,normalized_query_quality
from typing import List,Optional,Callable
from dataclasses import dataclass,field

import json
import re


@dataclass
class RewriteResult:
    original_query: str
    rewritten_query: str
    search_queries: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    sub_questions: List[str] = field(default_factory=list)
    need_decomposition: bool = False
    rewrite_method: str = "llm"


REWRITE_PROMPT_TEMPLATE = """
你是一个 RAG 问答系统中的 Query Rewriter。
你的任务是将用户问题改写成更适合检索的查询。

要求：
1. 不要改变用户原意。
2. 保留关键实体、技术术语、数字、版本号。
3. 可以补充常见中英文术语表达，例如 RAG / Retrieval-Augmented Generation，微调 / Fine-tuning。
4. 如果问题包含多个子问题，请拆解为 sub_questions。
5. search_queries 用于向量检索或关键词检索，数量控制在 3 到 5 个。
6. keywords 数量控制在 3 到 10 个。
7. 只输出 JSON,不要输出 Markdown,不要输出解释。

用户问题：
{query}

请严格按照下面 JSON 格式输出：

{{
  "rewritten_query": "...",
  "search_queries": ["...", "..."],
  "keywords": ["...", "..."],
  "sub_questions": ["...", "..."],
  "need_decomposition": true
}}
"""


def build_rewritten_prompt(query:str)->str:
    return REWRITE_PROMPT_TEMPLATE.format(query=query)


def extract_json_from_text(text: str) -> dict:
 
    text = text.strip()

    # 去掉 markdown 代码块
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass


    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No valid JSON object found in LLM output.")

    return json.loads(match.group(0))


def _ensure_list(value) -> List[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        value = value.strip()
        return [value] if value else []

    return []


#兜底保证，确保LLM失败后，retrieval pipeline仍然可以运行
def fallback_rewrite(query: str) -> RewriteResult:

    return RewriteResult(
        original_query=query,
        rewritten_query=query,
        search_queries=[query] if query else [],
        keywords=[],
        sub_questions=[],
        need_decomposition=False,
        rewrite_method="fallback",
    )


#正常处理prompt
def validate_and_build_result(query:str,data:dict)->RewriteResult:
    rewritten_query = str(data.get("rewritten_query","")).strip() or query

    search_queries = _ensure_list(data.get("search_queries"))
    keywords = _ensure_list(data.get("keywords"))
    sub_questions = _ensure_list(data.get("sub_questions"))

    # 至少保证原问题或改写问题参与检索
    if not search_queries:
        search_queries = [rewritten_query]

    # 去重，同时保留顺序
    search_queries = list(dict.fromkeys(search_queries))
    keywords = list(dict.fromkeys(keywords))
    sub_questions = list(dict.fromkeys(sub_questions))

    # 控制长度，避免后续检索成本过高
    search_queries = search_queries[:5]
    keywords = keywords[:10]
    sub_questions = sub_questions[:5]

    need_decomposition = bool(data.get("need_decomposition", False))

    return RewriteResult(
        original_query=query,
        rewritten_query=rewritten_query,
        search_queries=search_queries,
        keywords=keywords,
        sub_questions=sub_questions,
        need_decomposition=need_decomposition,
        rewrite_method="llm",
    )
    

# rewrite query的总函数 
def rewrite_query(query:str, llm_func=None)->RewriteResult:
    if query is None or not query.strip():
        return fallback_rewrite("")
    
    query = str(query).strip()
    prompt = build_rewritten_prompt(query)

    if llm_func is None:
        from src.llm.llm_client import call_llm
        llm_func = call_llm

    try:
        llm_output = llm_func(prompt)
        data = extract_json_from_text(llm_output)
        return validate_and_build_result(query,data)
    
    except Exception as e:
        print(f"[query rewriter] LLM rewriter failed: {e}")
        return fallback_rewrite(query)