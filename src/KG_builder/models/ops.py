
from KG_builder.models.db_engine import Fact, Subject, Predicate


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance
    
    
def add_triple_data(session, triple_data: dict):
    """
    Xử lý một dictionary 'triple' duy nhất và thêm nó vào CSDL.
    Hàm này sử dụng get_or_create để xử lý Subject và Predicate.
    """
    # print(triple_data["subject"])
    try:
        # 1. Trích xuất thông tin
        subject_name = triple_data['subject']
        predicate_name = triple_data['predicate']
        object_value = triple_data['object']
        metadata = triple_data.get('metadata', {})

        # 2. Lấy hoặc tạo Subject và Predicate
        # Đây là phần "ma thuật" của ORM, không cần viết SQL
        subject_obj = get_or_create(session, Subject, name=subject_name)
        predicate_obj = get_or_create(session, Predicate, name=predicate_name)

        # 3. (Tùy chọn) Kiểm tra xem Fact này đã tồn tại chính xác chưa
        # Điều này ngăn chặn việc chạy lại script sẽ tạo ra các bản ghi trùng lặp
        existing_fact = session.query(Fact).filter_by(
            subject=subject_obj,
            predicate=predicate_obj,
            object_value=object_value,
            page=metadata.get('page')
        ).first()

        if existing_fact:
            # print(f"Bỏ qua (đã tồn tại): {subject_name} | {predicate_name}")
            return # Đã tồn tại, không làm gì cả

        # 4. Tạo đối tượng Fact mới
        new_fact = Fact(
            subject=subject_obj,
            predicate=predicate_obj,
            object_value=object_value,
            page=metadata.get('page'),
            confidence=metadata.get('confidence'),
            source=metadata.get('source')
        )

        # 5. Thêm Fact mới vào session
        session.add(new_fact)
        # print(f"Đã thêm: {subject_name} | {predicate_name}")

    except Exception as e:
        print(f"Lỗi khi xử lý triple {triple_data}: {e}")
        raise # Ném lỗi ra ngoài để rollback
