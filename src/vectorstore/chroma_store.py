from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document as LangChainDocument

from config.setting import settings
from src.document import Document
from src.embedding.embedding_model import get_embedding_model


class ChromaVectorStore:
    def __init__(
        self,
        persist_directory: str = settings.VECTOR_DB_PATH,
        collection_name: str = settings.COLLECTION_NAME,
    ):
        self.embedding_model = get_embedding_model()
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embedding_model,
            persist_directory=persist_directory,
        )

    def add_documents(self, documents: List[Document]) -> None:
        lc_docs = [
            LangChainDocument(
                page_content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in documents
        ]

        ids = [doc.metadata["chunk_id"] for doc in documents]
        self.vector_store.add_documents(lc_docs, ids=ids)
        print(f"Added {len(documents)} chunks to Chroma.")

    def similarity_search(self, query: str, k: int = 5):
        return self.vector_store.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = 5):
        return self.vector_store.similarity_search_with_score(query, k=k)
