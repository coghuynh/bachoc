
from typing import List, Callable

def consine_similarity(a, b):
    import numpy as np
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    

class EmbeddingModel:
    
    def __init__(self, **args):
        self.model_name = args["model_name"]
        from google import genai
        self.model = genai.Client()
        
    def encode(self, context: List[str]):
        idx: int = 10
        # while 
        resp = self.model.models.embed_content(
            model=self.model_name,
            contents= context
        )
        
        emb = [e.values for e in resp.embeddings]
        # print(emb)
        return emb
    
    def similarity(self, definition_1: List[str], definition_2: List[str], similarity_func: Callable[[List[float], List[float]], float]):
        first_defs = self.encode(definition_1)
        second_defs = self.encode(definition_2)
        
        # print(first_defs)
        
        ret = [
            [similarity_func(emb_1, emb_2) for emb_2 in second_defs] for emb_1 in first_defs
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
    from dotenv import load_dotenv
    
    load_dotenv()
    
    embed_model = EmbeddingModel(**embed_config)
    
    print(embed_model.similarity(
        t_1, t_2, consine_similarity
    ))