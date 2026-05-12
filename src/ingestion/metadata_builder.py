import uuid
from datetime import datetime
from typing import List

from src.document import Document


class MetadataBuilder:
    def add_metadata(self,chunks: List[Document],file_path: str,file_type: str,) -> List[Document]:
        now = datetime.now().isoformat(timespec="seconds")

        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_id": str(uuid.uuid4()),
                "chunk_index": i,
                "file_type": file_type,
                "ingested_at": now,
            })

        return chunks