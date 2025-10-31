from abc import ABC, abstractmethod
from KG_builder.utils.clean_data import json_valid


class LLMException(Exception):
    """Custom exception for LLM errors"""
    pass


class BaseLLM(ABC):
    """Abstract base class for Large Language Models"""
    def __init__(self, **args):
        self.name = args.get("model_name")
    
    
    def chat(self, context: str, json_return: bool = False, **args) -> str:
        """Generate a chat response"""
        formatted_context = self._format_context(context, **args)
        response = self.generate_response(formatted_context, **args)
        if json_return:
            response = json_valid(response)

        return response
    
    @abstractmethod
    def generate_response(self, context: str, **args): ...
    
    
    def _format_context(self, context: str, **args) -> str:
        """Format context using template if available"""
        if args.get("context_template"):
            return args["context_template"].format(context=context)
        return context
    

