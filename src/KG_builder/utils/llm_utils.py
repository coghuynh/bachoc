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
                
        self.system_prompt = args["system_prompt"]
        if "context_template" in args: 
            self.context_template = args["context_template"]
    
    def chat(self, context: str, json_return: bool = False, **args):
        response: str = ""
        
        if self.name.count("Qwen"):    
            try:
                if self.context_template:
                    resp = self.generate_response(
                        [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": self.context_template.format(context=context)}
                        ]
                    )
                    
                else:
                    resp = self.generate_response(
                        [
                            {"role": "system", "content": self.system_prompt},
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
            self.instance = OpenAI(api_key=args["API_KEY"])
        elif args["model_name"].count("gemini"):
            self.instance = genai.Client()
        
        self.system_prompt = args["system_prompt"]
        if "context_template" in args: 
            self.context_template = args["context_template"]
            
    def chat(self, context: str, json_return: bool = False, **args):
        response: str = ""
        
        if self.name.count("gpt"):
            try:
                if self.context_template:
                    resp = self.instance.responses.create(
                        model = self.name,
                        input = [
                            {"role": "system", "content" : self.system_prompt},
                            {"role": "user", "content" : self.context_template.format(context = context)}
                        ]
                    )
                else:
                    resp = self.instance.response.create(
                        model = self.name,
                        input = [
                            {"role": "system", "content" : self.system_prompt},
                            {"role": "user", "content" : context}
                        ]
                    )
            except Exception as e:
                logging.exception(f"Message in gpt response: {e}")
                raise Exception(f"GPT problem {e}")
            response = resp.output_text
                
        if self.name.count("gemini"):
            try:
                if self.context_template:
                    resp = self.instance.models.generate_content(
                        model = self.name,
                        contents = self.context_template.format(context = context), 
                        config=GenerateContentConfig(
                            system_instruction=self.system_prompt
                        )
                    )
                else:
                    resp = self.instance.models.generate_content(
                        model = self.name,
                        contents = context, 
                        config=GenerateContentConfig(
                            system_instruction=self.system_prompt
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


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    logging.info("Start logging with time format")
    load_dotenv()
    
    # config = {
    #     "model_name": "gpt-3.5-turbo",
    #     "API_KEY": os.environ["OPENAI"],
    #     "system_prompt": "You are my assistance.",
    #     "context_template": "Hello {context}"
    # }
    
    # Test 1
    # llm = CostModel(**config)
    
    # print(llm.chat(
    #     "Huynh",
    # ))
    
    
    # Test 2
    
    config = {
        "model_name": "gpt-3.5-turbo",
        "API_KEY": os.environ["OPENAI"],
        "system_prompt": "You are my assistance. Just return JSON format by my context I give you",
        "context_template": "{context}"
    }
    
    gemini = CostModel(**config)
    print(gemini.chat(
        "My name is Huynh. I am a student in VNU.", json_return=True
    ))
    
    # Test 3
    config = {
        "model_name": "Qwen/Qwen2.5-0.5B-Instruct",
        "system_prompt": "You are my assistance. Just return JSON format by my context I give you",
        "context_template": "{context}"
    }
    
    qwen = FreeModel(**config)
    print(qwen.chat(
        "My name is Dang. My hobby is playing games.", json_return=True
    ))
               