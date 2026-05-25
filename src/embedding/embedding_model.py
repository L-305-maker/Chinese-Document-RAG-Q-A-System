import torch
from langchain_huggingface import HuggingFaceEmbeddings

from config.setting import settings


def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
