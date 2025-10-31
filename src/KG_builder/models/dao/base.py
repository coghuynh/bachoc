from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

ISO = "%Y-%m-%dT%H:%M:%S"

def now_iso() -> str:
    return datetime.utcnow().strftime(ISO)

def iso_to_datetime(iso_str: str) -> datetime:
    return datetime.strptime(iso_str, ISO)


class BaseDAO(ABC):
    def __init__(self, db):
        self.db = db

    @abstractmethod
    def create_table(self) -> None: ...
    
    
    