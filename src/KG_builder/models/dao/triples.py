from KG_builder.models.dao.base import BaseDAO, now_iso, iso_to_datetime
from typing import List
from KG_builder.models.schema import Triple
from KG_builder.utils.utils import hash_id
import sqlite3



class TriplesDAO(BaseDAO):
    
    def create_table(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS triples (
            id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            predicate_id TEXT NOT NULL,
            object_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            removed_at TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES entities(id) ON DELETE CASCADE,
            FOREIGN KEY (predicate_id) REFERENCES predicates(id) ON DELETE CASCADE,
            FOREIGN KEY (object_id) REFERENCES entities(id) ON DELETE CASCADE,
            UNIQUE(subject_id, predicate_id, object_id)
        );
        """)
        self.db.execute("PRAGMA foreign_keys = ON;")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_triples_subject_id ON triples(subject_id);")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_triples_predicate_id ON triples(predicate_id);")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_triples_object_id ON triples(object_id);")
        
    def upsert(
        self, 
        *,
        id: str,
        subject_id: str,
        predicate_id: str,
        object_id: str,
    ) -> str:
        if not id:
            id = hash_id("T", f"{subject_id}, {predicate_id}, {object_id}")
        try:
            self.db.execute("""
            INSERT INTO triples(id, subject_id, predicate_id, object_id, created_at, removed_at, updated_at)
            VALUES (?, ?, ?, ?, ?, NULL, ?)
            ON CONFLICT(id) DO UPDATE SET
                subject_id=excluded.subject_id,
                predicate_id=excluded.predicate_id,
                object_id=excluded.object_id,
                updated_at=excluded.updated_at
            """, (id, subject_id, predicate_id, object_id, now_iso(), now_iso()))
        except sqlite3.IntegrityError:
            print("Duplicate triple ignored.")
        return id
            
    def get(self, id: str) -> Triple:
        rows = self.db.query("SELECT * FROM triples WHERE id=? AND (removed_at IS NULL)", (id,))
        if not rows:
            return None
        r = rows[0]
        return Triple(
            id=r["id"],
            subject_id=r["subject_id"],
            predicate_id=r["predicate_id"],
            object_id=r["object_id"],
            created_at=iso_to_datetime(r["created_at"]),
            updated_at=iso_to_datetime(r["updated_at"])
        )
        
    def soft_delete(self, id: str):
        self.db.execute("UPDATE triples SET removed_at=?, updated_at=? WHERE id=?",
                        (now_iso(), now_iso(), id))
    
    def list(self, limit: int = 50) -> List[Triple]:
        rows = self.db.query(
            "SELECT * FROM triples WHERE (removed_at IS NULL) LIMIT ?",
            (limit, ),
        )
        
        out = []
        for r in rows:
            out.append(Triple(
                id=r["id"],
                subject_id=r["subject_id"],
                predicate_id=r["predicate_id"],
                object_id=r["object_id"],
                created_at=iso_to_datetime(r["created_at"]),
                updated_at=iso_to_datetime(r["updated_at"])
            ))
            
        return out
    
if __name__ == "__main__":
    from KG_builder.models.db import DB
    from KG_builder.models.dao.entities import EntitiesDAO
    from KG_builder.models.dao.predicates import PredicatesDAO

    # Use an in-memory DB for testing, enable FK constraints
    db = DB(":memory:")
    

    # DAOs
    entities = EntitiesDAO(db)
    predicates = PredicatesDAO(db)
    triples = TriplesDAO(db)

    # Create tables
    entities.create_table()
    predicates.create_table()
    triples.create_table()

    # Seed minimal rows
    now = now_iso()
    entities.upsert(id="e_subject", name="Albert Einstein")
    entities.upsert(id="e_object", name="Physics")
    predicates.upsert(id="p_related_to", name="related_to", definition="Generic relatedness")

    # Insert triple
    triples.upsert(
        id="t1",
        subject_id="e_subject",
        predicate_id="p_related_to",
        object_id="e_object",
    )

    # Read back
    got = triples.get("t1")
    assert got is not None, "get() should return a Triple"
    assert (got.subject_id, got.predicate_id, got.object_id) == ("e_subject", "p_related_to", "e_object")
    print("get() OK:", got)

    # Duplicate (same S,P,O different ID) should be ignored due to UNIQUE constraint
    triples.upsert(
        id="t_dup",
        subject_id="e_subject",
        predicate_id="p_related_to",
        object_id="e_object",
    )
    all_rows = triples.list(limit=10)
    assert any(t.id == "t1" for t in all_rows), "list() should include the original triple"
    print("list() OK:", [(t.id, t.subject_id, t.predicate_id, t.object_id) for t in all_rows])

    # Soft delete and verify hidden
    triples.soft_delete("t1")
    assert triples.get("t1") is None, "soft_delete() should hide the triple"
    print("soft_delete() OK")

    print("All TriplesDAO smoke tests passed.")