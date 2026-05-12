import re
from typing import List
from src.document import Document

class DocumentCleaner():
    def clean_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        text = re.sub(r"[ \t]+", " ", text)

        text = re.sub(r"\n{3,}", "\n\n", text)

        text = text.strip()

        return text

    def clean(self, documents: List[Document]) -> List[Document]:
        cleaned_docs = []

        for doc in documents:
            cleaned_text = self.clean_text(doc.page_content)

            if len(cleaned_text) < 20:
                continue

            doc.page_content = cleaned_text
            cleaned_docs.append(doc)

        return cleaned_docs
