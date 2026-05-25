from src.vectorstore.chroma_store import ChromaVectorStore
from src.ingestion.file_ingestor import FileIngestor


def main():
    vector_store = ChromaVectorStore(
        persist_directory="./data/vector_db",
        collection_name="rag_docs",
    )

    ingestor = FileIngestor(
        vector_store=vector_store,
        chunk_size=500,
        chunk_overlap=100,
    )

    # 入库整个文件夹
    chunks = ingestor.ingest_directory("./data/raw_rag")

    print(f"Total chunks ingested: {len(chunks)}")


if __name__ == "__main__":
    main()