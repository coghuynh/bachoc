

from KG_builder.embedding.load.base import BaseEmbed
import torch
from KG_builder.llm.free.free_model import QwenModel
from numpy.typing import NDArray
import numpy as np


class QwenEmbedding:
    def __init__(self, **args):
        self.model = QwenModel(**args)
        self.model.instance.model.eval()
        self.device = self.model.instance.device
        self.max_length = args.get("max_length", 512)

    def encode(self, context: list[str]) -> NDArray[np.float32]:
        
        toks = self.model.tokenizer(
            context,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length,
        )
        toks = {k: v.to(self.device) for k, v in toks.items()}

        
        with torch.inference_mode():
            outputs = self.model.instance.model(
                **toks,
                output_hidden_states=False,
            )
        
            hidden = outputs.last_hidden_state
        
            mask = toks["attention_mask"].unsqueeze(-1)  
            summed = (hidden * mask).sum(dim=1)          
            counts = mask.sum(dim=1).clamp(min=1)        
            embeddings = summed / counts                 

        
        return embeddings.detach().cpu().numpy().astype(np.float32)
    
if __name__ == "__main__":
    free_model = QwenEmbedding(model_name="Qwen/Qwen2.5-0.5B-Instruct")
    out = free_model.encode(["Hello", "1000", "dfhaodfhoasdifao"])
    print(out.shape)
    

    
    
        
    
    