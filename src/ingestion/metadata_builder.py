from datetime import datetime
from typing import List

from src.document import Document


class MetadataBuilder:

    #建立MetaData

    def add_metadata(self,chunks: List[Document],file_path: str,file_type: str) -> List[Document]:
        #给出存入Metadata的时间
        now = datetime.now().isoformat(timespec="seconds")

        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "chunk_index": i,             #chunk的序列号
                "file_type": file_type,       #文件类型
                "ingested_at": now,           #更新时间
                "file_path":file_path
            })

        return chunks