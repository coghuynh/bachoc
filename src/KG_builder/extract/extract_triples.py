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
    
    text = open("/Users/huynhnguyen/WorkDir/bachoc_1/data/21.nguyen-tung-phong.29-07-1967.15921924574530.1593436323.txt", "r").read()
    
    from KG_builder.utils.clean_data import clean_vn_text, chunk_corpus
    
    text = clean_vn_text(text)
    
    context = chunk_corpus(text)
    
    
    from KG_builder.utils.llm_utils import load_model
    from KG_builder.prompts.prompts import EXTRACT_TRIPLE_PROMPT
    
    llm = load_model("Qwen/Qwen2.5-0.5B-Instruct")
    for i, chunk in enumerate(context):
        
        print(f"Time: {i}")
        res = extract_triples(chunk, llm, **EXTRACT_TRIPLE_PROMPT)
        
    
        for triple in res:
            print(triple)
    
    