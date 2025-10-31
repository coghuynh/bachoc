from KG_builder.embedding.load.base import BaseEmbed
from typing import List
from numpy.typing import NDArray
import numpy as np
from google import genai
import asyncio
from time import perf_counter, sleep
import os

from dotenv import load_dotenv

load_dotenv()


class GeminiEmbedModel(BaseEmbed):
    MAX_BATCH = 100

    def __init__(
        self,
        *,
        model_name: str = "gemini-embedding-001",
        requests_per_minute: int | None = None,
    ):
        self.model = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.model_name = model_name
        self._lock = asyncio.Lock()
        self._rpm = requests_per_minute
        if self._rpm and self._rpm > 0:
            self._min_interval = 60.0 / self._rpm
        else:
            self._min_interval = 0.0
        self._last_request: float = 0.0

    async def encode(self, context: List[str]) -> NDArray[np.float32]:
        if not context:
            return np.empty((0, 0), dtype=np.float32)

        loop = asyncio.get_event_loop()
        vectors: List[np.ndarray] = []

        for start in range(0, len(context), self.MAX_BATCH):
            batch = context[start : start + self.MAX_BATCH]

            def _embed_items(items: List[str] = batch):
                response = self.model.models.embed_content(
                    model=self.model_name,
                    contents=items,
                )
                return [np.asarray(embedding.values, dtype=np.float32) for embedding in response.embeddings]

            async with self._lock:
                await self._respect_rate_limit()
                batch_vectors = await loop.run_in_executor(None, _embed_items)
                self._last_request = perf_counter()
            vectors.extend(batch_vectors)

        if not vectors:
            return np.empty((0, 0), dtype=np.float32)

        return np.vstack(vectors)

    async def _respect_rate_limit(self) -> None:
        if self._min_interval <= 0:
            return
        now = perf_counter()
        elapsed = now - self._last_request
        wait_time = self._min_interval - elapsed
        if wait_time > 0:
            await asyncio.sleep(wait_time)


class NonAsyncGeminiEmbedModel:
    MAX_BATCH = 100

    def __init__(
        self,
        *,
        model_name: str = "gemini-embedding-001",
        requests_per_minute: int | None = None,
    ):
        self.model = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model_name = model_name
        self._rpm = requests_per_minute
        if self._rpm and self._rpm > 0:
            self._min_interval = 60.0 / self._rpm
        else:
            self._min_interval = 0.0
        self._last_request: float = 0.0

    def encode(self, context: List[str]) -> NDArray[np.float32]:
        if not context:
            return np.empty((0, 0), dtype=np.float32)

        vectors: List[np.ndarray] = []
        for start in range(0, len(context), self.MAX_BATCH):
            batch = context[start : start + self.MAX_BATCH]
            self._respect_rate_limit_sync()
            response = self.model.models.embed_content(
                model=self.model_name,
                contents=batch,
            )
            vectors.extend(np.asarray(embedding.values, dtype=np.float32) for embedding in response.embeddings)
            self._last_request = perf_counter()

        if not vectors:
            return np.empty((0, 0), dtype=np.float32)

        return np.vstack(vectors)

    async def _respect_rate_limit(self) -> None:
        if self._min_interval <= 0:
            return
        now = perf_counter()
        elapsed = now - self._last_request
        wait_time = self._min_interval - elapsed
        if wait_time > 0:
            await asyncio.sleep(wait_time)

    def _respect_rate_limit_sync(self) -> None:
        if self._min_interval <= 0:
            return
        now = perf_counter()
        elapsed = now - self._last_request
        wait_time = self._min_interval - elapsed
        if wait_time > 0:
            sleep(wait_time)
    
    
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
    
