
def build_answer_prompt(question: str, documents: list[dict]) -> str:
    context_parts = []

    for i, doc in enumerate(documents, start=1):
        metadata = doc.get("metadata", {})
        source = metadata.get("source", "unknown")
        page = metadata.get("page")
        content = doc.get("content", "")

        source_text = source
        if page:
            source_text += f"，第 {page} 页"

        context_parts.append(
            f"[资料 {i}]\n来源：{source_text}\n内容：{content}"
        )

    context = "\n\n".join(context_parts)

    return f"""
你是一个基于本地知识库的中文文档问答助手。

请严格根据参考资料回答用户问题。
如果参考资料不足以回答，请说明“根据现有资料无法回答”，不要编造。
回答末尾请简要列出使用到的来源。

用户问题：
{question}

参考资料：
{context}

请给出答案：
""".strip()