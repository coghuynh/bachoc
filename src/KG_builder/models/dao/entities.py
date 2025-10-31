from typing import List, Iterable, Tuple
from KG_builder.models.dao.base import BaseDAO, now_iso, iso_to_datetime
from KG_builder.embedding.ops import to_blob, from_blob
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
            source TEXT,
            created_at TEXT NOT NULL,
            removed_at TEXT,
            updated_at TEXT NOT NULL
        );
        """)
        
        self.db.execute("""          
        CREATE TABLE IF NOT EXISTS entity_faiss_map (
            faiss_id TEXT PRIMARY KEY,
            entity_id TEXT UNIQUE NOT NULL,
            FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
        );                
        """)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);")

    def upsert(
        self,
        *,
        id: str = None,
        name: str,
        subject_or_object: str = "both",
        description: str = "",
        source: str = ""
    ) -> str:
        if not id:
            id = hash_id("E", name)
        ts = now_iso()
        self.db.execute("""
        INSERT INTO entities(id, name, subject_or_object, description, source, created_at, removed_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
        ON CONFLICT(id) DO UPDATE SET
          name=excluded.name,
          subject_or_object=excluded.subject_or_object,
          description=excluded.description,
          source=excluded.source,
          updated_at=excluded.updated_at
        """, (id, name, subject_or_object, description, source, ts, ts))
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
            "source": r["source"],
            "created_at": iso_to_datetime(r["created_at"]),
            "updated_at": iso_to_datetime(r["updated_at"]),
        })
        
    def map_faiss_ids(self, pairs: Iterable[Tuple[str, str]]):
        self.db.conn.executemany("""
        INSERT OR REPLACE INTO entity_faiss_map(faiss_id, entity_id) VALUES (?,?)
        """, pairs)
        
    def get_entity_id(self, faiss_id: str) -> str:
        rows = self.db.query("SELECT * FROM entity_faiss_map WHERE faiss_id=?", (faiss_id,))
        if not rows:
            return None
        r = rows[0]
        return r["entity_id"]

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
                "source": r["source"],
                "created_at": iso_to_datetime(r["created_at"]),
                "updated_at": iso_to_datetime(r["updated_at"]),
            }))
        return out
    
    def get_all(self) -> List[Entity]:
        rows = self.db.query(
            "SELECT * FROM entities WHERE (removed_at IS NULL)",
            (),
        )
        out = []
        for r in rows:
            out.append(Entity(**{
                "id": r["id"],
                "name": r["name"],
                "subject_or_object": r["subject_or_object"],
                "description": r["description"],
                "source": r["source"],
                "created_at": iso_to_datetime(r["created_at"]),
                "updated_at": iso_to_datetime(r["updated_at"]),
            }))
        return out
    
    
    
if __name__ == "__main__":
    
    from KG_builder.models.db import DB
    
    db: DB = DB(":memory:")
    entity_dao: EntitiesDAO = EntitiesDAO(db)
    
    with entity_dao.db.transaction():

    
        entity_dao.create_table()

    
        e1 = entity_dao.upsert(name="Albert Einstein", description="Physicist, relativity")
        e2 = entity_dao.upsert(name="Marie Curie", description="Chemist, radioactivity", subject_or_object="subject")
        

    with entity_dao.db.transaction():
        print(e1, e2)
        
        pairs = [("101", e1), ("102", e2)]

        entity_dao.map_faiss_ids(pairs)

    
    got = entity_dao.get(e1)
    assert got is not None and got.name == "Albert Einstein"
    print("get() works")

    
    lst = entity_dao.list_by_name("Marie Curie")
    for e in lst:
        print(e)
    assert any(e.name == "Marie Curie" for e in lst)
    print("list_by_name() works")

    
    cur = entity_dao.db.execute("SELECT * FROM entity_faiss_map ORDER BY faiss_id")
    rows = cur.fetchall()
    assert len(rows) == 2
    assert rows[0][1] == e1 and rows[1][1] == e2
    print("map_faiss_ids() insert verified")


    eid = entity_dao.get_entity_id("101")
    assert eid == e1, f"Expected {e1}, got {eid}"
    print("get_entity_id() works")


    entity_dao.soft_delete(e2)
    deleted = entity_dao.get(e2)
    assert deleted is None
    print("soft_delete() works")


    all_entities = entity_dao.get_all()
    ids = [e.id for e in all_entities]
    
    for e in all_entities:
        print(e.name)
    assert e1 in ids and e2 not in ids
    print("get_all() works (excludes deleted)")

    print("\nAll EntitiesDAO + FAISS map tests passed successfully!")
    
    
        
