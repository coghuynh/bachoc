from typing import Iterable, List, Optional, Tuple
from KG_builder.models.dao.base import BaseDAO, now_iso, iso_to_datetime
from KG_builder.models.schema import Predicate
from KG_builder.utils.utils import hash_id

class PredicatesDAO(BaseDAO):
    def create_table(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS predicates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            definition TEXT,
            created_at TEXT NOT NULL,
            removed_at TEXT,
            updated_at TEXT NOT NULL
        );                              
        """)
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS predicate_faiss_map (
            faiss_id TEXT PRIMARY KEY,
            predicate_id TEXT UNIQUE NOT NULL,
            FOREIGN KEY (predicate_id) REFERENCES predicates(id) ON DELETE CASCADE
        );
        """)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_predicates_name ON predicates(name);")
        
    
    def upsert(
        self,
        *,
        id: Optional[str] = None,
        name: str,
        definition: str = ""
    ) -> str:
        if not id:
            id = hash_id("P", name)
        ts = now_iso()
        
        self.db.execute("""
        INSERT INTO predicates(id, name, definition, created_at, removed_at, updated_at)                
        VALUES (?, ?, ?, ?, NULL, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            definition=excluded.definition,
            updated_at=excluded.updated_at
        """, (id, name, definition, ts, ts))
        return id

    def map_faiss_ids(self, pairs: Iterable[Tuple[str, str]]) -> None:
        pairs = list(pairs)
        if not pairs:
            return
        self.db.conn.executemany(
            "INSERT OR REPLACE INTO predicate_faiss_map(faiss_id, predicate_id) VALUES (?, ?)",
            pairs,
        )
        self.db.conn.commit()

    def get_predicate_id(self, faiss_id: str) -> Optional[str]:
        rows = self.db.query(
            "SELECT predicate_id FROM predicate_faiss_map WHERE faiss_id=?",
            (faiss_id,),
        )
        if not rows:
            return None
        return rows[0]["predicate_id"]
        
    def get(self, id: str) -> Optional[Predicate]:
        rows = self.db.query("SELECT * FROM predicates WHERE id=? AND (removed_at IS NULL)", (id, ))
        if not rows:
            return None
        r = rows[0]
        
        return Predicate(
            id = r["id"],
            name = r["name"],
            definition = r["definition"],
            created_at=iso_to_datetime(r["created_at"]),
            updated_at=iso_to_datetime(r["updated_at"])
        )
        
    def soft_delete(self, id: str):
        self.db.execute(
            "UPDATE predicates SET removed_at=?, updated_at=? WHERE id=?",
            (now_iso(), now_iso(), id),
        )
       
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
                created_at=iso_to_datetime(r["created_at"]),
                updated_at=iso_to_datetime(r["updated_at"])
            ))   
        return out
    
if __name__ == "__main__":
    from KG_builder.models.db import DB
    db = DB()
    dao = PredicatesDAO(db)

    dao.create_table()

    with dao.db.transaction():
        dao.upsert(
            id="p_is_a",
            name="is_a",
            definition="Type/subclass relation"
        )
        dao.upsert(
            id="p_part_of",
            name="part_of",
            definition="Part-whole relation"
        )
        dao.upsert(
            id="p_related_to",
            name="related_to",
            definition="Generic relatedness"
        )

    dao.map_faiss_ids([("42", "p_is_a")])
    assert dao.get_predicate_id("42") == "p_is_a"
    print("map_faiss_ids() OK")

    
    got = dao.get("p_is_a")
    assert got is not None, "get() should return a Predicate"
    assert got.name == "is_a"
    print("get() OK:", got)

    
    listed = dao.list_by_name("of", limit=10)
    assert any(p.name == "part_of" for p in listed), "list_by_name() should include 'part_of'"
    print("list_by_name() OK:", [p.name for p in listed])

    dao.soft_delete("p_related_to")
    none_after_delete = dao.get("p_related_to")
    assert none_after_delete is None, "soft_delete() should hide the row"
    print("soft_delete() OK")

    print("All PredicatesDAO smoke tests passed.")
