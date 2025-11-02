from numpy.typing import NDArray
import numpy as np
from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass
class Entity:
    id: str
    name: str
    role: str
    description: str
    embedding: NDArray[np.float32] | None
    created_at: datetime
    removed_at: datetime | None
    updated_at: datetime
    page: int | None
    confidence: float | None
    source: str | None
    
    
    def to_dict(self) -> dict:
        data = asdict(self)
        if self.embedding is not None:
            data["embedding"] = self.embedding.tolist() # Convert ndarray to list for JSON
        return data
            
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
            role=str(data["role"]),
            description=str(data["description"]),
            embedding=embedding,
            created_at=data["created_at"],
            removed_at=data.get("removed_at"),
            updated_at=data["updated_at"],
            page=data.get("page"),
            confidence=data.get("confidence"),
            source=data.get("source")
        )
        
    
@dataclass
class Predicate:
    id: str
    name: str
    description: str
    embedding: NDArray[np.float32] | None
    created_at: datetime
    removed_at: datetime | None
    updated_at: datetime
    page: int | None
    confidence: float | None
    source: str | None
    
    def to_dict(self):
        data = asdict(self)
        if self.embedding is not None:
            data["embedding"] = self.embedding.tolist()
        return data
    
    @classmethod
    def from_db_row(cls, row: tuple, columns: list[str]):
        """Create Predicate from database"""
        data = dict(zip(columns, row))
        
        embedding = None
        if data["embedding"] is not None:
            embedding = np.array(data["embedding"], dtype=np.float32)
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            embedding=embedding,
            source=data["source"],
            created_at=data["created_at"],
            removed_at=data.get("removed_at"),
            updated_at=data["updated_at"],
            page=data.get("page"),
            confidence=data.get("confidence"),
            source=data.get("source")
        )