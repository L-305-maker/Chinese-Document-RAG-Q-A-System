from langchain_huggingface import HuggingFaceEmbeddings
import torch

def get_embedding_model():
    embedding_model = HuggingFaceEmbeddings(
        model_name = "BAAI/bge-small-zh-v1.5",
        model_kwargs = {"device": "cuda" if torch.cuda.is_available() else "cpu"},
        encode_kwargs = {"normalize_embeddings": True}
    )

    return embedding_model