import numpy as np
import pytest

faiss = pytest.importorskip("faiss")

from KG_builder.embedding.storages.entity_storage import EntityStorage
from KG_builder.embedding.storages.predicate_storage import PredicateStorage


@pytest.mark.parametrize("storage_cls", [EntityStorage, PredicateStorage])
def test_faiss_storage_roundtrip(tmp_path, storage_cls):
    index_path = tmp_path / f"{storage_cls.__name__}.index"
    storage = storage_cls(str(index_path), d=8, M=16, efConstruction=80, efSearch=32)

    rng = np.random.default_rng(123)
    embeddings = rng.normal(size=(5, 8)).astype(np.float32)
    faiss_ids = np.arange(embeddings.shape[0], dtype=np.int64)

    storage.add(embeddings, faiss_ids)
    assert storage.count() == len(faiss_ids)
    assert index_path.exists()

    D, I = storage.search(embeddings[:1], k=5)
    assert D.shape == (1, 5)
    assert I.shape == (1, 5)
    assert faiss_ids[0] in I[0]

    storage.set_efSearch(24)
    D2, I2 = storage.search(embeddings[1:2], k=3)
    assert I2.shape == (1, 3)

    removed = storage.remove(np.array([faiss_ids[0]], dtype=np.int64))
    assert removed == 1
    assert storage.count() == len(faiss_ids) - 1

    # Removing again should be a no-op
    removed_again = storage.remove(np.array([faiss_ids[0]], dtype=np.int64))
    assert removed_again == 0
