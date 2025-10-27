import os
import json
import logging
import pandas as pd
from typing import Set, Dict, List
from KG_builder.utils.clean_data import read_schema, read_json
from KG_builder.utils.clean_data import clean_json_string
from dotenv import load_dotenv
from KG_builder.utils.llm_utils import load_model
from KG_builder.prompts.prompts import DEFINITION_PROMPT
load_dotenv()


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
    

if __name__ == "__main__":
    schema = read_schema("../new_entities.csv")
    result = read_json("../new_sample_entities.json")
    
    unseen = set()
    
    llm = load_model("Qwen/Qwen2.5-0.5B-Instruct")
    print(llm)
    for element in result:
        entity_value = element["entity"]
        entity_type = element["type"]
        if not entity_type.upper() in schema.keys():
            unseen.add(entity_type.upper())
    print(unseen)
    collection = collect_definition(unseen, llm, **DEFINITION_PROMPT)
    
    new_entity_type: Dict[str, List[str]] = {
        "Type" : [collect["type"] for collect in collection],
        "Definition" : [collect["definition"] for collect in collection]
    }
    
    new_df = pd.DataFrame(new_entity_type)
    
    new_df.to_csv("new_entities_test.csv")