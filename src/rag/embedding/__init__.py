from rag.embedding.base import BaseEmbedder
from rag.embedding.local_bge import LocalBgeEmbedder


def build_embedder(name: str = "local_bge") -> BaseEmbedder:
    if name == "local_bge":
        return LocalBgeEmbedder()
    raise ValueError(f"Unknown embedder: {name}")


__all__ = ["BaseEmbedder", "build_embedder"]