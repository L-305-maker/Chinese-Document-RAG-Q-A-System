import hashlib
from typing import List

from src.document import Document

def hash_text(text: str) -> str:
    normalized = " ".join(text.split())

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class DocumentDeduplicator():

    def deduplicator(self,chunks:List[Document]):
        seen = set()

        unique_chunks = []

        for chunk in chunks:
            content_hash = hash_text(chunk.page_content)
            if content_hash in seen:
                continue

            seen.add(content_hash)
            chunk.metadata["content_hash"] = content_hash
            chunk.metadata["chunk_id"] = content_hash

            unique_chunks.append(chunk)

        return unique_chunks