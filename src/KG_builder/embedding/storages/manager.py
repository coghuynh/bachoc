from __future__ import annotations

import hashlib
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np

from KG_builder.embedding.storages.embedding_storage import EmbeddingStorage
from KG_builder.embedding.storages.entity_storage import EntityStorage
from KG_builder.embedding.storages.predicate_storage import PredicateStorage
from KG_builder.models.dao.entities import EntitiesDAO
from KG_builder.models.dao.predicates import PredicatesDAO
from KG_builder.models.schema import Entity, Predicate


class EmbeddingManagerBase:
    def __init__(
        self,
        dao,
        storage: EmbeddingStorage,
        mapping_table: str,
        record_column: str,
    ) -> None:
        self.dao = dao
        self.storage = storage
        self.mapping_table = mapping_table
        self.record_column = record_column

    def upsert(self, *, embedding: np.ndarray, **record_kwargs) -> str:
        record_id = self.dao.upsert(**record_kwargs)
        self._store_embedding(record_id, embedding)
        return record_id

    def delete(self, record_id: str) -> None:
        self.dao.soft_delete(record_id)
        self._remove_embedding(record_id)

    def get(self, record_id: str):
        return self.dao.get(record_id)

    def list_by_name(self, text: str, limit: int = 50):
        return self.dao.list_by_name(text, limit=limit)

    def search(self, queries: np.ndarray, k: int) -> Tuple[np.ndarray, List[List[Optional[str]]]]:
        distances, raw_ids = self.storage.search(queries, k)
        mapped = self._map_faiss_ids(raw_ids)
        return distances, mapped

    def get_embedding(self, record_id: str) -> Optional[np.ndarray]:
        faiss_id = self._faiss_id_for(record_id)
        vector = self.storage.get_vector(faiss_id)
        if vector is None:
            return None
        return np.asarray(vector, dtype=np.float32)

    def sync_bulk(self, entries: Iterable[Tuple[str, np.ndarray]]) -> None:
        ids: List[int] = []
        vectors: List[np.ndarray] = []
        pairs: List[Tuple[str, str]] = []
        for record_id, embedding in entries:
            vector = self._normalize_embedding(embedding)
            faiss_id = self._faiss_id_for(record_id)
            ids.append(faiss_id)
            vectors.append(vector)
            pairs.append((str(faiss_id), record_id))
        if not ids:
            return
        stacked = np.vstack(vectors)
        id_array = np.asarray(ids, dtype=np.int64)
        self.storage.upsert(stacked, id_array)
        self._register_mappings(pairs)

    def _store_embedding(self, record_id: str, embedding: np.ndarray) -> None:
        faiss_id = self._faiss_id_for(record_id)
        vector = self._normalize_embedding(embedding)
        id_array = np.asarray([faiss_id], dtype=np.int64)
        self.storage.upsert(vector, id_array)
        self._register_mappings([(str(faiss_id), record_id)])

    def _remove_embedding(self, record_id: str) -> None:
        faiss_id = self._faiss_id_for(record_id)
        id_array = np.asarray([faiss_id], dtype=np.int64)
        self.storage.remove(id_array)
        self.dao.db.execute(
            f"DELETE FROM {self.mapping_table} WHERE {self.record_column}=?",
            (record_id,),
        )

    def _map_faiss_ids(self, raw_ids: np.ndarray) -> List[List[Optional[str]]]:
        arr = np.asarray(raw_ids, dtype=np.int64)
        flat = arr.ravel()
        valid = [int(x) for x in flat if x >= 0]
        if not valid:
            mapping = {}
        else:
            unique = sorted(set(valid))
            placeholders = ",".join(["?"] * len(unique))
            rows = self.dao.db.query(
                f"SELECT faiss_id, {self.record_column} FROM {self.mapping_table} WHERE faiss_id IN ({placeholders})",
                tuple(str(x) for x in unique),
            )
            mapping = {int(row["faiss_id"]): row[self.record_column] for row in rows}
        result = []
        idx = 0
        for _ in range(arr.shape[0]):
            row = []
            for _ in range(arr.shape[1]):
                value = flat[idx]
                idx += 1
                if value < 0:
                    row.append(None)
                else:
                    row.append(mapping.get(int(value)))
            result.append(row)
        return result

    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        arr = np.asarray(embedding, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.ndim != 2:
            raise ValueError("embedding must be a 1D or 2D array")
        if arr.shape[1] != self.storage.d:
            raise ValueError("embedding dimension does not match the index")
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized = arr / norms
        return np.ascontiguousarray(normalized)

    def _faiss_id_for(self, record_id: str) -> int:
        digest = hashlib.sha1(record_id.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big") & 0x7FFFFFFFFFFFFFFF

    def _register_mappings(self, pairs: Sequence[Tuple[str, str]]) -> None:
        if not pairs:
            return
        conn = self.dao.db.conn
        was_in_transaction = conn.in_transaction
        self.dao.map_faiss_ids(pairs)
        if not was_in_transaction:
            conn.commit()

class EntityEmbeddingManager(EmbeddingManagerBase):
    def __init__(self, dao: EntitiesDAO, storage: EntityStorage) -> None:
        super().__init__(dao, storage, "entity_faiss_map", "entity_id")

    def get(self, record_id: str) -> Optional[Entity]:
        return super().get(record_id)

    def list_by_name(self, text: str, limit: int = 50) -> List[Entity]:
        return super().list_by_name(text, limit=limit)


class PredicateEmbeddingManager(EmbeddingManagerBase):
    def __init__(self, dao: PredicatesDAO, storage: PredicateStorage) -> None:
        super().__init__(dao, storage, "predicate_faiss_map", "predicate_id")

    def get(self, record_id: str) -> Optional[Predicate]:
        return super().get(record_id)

    def list_by_name(self, text: str, limit: int = 50) -> List[Predicate]:
        return super().list_by_name(text, limit=limit)
