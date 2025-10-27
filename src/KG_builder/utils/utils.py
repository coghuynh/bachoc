import hashlib

def hash_id(prefix: str, *fields: str) -> str:
    data = "|".join(fields).encode("utf-8")
    digest = hashlib.sha1(data).hexdigest()[:12]
    return f"{prefix}_{digest}"