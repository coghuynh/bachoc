from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

import numpy as np
from dotenv import load_dotenv

from KG_builder.embedding.load.cost import GeminiEmbedModel
from KG_builder.embedding.load.free import QwenEmbedding
from KG_builder.embedding.storages import (
    EntityEmbeddingManager,
    EntityStorage,
    PredicateEmbeddingManager,
    PredicateStorage,
)
from KG_builder.extract.definition import async_collect_definition
from KG_builder.extract.extract_triples import async_extract_triples
from KG_builder.models.dao.entities import EntitiesDAO
from KG_builder.models.dao.predicates import PredicatesDAO
from KG_builder.models.dao.triples import TriplesDAO
from KG_builder.models.db import DB
from KG_builder.prompts.prompts import DEFINITION_PROMPT, EXTRACT_TRIPLE_PROMPT
from KG_builder.utils.clean_data import chunk_corpus, read_schema, write_schema
from KG_builder.utils.llm_utils import load_async_model
from KG_builder.utils.utils import hash_id



class KnowledgeGraphBuilder:
    def __init__(self, **args) -> None:
        self.entities_schema_path = Path(args["entities_schema"])
        self.relations_schema_path = Path(args["relation_schema"])
        self.threshold = float(args.get("threshold", 0.7))

        self.extract_triples_model = load_async_model(args["triples_model"])
        self.definition_model = load_async_model(args["definition_model"])
        embedding_name = args.get("embedding_model", "Qwen/Qwen2.5-0.5B-Instruct")
        if "qwen" in embedding_name.lower():
            self.embed_model = QwenEmbedding(model_name=embedding_name)
        else:
            self.embed_model = GeminiEmbedModel(
                model_name=embedding_name,
                requests_per_minute=args.get("embedding_rpm"),
            )

        self.db = DB(args.get("db_path", "kg.db"))
        self.entities_dao = EntitiesDAO(self.db)
        self.predicates_dao = PredicatesDAO(self.db)
        self.triples_dao = TriplesDAO(self.db)

        self.entities_dao.create_table()
        self.predicates_dao.create_table()
        self.triples_dao.create_table()

        self.entity_index_path = Path(args.get("entity_index_path", "data/entity.index"))
        self.predicate_index_path = Path(args.get("predicate_index_path", "data/predicate.index"))

        index_cfg = args.get("index_params", {})
        self.entity_index_params = {
            "M": index_cfg.get("entity_M", 32),
            "efConstruction": index_cfg.get("entity_efConstruction", 200),
            "efSearch": index_cfg.get("entity_efSearch", 64),
        }
        self.predicate_index_params = {
            "M": index_cfg.get("predicate_M", 32),
            "efConstruction": index_cfg.get("predicate_efConstruction", 200),
            "efSearch": index_cfg.get("predicate_efSearch", 64),
        }

        self._embedding_dim = args.get("embedding_dim")
        self._entity_storage: Optional[EntityStorage] = None
        self._predicate_storage: Optional[PredicateStorage] = None
        self._entity_manager: Optional[EntityEmbeddingManager] = None
        self._predicate_manager: Optional[PredicateEmbeddingManager] = None
        self._schema_bootstrapped = False

    @property
    def entity_manager(self) -> EntityEmbeddingManager:
        if self._entity_manager is None:
            raise RuntimeError("Entity storage has not been initialised.")
        return self._entity_manager

    @property
    def predicate_manager(self) -> PredicateEmbeddingManager:
        if self._predicate_manager is None:
            raise RuntimeError("Predicate storage has not been initialised.")
        return self._predicate_manager

    async def run_async(
        self,
        context: str,
        chunk_config: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, str]]:
        await self._bootstrap_schema_embeddings()

        if not context or not context.strip():
            logging.warning("Empty context received; skipping triple extraction.")
            return []

        chunk_kwargs = chunk_config or {}
        try:
            contexts = chunk_corpus(context, **chunk_kwargs)
        except TypeError:
            logging.exception("Invalid chunk configuration provided; using defaults.")
            contexts = chunk_corpus(context)

        if not contexts:
            contexts = [context]

        triples = await self._extract_triples(contexts)
        if not triples:
            logging.warning("No triples extracted from provided context.")
            return []

        predicate_names = {t["predicate"].strip() for t in triples if t.get("predicate")}
        predicate_map = await self._prepare_predicates(predicate_names)

        entity_names = {t["subject"].strip() for t in triples if t.get("subject")}
        entity_names.update({t["object"].strip() for t in triples if t.get("object")})
        entity_map = await self._prepare_entities(entity_names)

        persisted: List[Dict[str, str]] = []
        for triple in triples:
            subject = triple.get("subject", "").strip()
            predicate = triple.get("predicate", "").strip()
            obj = triple.get("object", "").strip()
            if not subject or not predicate or not obj:
                continue

            canonical_predicate = predicate_map.get(predicate, predicate)
            subject_id = entity_map.get(subject)
            object_id = entity_map.get(obj)
            if subject_id is None or object_id is None:
                continue

            predicate_id = hash_id("P", canonical_predicate)
            triple_id = hash_id("T", subject_id, predicate_id, object_id)

            self.triples_dao.upsert(
                id=triple_id,
                subject_id=subject_id,
                predicate_id=predicate_id,
                object_id=object_id,
            )

            persisted.append(
                {
                    "subject": subject,
                    "subject_id": subject_id,
                    "predicate": canonical_predicate,
                    "predicate_id": predicate_id,
                    "object": obj,
                    "object_id": object_id,
                }
            )

        return persisted

    def run(self, context: str, chunk_config: Optional[Dict[str, int]] = None) -> List[Dict[str, str]]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.run_async(context, chunk_config))
        else:
            if loop.is_running():
                raise RuntimeError("Use 'await run_async(...)' when already inside an event loop.")
            return loop.run_until_complete(self.run_async(context, chunk_config))

    def write_schema(self, path: str) -> None:
        write_schema(self.relations_schema, path)

    async def _bootstrap_schema_embeddings(self) -> None:
        if self._schema_bootstrapped:
            return

        entity_items = list(self.entities_schema.items())
        predicate_items = list(self.relations_schema.items())

        entity_vectors = (
            await self._encode([self._entity_schema_text(name, definition) for name, definition in entity_items])
            if entity_items
            else None
        )
        predicate_vectors = (
            await self._encode([self._predicate_text(name, definition) for name, definition in predicate_items])
            if predicate_items
            else None
        )

        dim = self._embedding_dim
        if dim is None:
            if entity_vectors is not None:
                dim = entity_vectors.shape[1]
            elif predicate_vectors is not None:
                dim = predicate_vectors.shape[1]

        if dim is None:
            self._schema_bootstrapped = True
            return

        self._ensure_storages(dim)

        if entity_vectors is not None:
            for (name, definition), vector in zip(entity_items, entity_vectors):
                entity_id = hash_id("E", name)
                self.entity_manager.upsert(
                    id=entity_id,
                    name=name,
                    description=definition,
                    subject_or_object="both",
                    source="schema",
                    embedding=vector,
                )

        if predicate_vectors is not None:
            for (name, definition), vector in zip(predicate_items, predicate_vectors):
                predicate_id = hash_id("P", name)
                self.predicate_manager.upsert(
                    id=predicate_id,
                    name=name,
                    definition=definition,
                    embedding=vector,
                )

        self._schema_bootstrapped = True

    async def _extract_triples(self, contexts: Sequence[str]) -> List[Dict[str, str]]:
        tasks = [
            async_extract_triples(chunk, self.extract_triples_model, **EXTRACT_TRIPLE_PROMPT)
            for chunk in contexts
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        aggregated: List[Dict[str, str]] = []
        seen: Set[tuple[str, str, str]] = set()

        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logging.exception("Triple extraction failed for chunk %s: %s", idx, result)
                continue
            if not isinstance(result, list):
                logging.warning("Unexpected triple extraction output type for chunk %s", idx)
                continue
            for triple in result:
                if not isinstance(triple, dict):
                    continue
                subject = triple.get("subject", "").strip()
                predicate = triple.get("predicate", "").strip()
                obj = triple.get("object", "").strip()
                if not subject or not predicate or not obj:
                    continue
                key = (subject, predicate, obj)
                if key in seen:
                    continue
                seen.add(key)
                aggregated.append({"subject": subject, "predicate": predicate, "object": obj})

        return aggregated

    async def _prepare_predicates(self, predicate_names: Set[str]) -> Dict[str, str]:
        mapping = {name: name for name in predicate_names if name in self.relations_schema}

        unseen = {name for name in predicate_names if name not in mapping}
        if not unseen:
            return mapping

        definitions = await async_collect_definition(unseen, self.definition_model, **DEFINITION_PROMPT)
        definition_map = {
            item.get("type", "").strip(): item.get("definition", "").strip()
            for item in definitions
            if isinstance(item, dict) and item.get("type")
        }

        for name in unseen:
            definition = definition_map.get(name, "")
            canonical = await self._upsert_predicate(name, definition)
            mapping[name] = canonical

        return mapping

    async def _prepare_entities(self, names: Set[str]) -> Dict[str, str]:
        clean = [name for name in (n.strip() for n in names) if name]
        if not clean:
            return {}

        ordered = list(dict.fromkeys(clean))
        vectors = await self._encode(ordered)
        self._ensure_storages(vectors.shape[1])

        mapping: Dict[str, str] = {}
        for name, vector in zip(ordered, vectors):
            entity_id = self._match_or_create_entity(name, vector)
            mapping[name] = entity_id

        return mapping

    async def _upsert_predicate(self, name: str, definition: str) -> str:
        vector = await self._encode([self._predicate_text(name, definition)])
        self._ensure_storages(vector.shape[1])
        vec = vector[0]
        normalized = self._normalize_vector(vec)

        if self.predicate_manager.storage.count() > 0:
            distances, matches = self.predicate_manager.search(normalized.reshape(1, -1), k=1)
            candidate_id = matches[0][0] if matches and matches[0] else None
            if candidate_id:
                stored_vec = self.predicate_manager.get_embedding(candidate_id)
                if stored_vec is not None:
                    similarity = self._cosine_similarity(normalized, stored_vec)
                    if similarity >= self.threshold:
                        candidate = self.predicates_dao.get(candidate_id)
                        if candidate:
                            return candidate.name

        predicate_id = hash_id("P", name)
        self.predicate_manager.upsert(
            id=predicate_id,
            name=name,
            definition=definition or name,
            embedding=normalized,
        )
        self.relations_schema[name] = definition or name
        return name

    def _match_or_create_entity(self, name: str, vector: np.ndarray) -> str:
        dim = vector.shape[-1] if vector.ndim > 1 else vector.shape[0]
        self._ensure_storages(dim)
        vec = vector.reshape(1, -1) if vector.ndim == 1 else vector
        normalized = self._normalize_vector(vec[0])

        if self.entity_manager.storage.count() > 0:
            distances, matches = self.entity_manager.search(normalized.reshape(1, -1), k=1)
            candidate_id = matches[0][0] if matches and matches[0] else None
            if candidate_id:
                stored_vec = self.entity_manager.get_embedding(candidate_id)
                if stored_vec is not None:
                    similarity = self._cosine_similarity(normalized, stored_vec)
                    if similarity >= self.threshold:
                        return candidate_id

        entity_id = hash_id("E", name)
        self.entity_manager.upsert(
            id=entity_id,
            name=name,
            description=name,
            subject_or_object="both",
            source="extracted",
            embedding=normalized,
        )
        return entity_id

    def _ensure_storages(self, dim: int) -> None:
        if self._embedding_dim is None:
            self._embedding_dim = dim
        if self._embedding_dim != dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self._embedding_dim}, received {dim}"
            )

        if self._entity_storage is None:
            self._entity_storage = EntityStorage(
                str(self.entity_index_path),
                d=dim,
                M=self.entity_index_params["M"],
                efConstruction=self.entity_index_params["efConstruction"],
                efSearch=self.entity_index_params["efSearch"],
            )
            self._entity_manager = EntityEmbeddingManager(self.entities_dao, self._entity_storage)

        if self._predicate_storage is None:
            self._predicate_storage = PredicateStorage(
                str(self.predicate_index_path),
                d=dim,
                M=self.predicate_index_params["M"],
                efConstruction=self.predicate_index_params["efConstruction"],
                efSearch=self.predicate_index_params["efSearch"],
            )
            self._predicate_manager = PredicateEmbeddingManager(
                self.predicates_dao,
                self._predicate_storage,
            )

    async def _encode(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._embedding_dim or 1), dtype=np.float32)
        vectors = await self.embed_model.encode(list(texts))
        if vectors.ndim != 2:
            raise ValueError("Embedding model must return a 2D array.")
        return np.asarray(vectors, dtype=np.float32)

    def _entity_schema_text(self, name: str, definition: str) -> str:
        if definition:
            return f"{name}: {definition}"
        return name

    def _predicate_text(self, name: str, definition: str) -> str:
        if definition:
            return f"{name}: {definition}"
        return name

    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        arr = np.asarray(vector, dtype=np.float32).reshape(-1)
        norm = np.linalg.norm(arr)
        if norm == 0:
            return arr
        return arr / norm

    def _cosine_similarity(self, left: np.ndarray, right: np.ndarray) -> float:
        a = self._normalize_vector(left)
        b = self._normalize_vector(right)
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)


# Backwards compatibility alias
KG_builder = KnowledgeGraphBuilder


if __name__ == "__main__":

    
    sample_text = """
        Albert Einstein was born in Ulm, Germany in 1879. He developed the theory of relativity,
        which changed how scientists understand space and time. In 1921, he received the Nobel Prize
        in Physics for his explanation of the photoelectric effect.
    """

    config = {
        "entities_schema": "entities.csv",
        "relation_schema": "relationships.csv",
        "triples_model": "gemini-2.0-flash",
        "definition_model": "gemini-2.0-flash",
        "embedding_model": "gemini-embedding-001",
        "threshold": 0.7,
        "db_path": "kg.db",
        "entity_index_path": "data/entity.index",
        "predicate_index_path": "data/predicate.index",
    }

    builder = KnowledgeGraphBuilder(**config)
    result = asyncio.run(builder.run_async(sample_text))
    print(result)
