from numpy.typing import NDArray
import numpy as np
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Entity:
    id: str
    name: str
    subject_or_object: str
    description: str
    embedding: NDArray[np.float32] | None
    source: str
    created_at: datetime
    updated_at: datetime
        
    
@dataclass
class Predicate:
    id: str
    name: str
    definition: str
    embedding: NDArray[np.float32] | None
    created_at: datetime
    updated_at: datetime
    
    
@dataclass 
class Triple:
    
    id: str
    subject_id: str
    predicate_id: str
    object_id: str
    created_at: datetime
    updated_at: datetime
    
    


    
    