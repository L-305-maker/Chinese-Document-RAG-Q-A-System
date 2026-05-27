from config.setting import settings


def _resolve_device() -> str:
    if settings.EMBEDDING_DEVICE == "cpu":
        return "cpu"

    if settings.EMBEDDING_DEVICE == "cuda":
        return "cuda" if _cuda_available() else "cpu"

    return "cuda" if _cuda_available() else "cpu"


def _cuda_available() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except Exception:
        return False


def get_embedding_model():
    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
        model_kwargs={"device": _resolve_device()},
        encode_kwargs={"normalize_embeddings": True},
    )
