from typing import List, Callable
from dotenv import load_dotenv
from google import genai
from abc import ABC, abstractmethod

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
        "model_name" : "gemini-embedding-001"
    }
    
    embed_model = EmbeddingModel(**embed_config)
    
    print(embed_model.similarity(
        t_1, t_2, cosine_similarity
    ))
