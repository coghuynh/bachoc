from typing import Optional, List, Dict, Any
from KG_builder.models.dao.base import BaseDAO, now_iso, iso_to_datetime
from KG_builder.embedding.ops import to_blob, from_blob
from KG_builder.models.schema import Predicate
from KG_builder.utils.utils import hash_id
import numpy as np

class PredicatesDAO(BaseDAO):
    def create_table(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS predicates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            definition TEXT,
            embedding BLOB,
            embedding_dim INTEGER,
            created_at TEXT NOT NULL,
            removed_at TEXT,
            updated_at TEXT NOT NULL
        );                              
        """)
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_predicates_name ON predicates(name);")
        
    
    def upsert(
        self,
        *,
        id: str,
        name: str,
        definition: str,
        embedding: Optional[np.ndarray] = None, 
    ) -> str:
        if not id:
            id = hash_id("P", name)
        blob, dim = to_blob(embedding)
        ts = now_iso()
        
        self.db.execute("""
        INSERT INTO predicates(id, name, definition, embedding, embedding_dim, created_at, removed_at, updated_at)                
        VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            definition=excluded.definition,
            embedding=excluded.embedding,
            embedding_dim=excluded.embedding_dim,
            created_at=excluded.created_at,
            updated_at=excluded.updated_at
        """, (id, name, definition, blob, dim, ts, ts))
        return id
        
    def get(self, id: str) -> Predicate:
        rows = self.db.query("SELECT * FROM predicates WHERE id=? AND (removed_at IS NULL)", (id, ))
        if not rows:
            return None
        r = rows[0]
        
        return Predicate(
            id = r["id"],
            name = r["name"],
            definition = r["definition"],
            embedding=from_blob(r["embedding"], r["embedding_dim"]),
            created_at=iso_to_datetime(r["created_at"]),
            updated_at=iso_to_datetime(r["updated_at"])
        )
        
    def soft_delete(self, id: str):
       self.db.execute("UPDATE predicates SET removed_at=?, updated_at=? WHERE id=?",
                        (now_iso(), now_iso(), id))
       
    def list_by_name(self, q: str, limit: int = 50) -> List[Predicate]:
        rows = self.db.query(
            "SELECT * FROM predicates WHERE name LIKE ? AND (removed_at IS NULL) ORDER BY name LIMIT ?",
            (f"%{q}%", limit),
        )
        out = []
        for r in rows:
            out.append(Predicate(
                id = r["id"],
                name = r["name"],
                definition = r["definition"],
                embedding=from_blob(r["embedding"], r["embedding_dim"]),
                created_at=iso_to_datetime(r["created_at"]),
                updated_at=iso_to_datetime(r["updated_at"])
            ))   
        return out
    
    def get_all(self) -> List[Predicate]:
        rows = self.db.query(
            "SELECT * FROM predicates WHERE (removed_at IS NULL)",
            (),
        )
        out = []
        for r in rows:
            out.append(Predicate(
                id = r["id"],
                name = r["name"],
                definition = r["definition"],
                embedding=from_blob(r["embedding"], r["embedding_dim"]),
                created_at=iso_to_datetime(r["created_at"]),
                updated_at=iso_to_datetime(r["updated_at"])
            ))   
        return out
    
if __name__ == "__main__":
    from KG_builder.models.db import DB
    db = DB()
    dao = PredicatesDAO(db)

    dao.create_table()

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