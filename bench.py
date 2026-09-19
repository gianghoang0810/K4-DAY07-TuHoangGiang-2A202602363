"""Validate and inspect the UTSC library corpus before benchmarking.

This first-stage runner deliberately does not call an embedding or LLM API.
It validates the cleaned Markdown files, their frontmatter, and sources.csv so
that later benchmark failures can be separated from ingestion problems.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path


REQUIRED_METADATA = (
    "doc_id",
    "title",
    "source_url",
    "retrieved_at",
    "document_version",
    "audience",
)


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    """Return simple YAML frontmatter and the Markdown body.

    The corpus uses one scalar value per line, so a small parser is sufficient
    and avoids adding a YAML dependency to the core lab requirements.
    """

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("missing opening frontmatter delimiter")

    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError("missing closing frontmatter delimiter")

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*?)\s*$", line)
        if not match:
            continue
        value = match.group(2).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        metadata[match.group(1)] = value

    return metadata, parts[2].lstrip("\r\n")


def validate_corpus(data_dir: Path) -> tuple[list[dict[str, object]], list[str]]:
    errors: list[str] = []
    rows: list[dict[str, object]] = []
    markdown_files = sorted(data_dir.glob("*.md"))

    if not markdown_files:
        errors.append(f"no Markdown files found in {data_dir}")

    if not 5 <= len(markdown_files) <= 10:
        errors.append(f"expected 5-10 Markdown files, found {len(markdown_files)}")

    audiences: Counter[str] = Counter()
    for path in markdown_files:
        try:
            metadata, content = parse_frontmatter(path)
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue

        missing = [key for key in REQUIRED_METADATA if not metadata.get(key)]
        if missing:
            errors.append(f"{path.name}: missing metadata: {', '.join(missing)}")
        if metadata.get("doc_id") != path.stem:
            errors.append(
                f"{path.name}: doc_id={metadata.get('doc_id')!r} does not match file stem"
            )
        if not content.strip():
            errors.append(f"{path.name}: Markdown body is empty")

        audience = metadata.get("audience", "")
        audiences[audience] += 1
        rows.append(
            {
                "file": path.name,
                "doc_id": metadata.get("doc_id", ""),
                "title": metadata.get("title", ""),
                "audience": audience,
                "category": metadata.get("category", ""),
                "characters": len(content),
            }
        )

    sources_path = data_dir / "sources.csv"
    source_ids: set[str] = set()
    if not sources_path.exists():
        errors.append("sources.csv is missing")
    else:
        with sources_path.open(encoding="utf-8", newline="") as handle:
            source_rows = list(csv.DictReader(handle))
        source_ids = {row.get("doc_id", "") for row in source_rows}
        file_ids = {str(row["doc_id"]) for row in rows}
        if source_ids != file_ids or len(source_rows) != len(rows):
            errors.append("sources.csv doc_id rows do not match Markdown files")
        for row in source_rows:
            file_path = row.get("file_path", "")
            if file_path:
                resolved = Path(file_path.replace("\\", "/"))
                if not resolved.is_absolute() and not (Path.cwd() / resolved).exists():
                    errors.append(f"sources.csv missing file_path target: {file_path}")

    if len([audience for audience in audiences if audience]) < 2:
        errors.append("audience must contain at least two distinct values")

    return rows, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/utsc-library-services"),
        help="directory containing cleaned Markdown files and sources.csv",
    )
    args = parser.parse_args()

    rows, errors = validate_corpus(args.data_dir)
    print(f"Corpus: {args.data_dir}")
    print(f"Documents found: {len(rows)}")
    print()
    for row in rows:
        print(
            f"- {row['file']}: {row['characters']} chars | "
            f"audience={row['audience']} | category={row['category']} | OK"
        )

    audiences = Counter(str(row["audience"]) for row in rows)
    print(f"Audience distribution: {dict(sorted(audiences.items()))}")
    if errors:
        print("\nVALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nVALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
