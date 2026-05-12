from typing import Dict, Any, List

from src.validation.prompt_validator import PromptValidator
from src.vectorstore.chroma_store import ChromaVectorStore


class VectorRetriever:
    def __init__(
        self,
        vector_store: ChromaVectorStore,
        top_k: int = 5,
    ):
        self.vector_store = vector_store
        self.top_k = top_k
        self.prompt_validator = PromptValidator()

    def retrieve(self, prompt: str) -> Dict[str, Any]:
        # 1. 校验用户输入
        validation = self.prompt_validator.validate(prompt)

        if not validation["is_valid"]:
            return {
                "status": "error",
                "message": "用户输入无效，可能为空、过长或包含乱码。",
                "validation": validation,
                "documents": [],
            }

        normalized_prompt = validation["normalized_prompt"]

        # 2. 向量检索
        results = self.vector_store.similarity_search_with_score(
            query=normalized_prompt,
            k=self.top_k,
        )

        # 3. 整理结果
        retrieved_docs = []

        for doc, score in results:
            retrieved_docs.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            })

        return {
            "status": "success",
            "query": normalized_prompt,
            "documents": retrieved_docs,
        }