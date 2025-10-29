from KG_builder.embedding.load.base import BaseEmbed
from typing import List
from numpy.typing import NDArray
import numpy as np
from google import genai
import asyncio
from KG_builder.utils.utils import perf




class GeminiEmbedModel(BaseEmbed):
    
    def __init__(self, 
                 *,
                 model_name: str = "gemini-embedding-001"
        ):
        self.model = genai.Client()        
        self.model_name = model_name
        
    
    async def encode(self, context: List[str]) -> NDArray[np.float32]:
        loop = asyncio.get_event_loop()
        
        resp = await loop.run_in_executor( 
            None, 
            lambda: 
                self.model.models.embed_content(
                model = self.model_name,
                contents= context
            )
        )
        
        emb = np.array([e.values for e in resp.embeddings], dtype=np.float32)
        return emb


class NonAsyncGeminiEmbedModel:
    
    def __init__(self, 
                 *,
                 model_name: str = "gemini-embedding-001"
        ):
        self.model = genai.Client()        
        self.model_name = model_name
        
    
    def encode(self, context: List[str]) -> NDArray[np.float32]:
        
        
        
        resp =  self.model.models.embed_content(
                model = self.model_name,
                contents= context
            )
        
        emb = np.array([e.values for e in resp.embeddings], dtype=np.float32)
        return emb
    
    
if __name__ == "__main__":
    import time
    from dotenv import load_dotenv
    
    load_dotenv()
    
    @perf
    def nonasync_test():
        non_async = NonAsyncGeminiEmbedModel()
    
        for i in range(10):
            non_async.encode([
                "hello, fuck",
                "CC",
                "Oh man what the fuck"
            ])
        
    @perf
    async def async_test():
        async_func = GeminiEmbedModel()
        tasks = [
            async_func.encode([
                "hello, fuck",
                "CC",
                "Oh man what the fuck"
            ])
            for _ in range(10)
        ]
        ans = await asyncio.gather(*tasks)
        return ans

    
    nonasync_test()
    
    asyncio.run(async_test())
    