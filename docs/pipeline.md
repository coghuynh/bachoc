# Pipeline Overview

## luồng xử lý chính
- Người dùng truyền vào đường dẫn tệp văn bản (`data`).
- `run.py` đọc nội dung, gọi `clean_vn_text()` để chuẩn hóa rồi chia nhỏ văn bản bằng `chunk_corpus()` theo cấu hình.
- Khởi tạo `KnowledgeGraphBuilder` cùng các thành phần:
  - LLM trích xuất triple (async)
  - LLM định nghĩa predicate (async)
  - Mô hình embedding (Qwen mặc định, có thể đổi Gemini)
  - SQLite `kg.db` (EntitiesDAO, PredicatesDAO, TriplesDAO)
  - Chỉ mục embedding (NumPy storage cho entity/predicate)
- Với từng chunk, gọi `async_extract_triples()` để thu về danh sách `{subject, predicate, object}`.
- Gộp toàn bộ triple, loại bản sao và lọc trường thiếu.
- Chuẩn hóa predicate:
  - Thu thập danh sách predicate mới → gọi `async_collect_definition()` để sinh định nghĩa.
  - Embed định nghĩa (hoặc tên) → tìm láng giềng gần nhất trong index → tái sử dụng predicate cũ nếu cosine ≥ `threshold`, ngược lại tạo mới (DAO + index).
- Chuẩn hóa entity:
  - Embed subject/object → tìm trong entity index → reuse khi đạt ngưỡng, ngược lại upsert vào DB + cập nhật index.
- Mỗi triple được ánh xạ sang ID nội bộ (`entity_id`, `predicate_id`, `triple_id`) và ghi vào bảng `triples`.
- Ghi kết quả JSON (đường dẫn `--output-triples`); DB và index lưu trạng thái cho lần chạy tiếp theo.

## pseudo-code
```pseudo
load_dotenv()
args = parse_cli()

text = read_file(args.data)
cleaned = clean_vn_text(text)
chunks = chunk_corpus(cleaned, config)

builder = KnowledgeGraphBuilder(config)

triples_raw = []
for chunk in chunks:
    triples_raw += async_extract_triples(chunk, builder.extract_triples_model)

unique_triples = deduplicate(triples_raw)

predicate_names = collect_predicates(unique_triples)
predicate_map = builder.prepare_predicates(predicate_names)

entity_names = collect_entities(unique_triples)
entity_map = builder.prepare_entities(entity_names)

result = []
for triple in unique_triples:
    subj = triple.subject.strip()
    pred = triple.predicate.strip()
    obj = triple.object.strip()
    if not valid(subj, pred, obj): continue

    canonical_pred = predicate_map[pred]
    subject_id = entity_map[subj]
    object_id = entity_map[obj]
    predicate_id = hash_id("P", canonical_pred)
    triple_id = hash_id("T", subject_id, predicate_id, object_id)

    builder.triples_dao.upsert(triple_id, subject_id, predicate_id, object_id)

    result.append({
        "subject": subj, "subject_id": subject_id,
        "predicate": canonical_pred, "predicate_id": predicate_id,
        "object": obj, "object_id": object_id
    })

write_json(args.output_triples, result)
```

### hàm hỗ trợ chính
```pseudo
prepare_predicates(names):
    unseen = names - known_relations
    if unseen:
        definitions = async_collect_definition(unseen)
        for name in unseen:
            definition = definitions.get(name)
            canonical = upsert_predicate(name, definition)
            mapping[name] = canonical
    return mapping

upsert_predicate(name, definition):
    vector = embed(definition or name)
    normalized = normalize(vector)
    if predicate_index.has_items():
        candidate_id, dist = nearest_search(normalized)
        if similarity(candidate_id, normalized) >= threshold:
            return existing_predicate_name(candidate_id)
    predicate_id = hash_id("P", name)
    predicate_manager.upsert(predicate_id, name, definition or name, normalized)
    relations_schema[name] = definition or name
    return name

prepare_entities(names):
    vectors = embed(names)
    mapping = {}
    for name, vector in zip(names, vectors):
        mapping[name] = match_or_create_entity(name, vector)
    return mapping

match_or_create_entity(name, vector):
    normalized = normalize(vector)
    if entity_index.has_items():
        candidate_id, dist = nearest_search(normalized)
        if similarity(candidate_id, normalized) >= threshold:
            return candidate_id
    entity_id = hash_id("E", name)
    entity_manager.upsert(entity_id, name, description=name, source="extracted", embedding=normalized)
    return entity_id
```

## ghi chú
- DAO quản lý SQLite (`entities`, `predicates`, `triples`, và bảng map embedding ↔ id).
- Embedding index sử dụng NumPy lưu `.index`, hỗ trợ `add`, `upsert`, `search`, `remove` (HNSW đã được thay thế). 
- `QwenEmbedding` là mặc định, tránh phụ thuộc quota; vẫn hỗ trợ Gemini nếu cấu hình.
- Chạy pipeline: `python src/run.py path/to/text.txt --output-triples out.json`.
- `kg.db` và các file `data/*.index` được cập nhật sau mỗi lần chạy, không cần schema CSV.

