"""Chunking strategy to divide text file into main topics."""
from KG_builder.extract.extract_triples import extract_triples
from KG_builder.prompts.prompts import EXTRACT_TRIPLE_PERSONAL_INFO_PROMPT
from KG_builder.utils.llm_utils import load_model

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


with open("../data/(16844277137145_29_06_2024_20_12)do-van-chien-1980-11-17-1719666757.txt", "r", encoding="utf-8") as f:
    text = f.read()
    
start_keywords = ["THÔNG TIN CÁ NHÂN", "7. Quá trình công tác", "5. Biên soạn sách"]
end_keywords = ["7. Quá trình công tác", "B. TỰ KHAI THEO ", "9. Các tiêu chuẩn"]

paragraphs: list[dict[str, any]] = []
for i, (start_word, end_word) in enumerate(zip(start_keywords, end_keywords)):
    paragraph = extract_specific_sections(
        text=text,
        start_keyword=start_word,
        end_keyword=end_word
    )
    paragraphs.append(paragraph)

# Extract personal info
llm = load_model("gemini-2.0-flash")
response = extract_triples(
    context=paragraphs[0]["content"],
    llm=llm,
    **EXTRACT_TRIPLE_PERSONAL_INFO_PROMPT
)