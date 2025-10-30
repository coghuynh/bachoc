from __future__ import annotations

from .embedding_storage import EmbeddingStorage


class EntityStorage(EmbeddingStorage):
    def __init__(self, index_path: str, **kwargs):
        super().__init__(index_path, **kwargs)
