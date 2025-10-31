import pytest

from KG_builder.models.dao.predicates import PredicatesDAO
from KG_builder.models.db import DB


@pytest.fixture
def predicates_dao():
    db = DB(":memory:")
    dao = PredicatesDAO(db)
    dao.create_table()
    try:
        yield dao
    finally:
        db.close()


def test_upsert_and_get(predicates_dao):
    pid = predicates_dao.upsert(name="regulates", definition="Controls a process")
    assert pid.startswith("P_")

    fetched = predicates_dao.get(pid)
    assert fetched is not None
    assert fetched.definition == "Controls a process"

    predicates_dao.upsert(id=pid, name="regulates", definition="Updated description")
    refetched = predicates_dao.get(pid)
    assert refetched is not None
    assert refetched.definition == "Updated description"


def test_faiss_mapping_roundtrip(predicates_dao):
    predicates_dao.map_faiss_ids([])

    pid_a = predicates_dao.upsert(name="related_to", definition="Generic relatedness")
    pid_b = predicates_dao.upsert(name="causes", definition="Cause and effect")

    predicates_dao.map_faiss_ids([("101", pid_a)])
    assert predicates_dao.get_predicate_id("101") == pid_a

    # Re-map the same FAISS id to a different predicate (should replace the old mapping)
    predicates_dao.map_faiss_ids([("101", pid_b)])
    assert predicates_dao.get_predicate_id("101") == pid_b

    rows = predicates_dao.db.query(
        "SELECT faiss_id, predicate_id FROM predicate_faiss_map WHERE faiss_id=?",
        ("101",),
    )
    assert len(rows) == 1
    assert rows[0]["predicate_id"] == pid_b

    assert predicates_dao.get_predicate_id("999") is None
