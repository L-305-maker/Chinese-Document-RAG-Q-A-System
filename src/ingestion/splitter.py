from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangChainDocument

from src.document import Document


class DocumentSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        lc_docs = [
            LangChainDocument(
                page_content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in documents
        ]

        lc_chunks = self.splitter.split_documents(lc_docs)

        chunks = [
            Document(
                page_content=chunk.page_content,
                metadata=dict(chunk.metadata),
            )
            for chunk in lc_chunks
        ]

        return chunks