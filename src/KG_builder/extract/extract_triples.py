from typing import List, Dict
import logging
from llm.base.base_model import BaseLLM
from dotenv import load_dotenv
import os
import json
from KG_builder.utils.clean_data import clean_vn_text, chunk_corpus
from KG_builder.utils.llm_utils import load_model
from KG_builder.prompts.prompts import EXTRACT_TRIPLE_PROMPT
    
load_dotenv()

def extract_triples(context: str, llm: BaseLLM,  **args) -> List[Dict[str, str]]:

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
    
    text = open("D:/fico/DỰ_ÁN/data/(16844277137145_29_06_2024_20_12)do-van-chien-1980-11-17-1719666757.txt", "r", encoding="utf-8").read()
    
    text = clean_vn_text(text)
    
    context = chunk_corpus(text)
    
    llm = load_model("gemini-2.0-flash")
    for i, chunk in enumerate(context):
        
        print(f"Time: {i}")
        res = extract_triples(chunk, llm, **EXTRACT_TRIPLE_PROMPT)
        
        for triple in res:
            print(triple)
    
    