from typing import Optional, List, Dict, Any
from KG_builder.models.dao.base import BaseDAO, now_iso, iso_to_datetime
from KG_builder.utils.embedding_utils import to_blob, from_blob
from KG_builder.models.schema import Entity
from KG_builder.utils.utils import hash_id
import numpy as np

class EntitiesDAO(BaseDAO):
    def create_table(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS entities (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          subject_or_object TEXT CHECK(subject_or_object IN ('subject','object','both')) NOT NULL DEFAULT 'both',
          description TEXT,
          embedding BLOB,
          embedding_dim INTEGER,
          source TEXT,
          created_at TEXT NOT NULL,
          removed_at TEXT,
          updated_at TEXT NOT NULL
        );
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);")

    def upsert(
        self,
        *,
        id: str = None,
        name: str,
        subject_or_object: str = "both",
        description: str = "",
        embedding: Optional[np.ndarray] = None,
        source: str = ""
    ) -> str:
        if not id:
            id = hash_id("E", name)
        blob, dim = to_blob(embedding)
        ts = now_iso()
        self.db.execute("""
        INSERT INTO entities(id, name, subject_or_object, description, embedding, embedding_dim, source, created_at, removed_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
        ON CONFLICT(id) DO UPDATE SET
          name=excluded.name,
          subject_or_object=excluded.subject_or_object,
          description=excluded.description,
          embedding=excluded.embedding,
          embedding_dim=excluded.embedding_dim,
          source=excluded.source,
          updated_at=excluded.updated_at
        """, (id, name, subject_or_object, description, blob, dim, source, ts, ts))
        return id

    def get(self, id: str) -> Entity:
        rows = self.db.query("SELECT * FROM entities WHERE id=? AND (removed_at IS NULL)", (id,))
        if not rows:
            return None
        r = rows[0]
        return Entity(**{
            "id": r["id"],
            "name": r["name"],
            "subject_or_object": r["subject_or_object"],
            "description": r["description"],
            "embedding": from_blob(r["embedding"], r["embedding_dim"]),
            "source": r["source"],
            "created_at": iso_to_datetime(r["created_at"]),
            "updated_at": iso_to_datetime(r["updated_at"]),
        })

    def soft_delete(self, id: str):
        self.db.execute("UPDATE entities SET removed_at=?, updated_at=? WHERE id=?",
                        (now_iso(), now_iso(), id))

    def list_by_name(self, q: str, limit: int = 50) -> List[Entity]:
        rows = self.db.query(
            "SELECT * FROM entities WHERE name LIKE ? AND (removed_at IS NULL) ORDER BY name LIMIT ?",
            (f"%{q}%", limit),
        )
        out = []
        for r in rows:
            out.append(Entity(**{
                "id": r["id"],
                "name": r["name"],
                "subject_or_object": r["subject_or_object"],
                "description": r["description"],
                "embedding": None,  
                "source": r["source"],
                "created_at": iso_to_datetime(r["created_at"]),
                "updated_at": iso_to_datetime(r["updated_at"]),
            }))
        return out
    
    
if __name__ == "__main__":
    from KG_builder.models.db import DB

    # Simple smoke test for PredicatesDAO
    db = DB()
    dao = PredicatesDAO(db)

    # Ensure table exists
    dao.create_table()

    # Insert a few rows
    import numpy as np
    emb = np.array([0.1, 0.2, 0.3], dtype=np.float32)

    with dao.db.transaction():
        dao.upsert(
            id="p_is_a",
            name="is_a",
            definition="Type/subclass relation",
            embedding=emb,
        )
        dao.upsert(
            id="p_part_of",
            name="part_of",
            definition="Part-whole relation",
            embedding=emb,
        )
        dao.upsert(
            id="p_related_to",
            name="related_to",
            definition="Generic relatedness",
            embedding=None,
        )

    # Get by id
    got = dao.get("p_is_a")
    assert got is not None, "get() should return a Predicate"
    assert got.name == "is_a"
    print("get() OK:", got)

    # List by name (LIKE)
    listed = dao.list_by_name("of", limit=10)
    assert any(p.name == "part_of" for p in listed), "list_by_name() should include 'part_of'"
    print("list_by_name() OK:", [p.name for p in listed])

    # Soft-delete and verify it no longer appears
    dao.soft_delete("p_related_to")
    none_after_delete = dao.get("p_related_to")
    assert none_after_delete is None, "soft_delete() should hide the row"
    print("soft_delete() OK")

    print("All PredicatesDAO smoke tests passed.")