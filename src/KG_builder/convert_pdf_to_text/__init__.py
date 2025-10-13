"""Public API for the convert_pdf_to_text package."""

from .core import (
    DEFAULT_MODEL,
    build_context_with_provenance,
    clean_page_text,
    extract_context_from_pdf,
    extract_profile_from_context,
    extract_profile_from_pdf,
    get_pdf_pages,
    has_structured_extractor,
)
from .cli import main as cli_main

main = cli_main

__all__ = [
    "DEFAULT_MODEL",
    "build_context_with_provenance",
    "clean_page_text",
    "cli_main",
    "main",
    "extract_context_from_pdf",
    "extract_profile_from_context",
    "extract_profile_from_pdf",
    "get_pdf_pages",
    "has_structured_extractor",
]
