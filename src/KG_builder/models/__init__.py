from KG_builder.models.db import DB
from KG_builder.models.dao.predicates import PredicatesDAO
from KG_builder.models.dao.entities import EntitiesDAO
from KG_builder.models.dao.triples import TriplesDAO

db: DB = DB("kg.db")
predicate_dao: PredicatesDAO = PredicatesDAO(db)
entity_dao: EntitiesDAO = EntitiesDAO(db)
triple_dao: TriplesDAO = TriplesDAO(db)

