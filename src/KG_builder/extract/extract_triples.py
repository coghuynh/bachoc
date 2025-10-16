from typing import List, Dict
import logging
from KG_builder.utils.llm_utils import CostModel, FreeModel
from dotenv import load_dotenv
import os
import json

load_dotenv()

def extract_triples(context: str) -> List[Dict[str, str]]:

    llm_configs = {
        # "model_name" : "gemini-2.0-flash",
        # "API_KEY" : os.environ["OPENAI"],
        "model_name" : "Qwen/Qwen2.5-0.5B-Instruct",
        "system_prompt" : f"""
            You are an expert information extraction system used to build knowledge graphs.
            Your task is to read a piece of text and extract all meaningful relationships in the form of triples:
            (Subject, Predicate, Object).

            Guidelines:
            - Each triple should represent a clear factual relationship.
            - You can extract triple from multiple sentences that connect the information.
            - Use concise entity names (avoid unnecessary adjectives or phrases).
            - Normalize capitalization (e.g., “Vietnam” not “vietnam”).
            - If the text includes dates, numbers, organizations, or locations, use them as entities where relevant.
            - Do not include subjective or speculative information.
            - If multiple relationships exist in the same sentence, extract each one separately.
            - Output must be a valid JSON array where each element has keys: "subject", "predicate", and "object".
            - Keep the format strictly machine-readable; no explanations, no commentary.

            Example:
            Input: "Albert Einstein was born in Ulm, Germany in 1879. He developed the theory of relativity."
            Output:
            [
            {{"subject": "Albert Einstein", "predicate": "was born in", "object": "Ulm, Germany"}},
            {{"subject": "Albert Einstein", "predicate": "developed", "object": "theory of relativity"}}
            ]
        """,
        "context_template" : f"""
            Extract relational triples from the following text.
            Return only the JSON array of triples (subject, predicate, object) as shown in the examples.

            Text:
            {{context}}
        """
    }
    
    # llm = CostModel(**llm_configs)
    llm = FreeModel(**llm_configs)
    
    idx: int = 0
    
    while idx < 10:
        try:
            response = llm.chat(context, json_return=True)
        
            print(response)
            res = json.loads(response)
            break
        except Exception as e:
            logging.exception(f"Message: {e}")
        finally:
            idx += 1
        
            
        
    return res



if __name__ == "__main__":
    text = """
        Albert Einstein was born in Ulm, Germany in 1879. He developed the theory of relativity, which changed how scientists understand space and time. In 1921, he received the Nobel Prize in Physics for his explanation of the photoelectric effect. Later, Einstein worked at Princeton University in the United States. His contributions influenced modern physics and inspired generations of scientists.
    """
    
    res = extract_triples(text)
    
    for triple in res:
        print(triple)
    
    