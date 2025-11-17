import json
import time
from pathlib import Path
from KG_builder.llm.base.base_model import BaseLLM
from KG_builder.triple_models import TripleList
from KG_builder.utils.llm_utils import load_model
from KG_builder.utils.clean_data import clean_vn_text
from KG_builder.config import SECTIONS_DEFINITION
from KG_builder.utils.chunking import extract_specific_sections

class Stage:
    def __init__(
        self,
        text: str,
        llm: BaseLLM,
        predicates: dict[str, list[str]],
        response_format: dict[str, any],
        context: str, 
        system_instruction: str,
        main_subject: str | None = None,
    ):
        self.text = text
        self.llm = llm
        self.predicates = predicates
        self.context = context
        self.system_instruction = system_instruction
        self.main_subject = main_subject
        self.response_format = response_format
        
        
    def build_message(self):
        if not self.main_subject:
            self.main_subject = ""
            
        messages = [
            {"role": "user", "content": self.context.format(
                main_subject=self.main_subject,
                predicates=self.predicates,
                text=self.text
            )},
            {"role": "system", "content": self.system_instruction}
        ]
        return messages
    
    
    def extract_triples(self):
        messages = self.build_message()
        response = self.llm.generate_response(messages, response_format=self.response_format)
        return json.loads(response)
    

class TripleExtraction:
    def __init__(self):
        self.stages: list[Stage] = []
        

    def add_stage(self, stage: Stage):
        self.stages.append(stage)
        
    
    def run(self, output_path: str | None = None):
        results = []
        current_main_subject = None
        
        for stage in self.stages:
            if current_main_subject:
                stage.main_subject = current_main_subject
                
            result = stage.extract_triples()
            
            if result.get("main_subject"):
                current_main_subject = result.get("main_subject")
            results.append(result)
    
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "main_subject": current_main_subject,
                    "stages": results
                }, f, ensure_ascii=False, indent=2)
            
        return results
    

if __name__ == "__main__":
    llm = load_model("gemini-2.0-flash")
    with open("./data/(17193813255334_29_06_2024_21_44)nguyen-thi-khanh-van-1969-09-02-1719672266.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    cleaned_text = clean_vn_text(text)
    
    response_format = {
        "type": "json_object",
        "response_mime_type": "application/json",
        "response_schema": TripleList
    }
    
    builder = TripleExtraction()
    
    for section in SECTIONS_DEFINITION:
        section_text = extract_specific_sections(text, section["start_word"], section["end_word"])
        print(section_text)
        builder.add_stage(
            stage=Stage(
                text=section_text,
                llm=llm,
                predicates=section["predicates"],
                response_format=response_format,
                context=section["context"],
                system_instruction=section["system_instruction"]
            )
        )
    
    # output_file = "./output/triples_4.json"
    
    # start = time.perf_counter()
    
    # results = builder.run(output_path=output_file)
    
    # end = time.perf_counter()
    # run_time = end - start
    # print(f"Triples extraction completes in {run_time}")
    # print(f"Saved to: ", output_file)