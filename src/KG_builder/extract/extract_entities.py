# from utils.llm_utils import CostModel
from typing import List, Any, Dict, Tuple

import logging
import json

import google.genai


def corpuses(text: str) -> List[str]:
    sentences = text.split("\n")
    ret: List[str] = []
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            ret.append(sentences[i] + " " + sentences[j])
            
    return ret

def extract_entities(text: str, schema: str) -> List[Any]:
    system_prompt = f"""
    You are an intelligent information extraction assistant.
    Your task is to extract all named entities and their types from the given text.
    
    ### Schema:
    {schema}
    
    ### Goals:
    1. Follow my schema, you can great new one when this entity have existed yet.
    2. Identify key entities (people, organizations, locations, dates, academic terms, etc.)
    3. Assign a semantic type to each entity. 
    4. If an entity does not fit any known type, you are allowed to **create a new type name** that best describes it.
    5. Keep type names short and consistent (e.g., PERSON, UNIVERSITY, POSITION, RESEARCH_FIELD, DEGREE, NEW_TYPE, ...).

    
    ### Output format (JSON list):
    [
      {{"entity": "<entity_text>", "type": "<entity_type>"}},
      ...
    ]
    
    ### Example:
    Input:
    "GS.TS Trần Văn Tỷ hiện đang công tác tại Trường Đại học Thủy lợi, chuyên ngành Kỹ thuật tài nguyên nước."
    
    Output:
    [
      {{"entity": "Trần Văn Tỷ", "type": "PERSON"}},
      {{"entity": "Trường Đại học Thủy lợi", "type": "UNIVERSITY"}},
      {{"entity": "Kỹ thuật tài nguyên nước", "type": "RESEARCH_FIELD"}},
      {{"entity": "GS.TS", "type": "ACADEMIC_TITLE"}}
    ]
    """

    context_template = f"""
    Extract all named entities from the following text and return them in JSON format.

    Text:
    \"\"\"{{context}}\"\"\"
    """
    
    import os
    
    from dotenv import load_dotenv
    
    load_dotenv()
    # print(text)
    
    config = [
        {
            "model_name": "gemini-2.5-flash",
            "API_KEY": os.environ["OPENAI"],
            "system_prompt": system_prompt,
            "context_template": context_template
        }, 
        {
            "model_name": "gemini-2.0-flash",
            "API_KEY": os.environ["OPENAI"],
            "system_prompt": system_prompt,
            "context_template": context_template
        },
        {
            "model_name": "gpt-3.5-turbo",
            "API_KEY": os.environ["OPENAI"],
            "system_prompt": system_prompt,
            "context_template": context_template
        }
        
    ]
    i: int = 0
    from KG_builder.utils.llm_utils import CostModel
    
    
    response: str = ""
    while i < len(config):
        try:    
            llm = CostModel(**config[i])
            response = llm.chat(
                text,
                True
            )
            break
        except Exception as e:
            i += 1
            logging.error(f"Message: {e}")
            # llm = CostModel(**config[i])
            
    # print("Hello")
    try:
        res = json.loads(response)
        
    except Exception as e:
        logging.error(f"JSON converted failed: {e}")
 
        
    
    return res
    
def read_csv(path: str) -> Tuple[str, Dict[str, str]]:
    import pandas as pd
    
    entities = pd.read_csv(path)
    
    ret = ""
    Entities: Dict[str, str] = {}
    
    for _, row in entities.iterrows():
        # print(row.values())
        ret += f"{row["Type"]}: {row["Definition"]}\n"
        
        
    return ret, Entities
        
    


if __name__ == "__main__":
    DATA_PATH = "/Users/huynhnguyen/WorkDir/bachoc_1/data/(16844277137145_29_06_2024_20_12)do-van-chien-1980-11-17-1719666757.txt"
    
    text = open(DATA_PATH, "r").read()
    # print(text)
    from KG_builder.utils.clean_data import clean_vn_text
    concated_senteces = corpuses(clean_vn_text(text))
    
    prompt_type, entities =  read_csv("/Users/huynhnguyen/WorkDir/bachoc_1/entities.csv")
    
    seen = set()
    
    final_result: List[Any] = []
    try:
        for i, sentence in enumerate(concated_senteces):
            print(f"Iterration: {i}")
            try:
                return_json = extract_entities(sentence, prompt_type)
                print("\t", return_json)
                
                for element in return_json:
                    entity = element["entity"]
                    entity_type = element["type"]
                    
                    if entity in seen:
                        continue
                    final_result.append(element)
                    
                    seen.add(entity)
            except Exception as e:
                logging.error(f"Message: {e}")
                break
            
        with open("new_sample_entities.json", "w", encoding="utf-8") as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Script crashed: {e}")
    finally:
        with open("recovery_final.json", "w", encoding="utf-8") as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)
    
    
    