
from typing import Tuple, Dict, List
import re

def clean_vn_text(text: str) -> str:
    # Chuẩn hóa xuống dòng
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 1) Xóa tag [PAGE ...]
    text = re.sub(r"\[PAGE\s*\d+\]\s*\n?", "", text, flags=re.IGNORECASE)

    # 2) Bỏ header lặp lại ở đầu trang (tuỳ biến pattern cho tài liệu của bạn)
    text = re.sub(
        r"(?:^|\n)\s*Ban hành kèm theo Công văn số:[^\n]*\n",
        "\n",
        text,
        flags=re.IGNORECASE
    )

    # 3) Loại ký tự lỗi/thay thế, gom dấu chấm/ba chấm
    text = text.replace("\ufeff", "").replace("�", "").replace("", "")
    text = re.sub(r"[…\.]{3,}", "…", text)

    # 4) Tạm “gắn thẻ” list/bullet để không bị gộp sai
    def tag_bullets(line):
        import re
        if re.match(r"\s*[-•]\s+", line):
            return "<KEEP_LI>" + re.sub(r"^\s*", "", line)
        if re.match(r"\s*\d+\.\s+", line):            # 1. 2. 3.
            return "<KEEP_NUM>" + re.sub(r"^\s*", "", line)
        if re.match(r"\s*[IVXLC]+\.\s+", line):       # I. II. III.
            return "<KEEP_ROMAN>" + re.sub(r"^\s*", "", line)
        return line

    lines = [tag_bullets(l) for l in text.split("\n")]

    # 5) Gộp các dòng bị “wrap mềm” thành câu
    end_punct = "…!?。．.!?:;”’\"»）)]}›"
    joined = []
    for line in lines:
        if not line.strip():
            joined.append("")
            continue
        if not joined:
            joined.append(line.strip())
            continue

        prev = joined[-1]
        prev_ends = prev[-1] if prev else ""
        # Heuristic: nếu dòng trước không kết thúc bằng dấu câu
        # và dòng sau bắt đầu bằng chữ thường/dấu, ta gộp.
        starts_lower = bool(re.match(
            r"^[^\w]*[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\-\,\.;:()\"“”‘’\[]",
            line.lower()
        ))
        is_table_row = bool(re.match(r"^\s*(TT|ISBN|ISSN|Tr\.)\b", line))
        is_list_tagged = line.startswith(("<KEEP_LI>", "<KEEP_NUM>", "<KEEP_ROMAN>"))

        if (prev and prev_ends not in end_punct) and starts_lower and not is_table_row and not is_list_tagged:
            joined[-1] = prev + " " + line.strip()
        else:
            joined.append(line.strip())

    text = "\n".join(joined)

    # 6) Khôi phục bullet/list
    text = text.replace("<KEEP_LI>", "- ").replace("<KEEP_NUM>", "").replace("<KEEP_ROMAN>", "")

    # 7) Chuẩn hoá khoảng trắng quanh dấu câu
    text = re.sub(r"\s+([,;:\.\)\]\}»”’])", r"\1", text)
    text = re.sub(r"([\(“‘\[\{«])\s+", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text)

    # 8) (Tuỳ chọn) Xuống dòng sau dấu kết câu nếu theo sau là chữ hoa
    text = re.sub(
        r"([\.!?…])\s+(?=[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ])",
        r"\1\n",
        text
    )

    # 9) Vá URL bị tách: xoá khoảng trắng bên trong chuỗi bắt đầu bằng http(s)://
    def _fix_url(m):
        return re.sub(r"\s+", "", m.group(0))
    text = re.sub(r"https?://[^\s]+(?:\s+[^\s]+)+", _fix_url, text)

    return text.strip()


def chunk_corpus(
    text: str,
    *,
    max_chunk_chars: int = 1200,
    min_chunk_chars: int = 400,
    sentence_overlap: int = 1,
) -> List[str]:
    """
    Split a cleaned corpus into overlapping chunks that keep nearby sentences together.

    Parameters
    ----------
    text: str
        Input corpus after cleaning.
    max_chunk_chars: int
        Upper bound for each chunk length (in characters).
    min_chunk_chars: int
        Preferred minimum size for a chunk; shortened automatically for short texts.
    sentence_overlap: int
        Number of sentences to reuse at the beginning of the next chunk to keep context.
    """
    if max_chunk_chars <= 0:
        raise ValueError("max_chunk_chars must be positive.")
    if sentence_overlap < 0:
        raise ValueError("sentence_overlap must be non-negative.")

    if min_chunk_chars <= 0 or min_chunk_chars > max_chunk_chars:
        min_chunk_chars = max_chunk_chars // 2

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[\.!?…])\s+", text)
        if sentence.strip()
    ]

    if not sentences:
        sentences = [segment.strip() for segment in text.split("\n") if segment.strip()]

    if not sentences:
        return []

    chunks: List[str] = []
    start_idx = 0
    total_sentences = len(sentences)

    while start_idx < total_sentences:
        end_idx = start_idx
        current_chunk: List[str] = []
        current_len = 0

        while end_idx < total_sentences:
            sentence = sentences[end_idx]
            sentence_len = len(sentence)

            if current_chunk and current_len + sentence_len + 1 > max_chunk_chars:
                break

            if not current_chunk and sentence_len > max_chunk_chars:
                current_chunk.append(sentence)
                end_idx += 1
                break

            current_chunk.append(sentence)
            current_len += sentence_len + 1
            end_idx += 1

            if current_len >= min_chunk_chars:
                next_sentence_len = len(sentences[end_idx]) if end_idx < total_sentences else 0
                if current_len + next_sentence_len + 1 > max_chunk_chars:
                    break

        if not current_chunk:
            current_chunk.append(sentences[start_idx])
            end_idx = start_idx + 1

        chunk_text = " ".join(current_chunk).strip()
        if chunk_text:
            chunks.append(chunk_text)

        if end_idx >= total_sentences:
            break

        overlap = min(sentence_overlap, len(current_chunk))
        next_start = end_idx - overlap
        if next_start <= start_idx:
            next_start = end_idx
        start_idx = next_start

    return chunks


def write_schema(schema: Dict[str, str], path: str):
    import pandas as pd
    
    df_schema = pd.DataFrame({
        "Type" : [key for key, value in schema.items()],
        "Definition" : [value for key, value in schema.items()]
    })
    
    df_schema.to_csv(path)
    

def read_schema(path: str) -> Tuple[str, Dict[str, str]]:
    import pandas as pd
    
    entities = pd.read_csv(path)
    
    ret = ""
    Entities: Dict[str, str] = {}
    
    for _, row in entities.iterrows():
        # print(row.values())
        ret += f"{row["Type"]}: {row["Definition"]}\n"
        Entities[row["Type"]] = row["Definition"]
        
        
    return Entities


def read_json(path: str) -> List[Dict[str, str]]:
    import json
    with open(path, "r") as f:
        data = json.load(f)
        
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        raise ValueError("Expected JSON to be a list of objects")

    data = [{k: str(v) for k, v in d.items()} for d in data if isinstance(d, dict)]
    
    return data
