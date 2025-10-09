#!/usr/bin/env python3
"""Convert the semi-structured triples in canon_kg.txt into a SPARQL INSERT command.

Usage:
    python canon_to_sparql.py \
        --input ../canon_kg.txt \
        --output ../canon_kg_insert.rq \
        --graph http://duncan.org/graph/canon

If --output is omitted, the SPARQL command is printed to stdout.
"""

from __future__ import annotations

import argparse
import ast
import unicodedata
import re
from pathlib import Path
from typing import Iterable, Tuple, Set

PREFIX_LINES = [
    "PREFIX ex: <http://duncan.org/resource/>",
    "PREFIX prop: <http://duncan.org/property/>",
    "PREFIX wdt: <http://www.wikidata.org/prop/direct/>",
    "PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>",
]

PREDICATE_MAP = {
    "date of birth": "wdt:P569",
    "place of birth": "wdt:P19",
    "located in the administrative territorial entity": "wdt:P131",
    "country": "wdt:P17",
    "start time": "wdt:P580",
}

RESOURCE_PREDICATES = {
    "place of birth",
    "located in the administrative territorial entity",
    "country",
}

INPUT_ENCODING = "utf-8"


def slugify(text: str) -> str:
    """Create a safe identifier that can be used in CURIE local parts."""
    normalized = unicodedata.normalize("NFD", text)
    normalized = normalized.replace("đ", "d").replace("Đ", "D")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    if not cleaned:
        cleaned = "resource"
    if not cleaned[0].isalpha():
        cleaned = f"r_{cleaned}"
    return cleaned


def to_resource(name: str) -> str:
    return f"ex:{slugify(name)}"


def to_property(predicate: str) -> str:
    mapped = PREDICATE_MAP.get(predicate)
    if mapped:
        return mapped
    return f"prop:{slugify(predicate)}"


def is_numeric_string(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9]+", value))


def is_date(value: str) -> str | None:
    match = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", value)
    if match:
        day, month, year = match.groups()
        return f'"{year}-{month}-{day}"^^xsd:date'
    match = re.fullmatch(r"\d{4}", value)
    if match:
        return f'"{value}"^^xsd:gYear'
    return None


def escape_literal(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def should_use_resource(predicate: str, obj: str) -> bool:
    if predicate not in RESOURCE_PREDICATES:
        return False
    return any(ch.isalpha() for ch in obj)


def format_object(predicate: str, obj: str) -> str:
    date_literal = is_date(obj)
    if date_literal and predicate == "date of birth":
        return date_literal
    if should_use_resource(predicate, obj):
        return to_resource(obj)
    if date_literal:
        return date_literal
    if is_numeric_string(obj):
        return f'"{obj}"'
    return escape_literal(obj)


def load_triples(path: Path) -> Iterable[Tuple[str, str, str]]:
    for idx, line in enumerate(path.read_text(encoding=INPUT_ENCODING).splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped == "[]":
            continue
        try:
            entries = ast.literal_eval(stripped)
        except (SyntaxError, ValueError) as exc:
            raise ValueError(f"Cannot parse line {idx}: {stripped}") from exc
        for entry in entries:
            if len(entry) != 3:
                raise ValueError(f"Invalid triple at line {idx}: {entry}")
            subj, pred, obj = entry
            yield subj, pred, obj


def build_insert(triples: Iterable[Tuple[str, str, str]], graph_iri: str | None = None) -> str:
    formatted: Set[Tuple[str, str, str]] = set()
    for subj, pred, obj in triples:
        formatted.add((to_resource(subj), to_property(pred), format_object(pred, obj)))

    sorted_triples = sorted(formatted)
    lines = PREFIX_LINES + ["", "INSERT DATA {"]

    indent = "  "
    if graph_iri:
        lines.append(f"  GRAPH <{graph_iri}> {{")
        indent = "    "

    for subj, pred, obj in sorted_triples:
        lines.append(f"{indent}{subj} {pred} {obj} .")

    if graph_iri:
        lines.append("  }")

    lines.append("}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert canon_kg triples into a SPARQL INSERT command")
    parser.add_argument("--input", type=Path, default=Path("../canon_kg.txt"), help="Path to canon_kg.txt")
    parser.add_argument("--output", type=Path, help="Optional path to write the SPARQL command")
    parser.add_argument("--graph", help="Optional named graph IRI to target in the INSERT")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    triples = list(load_triples(args.input))
    if not triples:
        raise SystemExit(f"No triples found in {args.input}")

    sparql = build_insert(triples, args.graph)

    if args.output:
        args.output.write_text(sparql, encoding=INPUT_ENCODING)
    else:
        print(sparql)


if __name__ == "__main__":
    main()
