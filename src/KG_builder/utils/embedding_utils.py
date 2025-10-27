from typing import List, Callable, Optional, Tuple
from google import genai
from abc import ABC, abstractmethod
import torch
from KG_builder.llm.free.free_model import QwenModel
from sentence_transformers import SentenceTransformer
import numpy as np

def to_blob(emb: Optional[np.ndarray]) -> Tuple[Optional[bytes], Optional[int]]:
    if emb is None:
        return None, None
    emb = np.asarray(emb, dtype=np.float32)
    return emb.tobytes(), emb.shape[0]

def from_blob(blob: Optional[bytes], dim: Optional[int]) -> Optional[np.ndarray]:
    if blob is None or dim is None:
        return None
    arr = np.frombuffer(blob, dtype=np.float32)
    if arr.size != dim:
        return None
    return arr


def cosine_similarity(a, b):
    import numpy as np

    a = np.array(a)
    b = np.array(b)

    if a.ndim > 1:
        a = a.reshape(-1)
    if b.ndim > 1:
        b = b.reshape(-1)

    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)

    if a_norm == 0 or b_norm == 0:
        return 0.0

    return float(np.dot(a, b) / (a_norm * b_norm))
    

class EmbeddingModel(ABC):
    
    def __init__(self, **args):
        self.model_name = args["model_name"]
        if args["similarity"].count("cosine"):
            self.simfunc = cosine_similarity
    
    @abstractmethod
    def encode(self, context: List[str]):
        pass
    
    @abstractmethod
    def similarity(self, definition_1: List[str], definition_2: List[str], similarity_func: Callable[[List[float], List[float]], float]):
        pass
    
    
class CostEmbeddingModel(EmbeddingModel):
    def __init__(self, **args):
        super().__init__(**args)
        self.model = genai.Client()
        
    def encode(self, context: List[str]):
        # while 
        resp = self.model.models.embed_content(
            model=self.model_name,
            contents= context
        )
        
        emb = [e.values for e in resp.embeddings]
        # print(emb)
        return emb
    
    def similarity(self, definition_1: List[str], definition_2: List[str]):
        first_defs = self.encode(definition_1)
        second_defs = self.encode(definition_2)
        
        # print(first_defs)
        
        ret = [
            [self.simfunc(emb_1, emb_2) for emb_2 in second_defs] for emb_1 in first_defs
        ]
        
        return ret
    
    
class QwenEmbedding:
    def __init__(self, **args):
        self.model = QwenModel(**args)
        
    def encode(self, text: str):
        input = self.model.tokenizer([text], return_tensors="pt").to(self.model.instance.device)
        with torch.no_grad():
            outputs = self.model.instance.model(**input, output_hidden_states=True)
            hidden = outputs.last_hidden_state
            embeddings = hidden.mean(dim=1)
            print(embeddings.shape)
        return embeddings.cpu().numpy()
    
    def similarity(self, defi1: list[str], defi2: list[str], similarity_func: Callable[[List[float], List[float]], float]):
        first_def = self.encode(defi1)
        second_def = self.encode(defi2)
        
        ret = [
            [similarity_func(emb_1, emb_2) for emb_2 in second_def] for emb_1 in first_def
        ]
        
        return ret
    
class IntFloatEmbedding:
    def __init__(self, **args):
        self.args = args
        self.name = args.get("model_name")
        self.model = SentenceTransformer(self.name)
    
    def similarity(self, defi1: list[str], defi2: list[str]):
        format_defi1 = ["query: " + text for text in defi1]
        format_defi2 = ["query: " + text for text in defi2]
        first_def = self.model.encode(format_defi1)
        second_def = self.model.encode(format_defi2)
        
        similarities = self.model.similarity(first_def, second_def)
        return similarities
        
if __name__ == "__main__":
    t_1 = [
        "Hello. How are you?",
        "You're good bro."
    ]
    
    t_2 = [
        "Nice to meet you.",
        "Hey whassup."
    ]
        
    embed_config = {
        "model_name" : "Qwen/Qwen2.5-0.5B-Instruct"
    }
    
    embed_model = QwenEmbedding(**embed_config)
    
    print(embed_model.similarity(
        t_1, t_2, cosine_similarity
    ))
    
    multilingual_config = {
        "model_name": "intfloat/multilingual-e5-large"
    }
    
    multilingual_model = IntFloatEmbedding(**multilingual_config)
    
    print(multilingual_model.similarity(
        t_1, t_2
    ))