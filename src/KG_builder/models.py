from numpy.typing import NDArray
import numpy as np
from dataclasses import asdict, dataclass
from datetime import datetime, date


@dataclass
class Entity:
    id: str
    name: str
    subject_or_object: str
    description: str
    embedding: NDArray[np.float32] | None
    source: str
    created_at: datetime
    removed_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_db_row(cls, row: tuple, columns: list[str]) -> "Entity":
        """Create Entity from database row"""
        data = dict(zip(columns, row))
        
        embedding = None
        if data.get("embedding") is not None:
            embedding = np.array(data["embedding"], dtype=np.float32)
            
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            subject_or_object=str(data["subject_or_object"]),
            description=str(data["description"]),
            embedding=embedding,
            source=data["source"],
            created_at=data["created_at"],
            removed_at=data["removed_at"],
            updated_at=data["updated_at"]
        )
        
    
@dataclass
class Predicate:
    id: str
    name: str
    description: str
    embedding: NDArray[np.float32] | None
    source: str
    created_at: datetime
    removed_at: datetime
    updated_at: datetime
