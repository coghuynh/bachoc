from KG_builder.llm.base.base_model import BaseLLM
from google import genai
from google.genai.types import GenerateContentConfig
from openai import OpenAI
import os

class CostModel(BaseLLM):
    """Paid API models (GPT, Gemini)"""
    def __init__(self, **args):
        super().__init__(**args)
    

class GeminiModel(CostModel):
    def __init__(self, **args):
        super().__init__(**args)
        self.instance = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        
        
    def generate_response(self, context: str, **args):
        config = GenerateContentConfig(
            system_instruction=args["system"],
        )
        response = self.instance.models.generate_content(
            model=self.name,
            contents=context, 
            config=config
        )
        
        return response.text
    
    
class GPTModel(CostModel):
    def __init__(self, **args):
        super().__init__(**args)
        self.client = OpenAI(api_key=os.environ["OPENAI"])
        
    def generate_response(self, context: str, **args):
        response = self.client.responses.create(
            model=self.name,
            messages=[
                {"role": "system", "content" : args["system"]},
                {"role": "user", "content" : context}
            ]
        )
        response = response.output_text
        
    
    