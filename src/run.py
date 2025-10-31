from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

from dotenv import load_dotenv

from KG_builder.builder import KnowledgeGraphBuilder
from KG_builder.utils.clean_data import clean_vn_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract knowledge graph triples from a text file."
    )
    parser.add_argument("data", type=Path, help="Path to the input text file.")

    parser.add_argument("--entities-schema", type=Path, default=Path("entities.csv"))
    parser.add_argument("--relation-schema", type=Path, default=Path("relationships.csv"))
    parser.add_argument("--triples-model", default="gemini-2.0-flash")
    parser.add_argument("--definition-model", default="gemini-2.0-flash")
    parser.add_argument("--embedding-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument(
        "--embedding-rpm",
        type=int,
        default=None,
        help="Maximum embedding requests per minute (optional rate limit).",
    )

    parser.add_argument("--threshold", type=float, default=0.7)
    parser.add_argument("--db-path", type=Path, default=Path("kg.db"))
    parser.add_argument("--entity-index", type=Path, default=Path("data/entity.index"))
    parser.add_argument("--predicate-index", type=Path, default=Path("data/predicate.index"))

    parser.add_argument("--max-chunk-chars", type=int, default=4800)
    parser.add_argument("--min-chunk-chars", type=int, default=1200)
    parser.add_argument("--sentence-overlap", type=int, default=1)

    parser.add_argument("--output-triples", type=Path, default=Path("triples.json"))
    parser.add_argument(
        "--output-schema",
        type=Path,
        default=None,
        help="Optional path to persist the updated relation schema.",
    )

    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    if not args.data.exists():
        raise FileNotFoundError(f"Input file not found: {args.data}")

    text = args.data.read_text(encoding="utf-8")
    cleaned = clean_vn_text(text)

    builder_config = {
        "entities_schema": str(args.entities_schema),
        "relation_schema": str(args.relation_schema),
        "triples_model": args.triples_model,
        "definition_model": args.definition_model,
        "embedding_model": args.embedding_model,
        "embedding_rpm": args.embedding_rpm,
        "threshold": args.threshold,
        "db_path": str(args.db_path),
        "entity_index_path": str(args.entity_index),
        "predicate_index_path": str(args.predicate_index),
    }

    chunk_config = {
        "max_chunk_chars": args.max_chunk_chars,
        "min_chunk_chars": args.min_chunk_chars,
        "sentence_overlap": args.sentence_overlap,
    }

    builder = KnowledgeGraphBuilder(**builder_config)

    start = perf_counter()
    triples = builder.run(cleaned, chunk_config)
    elapsed = perf_counter() - start

    args.output_triples.parent.mkdir(parents=True, exist_ok=True)
    with args.output_triples.open("a", encoding="utf-8") as fh:
        json.dump(triples, fh, ensure_ascii=False, indent=2)

    if args.output_schema:
        args.output_schema.parent.mkdir(parents=True, exist_ok=True)
        builder.write_schema(str(args.output_schema))

    print(f"Extracted {len(triples)} triples in {elapsed:.2f}s; saved to {args.output_triples}")


if __name__ == "__main__":
    main()
