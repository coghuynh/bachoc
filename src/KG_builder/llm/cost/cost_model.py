from KG_builder.llm.base.base_model import BaseLLM
from google import genai
from google.genai.types import GenerateContentConfig
from openai import OpenAI
import os

class CostModelAPIError(Exception):
    pass

class CostModel(BaseLLM):
    """Paid API models (GPT, Gemini)"""
    def __init__(self, **args):
        super().__init__(**args)
    

class GeminiModel(CostModel):
    def __init__(self, **args):
        super().__init__(**args)
        self.api_key = os.environ["GEMINI_API_KEY"]
        
        if not self.api_key:
            raise ValueError("Set api key in .env file of pass an valid api key")
        
        try: 
            self.instance = genai.Client(api_key=self.api_key)
        
        except Exception as e:
            raise CostModelAPIError(f"Failed to connect to Gemini: {str(e)}")
        
        
    def generate_response(self, context: str, **args):
        config = GenerateContentConfig(
            system_instruction=args["system"],
            response_mime_type="application/json",
            response_schema=args["triple_type"]
        )
        try:
            response = self.instance.models.generate_content(
                model=self.name,
                contents=context, 
                config=config
            )
            # check if text in response format
            if hasattr(response, "text"):
                return response.text
            
            # check if candidate in response format
            elif hasattr(response, "candidate") and response.candidates():
                return response.candidates[0].content.parts[0].text
            
            else:
                raise CostModelAPIError("No valid response from Gemini")
        
        except Exception as e:
            raise CostModelAPIError(f"Error: {str(e)}")
    
    
class GPTModel(CostModel):
    def __init__(self, **args):
        super().__init__(**args)
        # self.client = OpenAI(api_key=os.environ["OPENAI"])
        
    def generate_response(self, context: str, **args):
        response = self.client.responses.create(
            model=self.name,
            messages=[
                {"role": "system", "content" : args.get("system")},
                {"role": "user", "content" : context}
            ]
        )
        response = response.output_text
        
    
    