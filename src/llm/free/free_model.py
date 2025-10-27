from llm.base.base_model import BaseLLM
from KG_builder.config import DEVICE_MAP, TEMPERATURE, MAX_NEW_TOKENS, REPETITION_PENALTY
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class FreeModel(BaseLLM):
    """Free models (Qwen,...)"""
    def __init__(self, **args):
        super().__init__(**args)

    
class QwenModel(FreeModel):
    def __init__(self, **args):
        super().__init__(**args)
        self.instance = AutoModelForCausalLM.from_pretrained(
            self.name, 
            dtype=torch.float16,
            device_map=DEVICE_MAP
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.name)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
    
    def generate_response(self, context: str, **args):
        messages=[
            {"role": "system", "content" : args["system"]},
            {"role": "user", "content" : context}
        ]
        
        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize input
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.instance.device)
        generated_ids = self.instance.generate(
            **model_inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            repetition_penalty=REPETITION_PENALTY,
            pad_token_id=self.tokenizer.pad_token_id
        )
        
        # Extract only new tokens
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        
        return response
    

if __name__ == "__main__":
    config = {
        "model_name": "Qwen/Qwen2.5-0.5B-Instruct"
    }
    
    qwen = QwenModel(**config)
    prompt = {
        "system": "You are my assistance. Just return JSON format by my context I give you",
        "context_template": "{context}"
    }
    print(qwen.chat(
        "My name is Dang. My hobby is playing games.", json_return=True, **prompt
    ))