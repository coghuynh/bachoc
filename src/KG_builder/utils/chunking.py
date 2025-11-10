"""Chunking strategy to divide text file into main topics."""
from KG_builder.extract.extract_triples import extract_triples
from KG_builder.prompts.prompts import (
    EXTRACT_TRIPLE_PERSONAL_INFO_PROMPT,
    EXTRACT_TRIPLE_PERSONAL_INFO_USER_PROMPT,
    EXTRACT_TRIPLE_WORKING_INFO_PROMPT,
    EXTRACT_TRIPLE_WORKING_INFO_USER_PROMPT
)
from KG_builder.utils.llm_utils import load_model
from KG_builder.utils.clean_data import clean_vn_text
from KG_builder.triple_models import TripleList
import re
import json

def extract_specific_sections(
    text: str,
    start_keyword: str,
    end_keyword: str
) -> dict[str, any]:
    """Extract paragraph start with start_keyword and end before end_keyword"""
    lines = text.split("\n")
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        has_start = start_keyword.lower() in line.lower()
        
        if has_start:
            # Start to extract paragraph
            section_lines = [line]
            section_start_idx = i
            i += 1
            
            found_end = False
            while i < len(lines):
                current_line = lines[i]
                
                # Check end_keyword
                has_end = end_keyword.lower() in current_line.lower()
                
                if has_end:
                    found_end = True
                    break
                
                section_lines.append(current_line)
                i += 1
            
            # Lưu section nếu tìm thấy end hoặc hết file
            section = {
                'content': '\n'.join(section_lines),
                'start_line': section_start_idx,
                'end_line': i - 1,
                'has_end_marker': found_end,
                'start_keyword': start_keyword,
                'end_keyword': end_keyword if found_end else None
            }
        else:
            i += 1
    return section


def chunk_table_sections(data: dict[str, any]):
    """
    Chunk dictionary table data into 6 chunks:
    - 1 chunk for (projects, books, patents, training programs)
    - 5 chunks for papers
    """
    chunks = []
    summary_chunk = {}
    
    for key in ["projects", "books", "patents", "achievements", "training_programs"]:
        if data.get(key) is not None:
            summary_chunk[key] = data[key]
    
    if summary_chunk:
        chunks.append(summary_chunk)
        
    papers_list = data.get("papers", [])
    n_papers = len(papers_list)
    chunk_size = 10
    
    for i in range(0, n_papers, chunk_size):
        paper_chunk = {
            "papers": papers_list[i: i + chunk_size]
        }
        chunks.append(paper_chunk)
        
    return chunks


def save_chunks_to_json(chunks: list[dict[str, any]]):
    for i, chunk in enumerate(chunks):
        if i == 0: # summary chunk
            filename = f"summary_chunk.json"
        else:
            filename = f"chunk_{i}_papers.json"
            
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving file {filename}: {e}")
            
            
    
    
if __name__ == "__main__":
    # Generate model and response format for structured output
    llm = load_model("gemini-2.0-flash")
    response_format = {
        "type": "json_object",
        "response_mime_type": "application/json",
        "response_schema": TripleList
    }
    
    #TODO: read text file -> clean text -> split_into main_chunks -> extract triples from chunks
    
    with open("../data/(16844277137145_29_06_2024_20_12)do-van-chien-1980-11-17-1719666757.txt", "r", encoding="utf-8") as f:
        text = f.read()
    
    cleaned_text = clean_vn_text(text)
    
    section_boundaries = [
        ("THÔNG TIN CÁ NHÂN", "7. Quá trình công tác"),
        ("7. Quá trình công tác", "B. TỰ KHAI THEO")
    ]
    
    section_prompts = [
        (EXTRACT_TRIPLE_PERSONAL_INFO_PROMPT, EXTRACT_TRIPLE_PERSONAL_INFO_USER_PROMPT),
        (EXTRACT_TRIPLE_WORKING_INFO_PROMPT, EXTRACT_TRIPLE_WORKING_INFO_USER_PROMPT)
    ]
    
    main_subject = None
    
    for i, ((start_keyword, end_keyword), (system_instruction, context)) in enumerate(zip(section_boundaries, section_prompts)):
        # Get specific main section to extract triples.
        section = extract_specific_sections(
            text=text,
            start_keyword=start_keyword,
            end_keyword=end_keyword
        )
        
        context_kwargs = {"context": section}
        if main_subject:
            context_kwargs["main_subject"] = main_subject

        messages = {
            "system_instruction": system_instruction.format(),
            "context": context.format(**context_kwargs)
        }
        
        response = extract_triples(
            messages=messages,
            llm=llm,
            response_format=response_format
        )
        with open(f"test_triple_section_{i + 1}.json", "w", encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
        
        if i == 0:
            main_subject = response.get("triples")[0]["subject"]["name"]

# with open("D:/fico/DỰ_ÁN\src/table_data_1.json", 'r', encoding='utf-8') as f:
#     extracted_data = json.load(f)

# chunks = chunk_table_sections(extracted_data)
# save_chunks_to_json(chunks)