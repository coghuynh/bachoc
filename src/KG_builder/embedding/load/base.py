
from abc import ABC, abstractmethod
from typing import List
from numpy.typing import NDArray
import numpy as np

class BaseEmbed(ABC):
    @abstractmethod
    async def encode(self, context: List[str]) -> NDArray[np.float32]: ...
    
    
