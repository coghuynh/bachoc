from typing import List, Dict
import logging
from KG_builder.utils.llm_utils import LLM
from dotenv import load_dotenv
import os
import json

load_dotenv()

def extract_triples(context: str, llm: LLM,  **args) -> List[Dict[str, str]]:

    try:
        response = llm.chat(context, json_return=True, **args)
        res = json.loads(response)
    except Exception as e:
        logging.exception(f"Message: {e}")
        
    return res



if __name__ == "__main__":
    text = """
        Albert Einstein was born in Ulm, Germany in 1879. He developed the theory of relativity, which changed how scientists understand space and time. In 1921, he received the Nobel Prize in Physics for his explanation of the photoelectric effect. Later, Einstein worked at Princeton University in the United States. His contributions influenced modern physics and inspired generations of scientists.
    """
    
    res = extract_triples(text)
    
    for triple in res:
        print(triple)
    
    