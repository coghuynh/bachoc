
from KG_builder.models.schema import Predicate
from KG_builder.models import predicate_dao
from KG_builder.embedding.load import gemini
from typing import List

class PredicatesStorage:
    predicates: List[Predicate]
    dim_size: int 
    
    def add(self, predicate: List[str]): 
        gemini.encode(predicate)
    
        
    
    @classmethod
    def load(cls):
        
        obj = cls()
        obj.predicates = predicate_dao.get_all()
        return obj
        
        
    