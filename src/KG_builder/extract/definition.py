from KG_builder.utils.clean_data import read_schema, read_json
from typing import Set, Dict, List
import logging
from KG_builder.utils.clean_data import clean_json_string
import os
from dotenv import load_dotenv
from KG_builder.utils.llm_utils import CostModel, FreeModel
import pandas as pd
    
load_dotenv()


def collect_definition(unseen: Set[str]) -> List[Dict[str, str]]:
    chat_config = {
        "model_name" : "Qwen/Qwen2.5-0.5B-Instruct",
        # "API_KEY": os.environ["OPENAI"],
        "system_prompt" : """
            You are an ontology and schema construction assistant for a Knowledge Graph (KG).
            Your task is to provide precise, academic-style definitions for entity *types* used in
            semantic data extraction from documents (e.g., forms, academic CVs, and medical reports).

            Each entity type represents a **category** of real-world concepts such as PERSON, ORGANIZATION,
            RESEARCH_FIELD, or DEGREE. Your definitions must be concise, unambiguous, and suitable for
            use in a schema or ontology.

            Guidelines:
            - Use 1 per definition.
            - Avoid examples or specific instances.
            - Write definitions as if for a data dictionary or ontology schema.
            - If a type seems redundant or unclear, infer its likely meaning from context (e.g., FORM_FIELD_LABEL, MEDICAL_CONDITION).
            - Output only structured JSON following the provided format.

            Format:
            [
            {"type": "<ENTITY_TYPE>", "definition": "<short, formal definition>"}
            ]
        """,
        "context_template" : """
            The following is a list of unseen entity types extracted from structured document data.
            For each entity type, generate a short, ontology-style definition that captures its
            semantic meaning.

            Unseen entity types:
            {context}

            You **MUST** return output strictly as a JSON array of objects with the fields:
            - "type"
            - "definition"
            """
    }
    
    try:
        # llm = CostModel(**chat_config)
        # result = llm.chat(str(unseen), True)
        llm = FreeModel(**chat_config)
        result = llm.chat(str(unseen), True)
    except Exception as e:
        logging.exception(f"Message: {e}")
    try:
        import json
        result = clean_json_string(result)
        result = json.loads(result)
    except Exception as e:
        logging.exception(f"Message: {e}")
    return result
    

# New function for predicate definitions
def collect_predicate_definition(unseen: Set[str]) -> List[Dict[str, str]]:
    """
    Similar to collect_definition() but for relation/predicate types.
    Generates short, ontology-style definitions for predicates used in a Knowledge Graph.
    """

    chat_config = {
        "model_name": "gemini-2.5-flash",
        # "API_KEY": os.environ["OPENAI"],
        "system_prompt": """
            You are an ontology and schema construction assistant for a Knowledge Graph (KG).
            Your task is to provide precise, academic-style definitions for **relation/predicate types**
            used in semantic data extraction (e.g., WORKS_AT, BORN_IN, HAS_SYMPTOM).

            Requirements:
            - Define the predicate's intended semantic meaning.
            - Keep each definition short, formal, and unambiguous.
            - Avoid examples or specific instances.
            - Focus on the relation itself (not entity descriptions).
            - If a predicate name is unclear, infer a likely conventional meaning.
            - Output strictly structured JSON using the provided format.

            Format:
            [
              {"predicate": "<PREDICATE_TYPE>", "definition": "<short, formal definition>"}
            ]
        """,
        "context_template": """
            The following is a list of unseen predicate types extracted from structured document data.
            For each predicate, generate a short, ontology-style definition that captures its
            intended relational semantics.

            Unseen predicate types:
            {context}

            Return output strictly as a JSON array of objects with the fields:
            - "predicate"
            - "definition"
            """
    }

    try:
        llm = CostModel(**chat_config)
        result = llm.chat(str(unseen), True)
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
    schema = read_schema("D:/fico/DỰ_ÁN/new_entities.csv")
    result = read_json("D:/fico/DỰ_ÁN/new_sample_entities.json")
    
    unseen = set()
    
    for element in result:
        entity_value = element["entity"]
        entity_type = element["type"]
        if not entity_type.upper() in schema.keys():
            unseen.add(entity_type.upper())
            
    collection = collect_definition(unseen)
    
    new_entity_type: Dict[str, List[str]] = {
        "Type" : [collect["type"] for collect in collection],
        "Definition" : [collect["definition"] for collect in collection]
    }
    
    new_df = pd.DataFrame(new_entity_type)
    
    new_df.to_csv("new_entities.csv")
    
    
