from pathlib import Path
from typing import List

from src.document import Document
from src.ingestion.file_type import detect_file_type
from src.ingestion.loaders import LoaderFactory
from src.ingestion.cleaner import DocumentCleaner
from src.ingestion.splitter import DocumentSplitter
from src.ingestion.metadata_builder import MetadataBuilder
from src.vectorstore.chroma_store import ChromaVectorStore


class FileIngestor:
    def __init__(
        self,
        vector_store: ChromaVectorStore,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ):
        self.vector_store = vector_store
        self.loader_factory = LoaderFactory()
        self.cleaner = DocumentCleaner()
        self.splitter = DocumentSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self.metadata_builder = MetadataBuilder()

    def ingest(self, file_path: str) -> List[Document]:
        file_type = detect_file_type(file_path)

        loader = self.loader_factory.get_loader(file_type)

        raw_documents = loader.load(file_path)

        cleaned_documents = self.cleaner.clean(raw_documents)

        chunks = self.splitter.split_documents(cleaned_documents)

        chunks = self.metadata_builder.add_metadata(
            chunks=chunks,
            file_path=file_path,
            file_type=file_type,
        )

        self.vector_store.add_documents(chunks)

        return chunks

    def ingest_directory(self, directory_path: str) -> List[Document]:
        directory = Path(directory_path)
        all_chunks = []

        for file_path in directory.rglob("*"):
            if not file_path.is_file():
                continue

            try:
                chunks = self.ingest(str(file_path))
                all_chunks.extend(chunks)
                print(f"Successfully ingested: {file_path}")

            except ValueError as e:
                print(f"Skipped unsupported file: {file_path}, reason: {e}")

            except Exception as e:
                print(f"Failed to ingest: {file_path}, reason: {e}")

        return all_chunks