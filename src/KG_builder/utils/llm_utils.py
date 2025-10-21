from abc import ABC, abstractmethod
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from openai import OpenAI
from google import genai
from google.genai.types import GenerateContentConfig
from dotenv import load_dotenv
import logging
import os

load_dotenv()




class LLM(ABC):
    
    def __init__(self, **args):
        self.name = args["model_name"]
    
    @abstractmethod
    def chat(context: str, **args):
        pass
    

class FreeModel(LLM):
    def __init__(self, **args):
        super().__init__(**args)
        if args["model_name"].count("Qwen"):
            self.instance = AutoModelForCausalLM.from_pretrained(
                        self.name, 
                        dtype=torch.float16,
                        device_map="auto"
                )
            self.tokenizer = AutoTokenizer.from_pretrained(self.name)
            if self.tokenizer.pad_token_id is None:
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
                
    
    def chat(self, context: str, json_return: bool = False, **args):
        response: str = ""
        
        if self.name.count("Qwen"):    
            try:
                if args["context_template"]:
                    resp = self.generate_response(
                        [
                            {"role": "system", "content": args["system"]},
                            {"role": "user", "content": args["context_template"].format(context = context)}
                        ]
                    )
                    
                else:
                    resp = self.generate_response(
                        [
                            {"role": "system", "content": args["system"]},
                            {"role": "user", "content": context}
                        ]
                    )
            except Exception as e:
                logging.exception(f"Message in Qwen response: {e}")
                raise Exception(f"Qwen problem {e}")
        
        if json_return:
            response = json_valid(resp)
            
        return response
    
    def generate_response(self, messages: list[dict[str, str]]):
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.instance.device)
        generated_ids = self.instance.generate(
            **model_inputs,
            max_new_tokens=500,
            temperature=0.7,
            repetition_penalty=1.2
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        return response
    

class CostModel(LLM):
    def __init__(self, **args):
        super().__init__(**args)
        if args["model_name"].count("gpt"):
            self.instance = OpenAI(api_key=os.environ["OPENAI"])
        elif args["model_name"].count("gemini"):
            self.instance = genai.Client()
            
    def chat(self, context: str, json_return: bool = False, **args):
        response: str = ""
        
        if self.name.count("gpt"):
            try:
                if args["context_template"]:
                    resp = self.instance.responses.create(
                        model = self.name,
                        input = [
                            {"role": "system", "content" : args["system"]},
                            {"role": "user", "content" : args["context_template"].format(context = context)}
                        ]
                    )
                else:
                    resp = self.instance.response.create(
                        model = self.name,
                        input = [
                            {"role": "system", "content" : args["system"]},
                            {"role": "user", "content" : context}
                        ]
                    )
            except Exception as e:
                logging.exception(f"Message in gpt response: {e}")
                raise Exception(f"GPT problem {e}")
            response = resp.output_text
                
        if self.name.count("gemini"):
            try:
                if args["context_template"]:
                    resp = self.instance.models.generate_content(
                        model = self.name,
                        contents =  args["context_template"].format(context = context), 
                        config=GenerateContentConfig(
                            system_instruction=args["system"]
                        )
                    )
                else:
                    resp = self.instance.models.generate_content(
                        model = self.name,
                        contents = context, 
                        config=GenerateContentConfig(
                            system_instruction=args["system"]
                        )
                    )
                response = resp.text
            except Exception as e:
                logging.exception(f"Message in Gemini response: {e}")
                raise Exception(f"Gemini problem {e}")
    
        
        if json_return:
            response = json_valid(response)
            
        return response
        
        
def json_valid(raw_resp: str) -> str:
    raw_resp = raw_resp.strip("`").replace("json", "").strip()
    return raw_resp

def load_model(model_name: str) -> LLM:
    model: LLM = None
    if model_name.count("gpt") or model_name.count("gemini"):
        model = CostModel(model_name = model_name)
    else:
        model = FreeModel(model_name = model_name)
        
    return model


if __name__ == "__main__":
    
    llm = load_model("gemini-2.5-flash")
    
    # Test 3
    config = {
        "system": "You are my assistance. Just return JSON format by my context I give you",
        "context_template": "{context}"
    }
    
    print(llm.chat(
        "My name is Dang. My hobby is playing games.", json_return=True, **config
    ))
               