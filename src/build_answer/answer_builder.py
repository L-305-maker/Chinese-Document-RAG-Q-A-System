from src.build_answer.context_builder import build_context


def build_answer_prompt(question: str, documents: list[dict]) -> str:
    context = build_context(documents)

    return f"""
你是一个基于本地知识库的中文文档问答助手。

请严格根据参考资料回答用户问题。
如果参考资料不足以回答，请说明“根据现有资料无法回答”，不要编造。
回答末尾请简要列出使用到的来源。

用户问题:
{question}

参考资料:
{context}

请给出答案:
""".strip()
