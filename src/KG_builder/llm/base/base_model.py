from abc import ABC, abstractmethod
from KG_builder.utils.clean_data import json_valid


class LLMException(Exception):
    """Custom exception for LLM errors"""
    pass


class BaseLLM(ABC):
    """Abstract base class for Large Language Models"""
    def __init__(self, **args):
        self.name = args.get("model_name")
    
    @abstractmethod
    def generate_response(self, context: str, **args):
        """Generate a response based on the given context."""
        pass