from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


class EmbeddingStorage:
    def __init__(
        self,
        index_path: str,
        *,
        d: int,
        metric: Optional[str] = None,
        **_: int,
    ) -> None:
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        self.d = int(d)
        if isinstance(metric, str):
            self.metric = metric.lower()
        else:
            self.metric = "l2"
        self.efSearch: Optional[int] = None

        self._ids = np.empty(0, dtype=np.int64)
        self._embeddings = np.empty((0, self.d), dtype=np.float32)
        self._id_to_index: dict[int, int] = {}

        self._load()

    # Public API -----------------------------------------------------------------
    def add(self, embeddings: np.ndarray, ids: np.ndarray) -> None:
        embeddings, ids = self._prepare_inputs(embeddings, ids)
        self._remove_ids(ids)
        self._append(ids, embeddings)
        self._save()

    def upsert(self, embeddings: np.ndarray, ids: np.ndarray) -> None:
        embeddings, ids = self._prepare_inputs(embeddings, ids)
        self._remove_ids(ids)
        self._append(ids, embeddings)
        self._save()

    def remove(self, ids: np.ndarray) -> int:
        ids = self._as_int64_vector(ids)
        removed = self._remove_ids(ids)
        if removed:
            self._save()
        return removed

    def search(self, queries: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        queries = self._as_float32_matrix(queries)
        if self.count() == 0 or k <= 0:
            n = queries.shape[0]
            D = np.full((n, k), np.inf, dtype=np.float32)
            I = np.full((n, k), -1, dtype=np.int64)
            return D, I

        distances = self._pairwise_distance(queries)
        n_queries = queries.shape[0]
        k_avail = min(k, self._ids.size)

        D = np.full((n_queries, k), np.inf, dtype=np.float32)
        I = np.full((n_queries, k), -1, dtype=np.int64)

        if k_avail == 0:
            return D, I

        idx_part = np.argpartition(distances, kth=k_avail - 1, axis=1)[:, :k_avail]
        topk_dists = np.take_along_axis(distances, idx_part, axis=1)
        ids_matrix = np.broadcast_to(self._ids, (n_queries, self._ids.size))
        topk_ids = np.take_along_axis(ids_matrix, idx_part, axis=1)

        order = np.argsort(topk_dists, axis=1)
        sorted_dists = np.take_along_axis(topk_dists, order, axis=1)
        sorted_ids = np.take_along_axis(topk_ids, order, axis=1)

        D[:, :k_avail] = sorted_dists
        I[:, :k_avail] = sorted_ids
        return D, I

    def set_efSearch(self, value: int) -> None:  # compatibility no-op
        self.efSearch = value

    def count(self) -> int:
        return int(self._ids.size)

    def get_vector(self, internal_id: int) -> Optional[np.ndarray]:
        idx = self._id_to_index.get(int(internal_id))
        if idx is None:
            return None
        return np.array(self._embeddings[idx], copy=True)

    # Internal helpers ------------------------------------------------------------
    def _prepare_inputs(self, embeddings: np.ndarray, ids: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        embeddings = self._as_float32_matrix(embeddings)
        ids = self._as_int64_vector(ids)

        if embeddings.shape[0] != ids.shape[0]:
            raise ValueError("embeddings and ids must contain the same number of rows")
        if embeddings.shape[1] != self.d:
            raise ValueError(f"embedding dimension mismatch ({embeddings.shape[1]} != {self.d})")
        return embeddings, ids

    def _append(self, ids: np.ndarray, embeddings: np.ndarray) -> None:
        if self._ids.size == 0:
            self._ids = ids.copy()
            self._embeddings = embeddings.copy()
        else:
            self._ids = np.concatenate([self._ids, ids])
            self._embeddings = np.concatenate([self._embeddings, embeddings], axis=0)
        self._sync_lookup()

    def _remove_ids(self, ids: np.ndarray) -> int:
        if self._ids.size == 0:
            return 0
        remove_set = {int(x) for x in ids.tolist()}
        if not remove_set:
            return 0
        mask = np.array([int(x) not in remove_set for x in self._ids], dtype=bool)
        removed = int(self._ids.size - mask.sum())
        if removed == 0:
            return 0
        self._ids = self._ids[mask]
        self._embeddings = self._embeddings[mask]
        self._sync_lookup()
        return removed

    def _pairwise_distance(self, queries: np.ndarray) -> np.ndarray:
        if self.metric == "cosine":
            q_norm = queries / np.linalg.norm(queries, axis=1, keepdims=True).clip(min=1e-12)
            e_norm = self._embeddings / np.linalg.norm(self._embeddings, axis=1, keepdims=True).clip(min=1e-12)
            similarity = q_norm @ e_norm.T
            return (1.0 - similarity).astype(np.float32, copy=False)

        diff = queries[:, None, :] - self._embeddings[None, :, :]
        return np.sum(diff * diff, axis=2, dtype=np.float32)

    def _save(self) -> None:
        with self.index_path.open("wb") as fh:
            np.savez_compressed(
                fh,
                ids=self._ids.astype(np.int64, copy=False),
                embeddings=self._embeddings.astype(np.float32, copy=False),
                metadata=np.asarray([self.d], dtype=np.int64),
            )

    def _load(self) -> None:
        if not self.index_path.exists():
            return
        try:
            with self.index_path.open("rb") as fh:
                with np.load(fh, allow_pickle=False) as data:
                    ids = data["ids"].astype(np.int64)
                    embeddings = data["embeddings"].astype(np.float32)
                    if embeddings.ndim != 2 or embeddings.shape[1] != self.d:
                        logging.warning(
                            "Stored embedding index %s has incompatible dimension; reinitialising.",
                            self.index_path,
                        )
                        self.index_path.unlink(missing_ok=True)
                        return
                    self._ids = ids
                    self._embeddings = embeddings
                    self._sync_lookup()
        except Exception as exc:  # pragma: no cover
            logging.warning(
                "Failed to load embedding index %s (%s); removing file and starting empty.",
                self.index_path,
                exc,
            )
            self.index_path.unlink(missing_ok=True)

    def _sync_lookup(self) -> None:
        self._id_to_index = {int(idx): pos for pos, idx in enumerate(self._ids.tolist())}

    @staticmethod
    def _as_float32_matrix(values: np.ndarray) -> np.ndarray:
        arr = np.asarray(values, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.ndim != 2:
            raise ValueError("embeddings must be a 2D array")
        return np.ascontiguousarray(arr)

    @staticmethod
    def _as_int64_vector(values: np.ndarray) -> np.ndarray:
        arr = np.asarray(values, dtype=np.int64)
        if arr.ndim == 2 and arr.shape[1] == 1:
            arr = arr.reshape(-1)
        if arr.ndim != 1:
            raise ValueError("ids must be a 1D array")
        return np.ascontiguousarray(arr)
