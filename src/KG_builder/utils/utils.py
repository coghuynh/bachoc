import hashlib
import inspect
from functools import wraps
import time

def hash_id(prefix: str, *fields: str) -> str:
    data = "|".join(fields).encode("utf-8")
    digest = hashlib.sha1(data).hexdigest()[:12]
    return f"{prefix}_{digest}"

def perf(func):
    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                print(f"{func.__name__} took {elapsed:.6f}s")
        return wrapper
    else:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                print(f"{func.__name__} took {elapsed:.6f}s")
        return wrapper