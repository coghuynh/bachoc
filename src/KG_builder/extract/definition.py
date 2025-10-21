from KG_builder.utils.clean_data import read_schema, read_json
from typing import Set, Dict, List
import logging
from KG_builder.utils.clean_data import clean_json_string
import os
from dotenv import load_dotenv
from KG_builder.utils.llm_utils import CostModel, FreeModel
import pandas as pd
    
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
        import json
        result = json.loads(result)
    except Exception as e:
        logging.exception(f"Message: {e}")
        result = []
    return result
    

if __name__ == "__main__":
    schema = read_schema("./new_entities.csv")
    result = read_json("./new_sample_entities.json")
    
    unseen = set()
    
    for element in result:
        entity_value = element["entity"]
        entity_type = element["type"]
        if not entity_type.upper() in schema.keys():
            unseen.add(entity_type.upper())
            
    collection = collect_definition(unseen)
    
    config = {
        
    }
    
    new_entity_type: Dict[str, List[str]] = {
        "Type" : [collect["type"] for collect in collection],
        "Definition" : [collect["definition"] for collect in collection]
    }
    
    new_df = pd.DataFrame(new_entity_type)
    
    new_df.to_csv("new_entities.csv")
    
    
