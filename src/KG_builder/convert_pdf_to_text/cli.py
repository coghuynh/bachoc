"""Command-line interface for the convert_pdf_to_text package."""

from __future__ import annotations

import argparse
import json
import os
from typing import Iterable, Optional

from . import core


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PDF → cleaned text or JSON (AcademicProfile)."
    )
    parser.add_argument("pdf_path", help="Path to PDF")
    parser.add_argument(
        "--mode",
        choices=["text", "json"],
        default="text",
        help="text: print cleaned text; json: run extractor and print JSON",
    )
    parser.add_argument(
        "--model",
        default=core.DEFAULT_MODEL,
        help="OpenAI model (json-structured)",
    )
    parser.add_argument(
        "--no-strip-headers",
        action="store_true",
        help="Do not remove headers/footers",
    )
    parser.add_argument(
        "--no-join",
        action="store_true",
        help="Do not join soft-wrapped lines",
    )
    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Do not dedup consecutive lines",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=0,
        help="If >0, truncate context to this many characters (safe cost cap)",
    )
    parser.add_argument(
        "--doc-id",
        default=None,
        help="Provenance doc_id to hint the model (e.g., pdf:TLU-2020-PGS-01)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate JSON against schema (requires jsonschema)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = _parse_args(argv)

    if not os.path.exists(args.pdf_path):
        raise SystemExit(f"File not found: {args.pdf_path}")

    pages = core.get_pdf_pages(args.pdf_path)
    built = core.build_context_with_provenance(
        pages,
        strip_headers=not args.no_strip_headers,
        join_lines=not args.no_join,
        dedup_consecutive=not args.no_dedup,
    )

    context = built["context"]
    if args.max_chars and args.max_chars > 0:
        context = context[: args.max_chars]

    if args.mode == "text" or not core.has_structured_extractor():
        print(context)
        if args.mode == "json" and not core.has_structured_extractor():
            print(
                "\n[WARN] kb_profile_extractor not installed. Showing text only.",
                flush=True,
            )
        return

    profile = core.extract_profile_from_context(
        context,
        model=args.model,
        validate_schema=args.validate,
        doc_id=args.doc_id,
    )

    print(json.dumps(profile, ensure_ascii=False, indent=2))


__all__ = ["main"]
