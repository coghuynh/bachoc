import os
import json
import logging
import pandas as pd
from typing import Set, Dict, List
from KG_builder.utils.clean_data import read_schema, read_json
from KG_builder.utils.llm_utils import load_model
from KG_builder.prompts.prompts import DEFINITION_PROMPT
from KG_builder.llm.cost.async_cost_model import AsyncCostModel


# New function for predicate definitions
def collect_definition(unseen: Set[str], llm, **args) -> List[Dict[str, str]]:
    """
    Similar to collect_definition() but for relation/predicate types.
    Generates short, ontology-style definitions for predicates used in a Knowledge Graph.
    """

    try:
        result = llm.chat(str(unseen), True, **args)
        print(result)
    except Exception as e:
        logging.exception(f"Message: {e}")
        result = "[]"

    try:
        result = json.loads(result)
    except Exception as e:
        logging.exception(f"Message: {e}")
        result = []
    return result

async def async_collect_definition(unseen: Set[str], llm: AsyncCostModel, **args) -> List[Dict[str, str]]:
    try:
        result = await llm.chat(str(unseen), True, **args)
        print(result)
    except Exception as e:
        logging.exception(f"Message: {e}")
        result = "[]"

    try:
        result = json.loads(result)
    except Exception as e:
        logging.exception(f"Message: {e}")
        result = []
    return result
    

if __name__ == "__main__":
    
    import asyncio
    
    from KG_builder.llm.cost.async_cost_model import AsyncGeminiModel
    
    ins: AsyncGeminiModel = AsyncGeminiModel(model_name="gemini-2.0-flash")
    
    asyncio.run(async_collect_definition(
        {"apple", "lemon", "juice"},
        ins,
        **DEFINITION_PROMPT
    ))