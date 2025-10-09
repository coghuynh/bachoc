import os 

from convert_pdf_to_text import extract_context_from_pdf
from dotenv import load_dotenv
import json

load_dotenv()
directory = "/Users/huynhnguyen/WorkDir/bachoc_1/data"
text_directory = "/Users/huynhnguyen/WorkDir/bachoc_1/text_data"

files = os.listdir(directory)

text_data = []

for file in files:
    try:
        resp = extract_context_from_pdf(os.path.join(directory, file))
    except Exception as e:
        print(f"Error: {e}")
    output = os.path.splitext(file)[0] + ".txt"
    with open(os.path.join(text_directory, output), "w") as f:
        f.write(resp)
    print(f"--- {file}: \n {resp}")
    
# print(len(json_data))


# with open("sample_data.json", "w", encoding="utf-8") as f:
#     json.dump(json_data, f, ensure_ascii=False, indent=4)