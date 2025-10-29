from typing import List, Dict
import logging
from KG_builder.llm.base.base_model import BaseLLM
from dotenv import load_dotenv
import os
import json
from KG_builder.utils.clean_data import clean_vn_text, chunk_corpus
from KG_builder.utils.llm_utils import load_model
from KG_builder.prompts.prompts import EXTRACT_TRIPLE_PROMPT
from KG_builder.llm.cost.async_cost_model import AsyncCostModel

def extract_triples(context: str, llm: BaseLLM,  **args) -> List[Dict[str, str]]:

    try:
        response = llm.chat(context, json_return=True, **args)
        res = json.loads(response)
    except Exception as e:
        logging.exception(f"Message: {e}")
        
    return res

async def async_extract_triples(context: str, llm: AsyncCostModel, **args) -> List[Dict[str, str]]:
    try:
        response = await llm.chat(context, json_return=True, **args)
        res = json.loads(response)
    except Exception as e:
        logging.exception(f"Message: {e}")
        
    return res


if __name__ == "__main__":
    
    text = open("./data/(16844277137145_29_06_2024_20_12)do-van-chien-1980-11-17-1719666757.txt", "r", encoding="utf-8").read()
    
    text = clean_vn_text(text)
    
    context = chunk_corpus(text)
    
    from KG_builder.utils.utils import perf
    @perf
    def query(context):
        llm = load_model("gemini-2.0-flash")
        for i, chunk in enumerate(context):
            res = extract_triples(chunk, llm, **EXTRACT_TRIPLE_PROMPT)
        
        
    from KG_builder.llm.cost.async_cost_model import AsyncGeminiModel
    import asyncio
    @perf
    async def async_query(context, llm: AsyncGeminiModel):
        resp = await asyncio.gather(*[async_extract_triples(chunk, llm, **EXTRACT_TRIPLE_PROMPT) for chunk in context])
        
    
    query(context)
    
    inst: AsyncCostModel = AsyncGeminiModel(model_name="gemini-2.0-flash")
    asyncio.run(async_extract_triples(context, inst))
                
    
    
    