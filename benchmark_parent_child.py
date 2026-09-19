"""Parent-child indexing for the UTSC benchmark.

The core lab classes remain unchanged: child Documents are embedded and
searched in an EmbeddingStore, while each result is expanded to its parent
section before it is passed to KnowledgeBaseAgent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bench import parse_frontmatter
from src import Document, EmbeddingStore, FixedSizeChunker, RecursiveChunker


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class ParentSection:
    parent_id: str
    doc_id: str
    section: str
    content: str
    metadata: dict[str, str]


@dataclass
class ParentChildCorpus:
    parents: dict[str, ParentSection]
    children: list[Document]


def _sections(content: str) -> list[tuple[str, str]]:
    """Split Markdown body into heading-led sections."""

    matches = list(HEADING_RE.finditer(content))
    if not matches:
        return [("Document", content.strip())] if content.strip() else []

    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        section_text = content[match.start() : end].strip()
        if section_text:
            sections.append((match.group(2).strip(), section_text))
    return sections


def _parent_parts(section_title: str, section_text: str, max_parent_chars: int) -> list[str]:
    if len(section_text) <= max_parent_chars:
        return [section_text]

    heading = section_text.splitlines()[0].strip()
    body = section_text[len(section_text.splitlines()[0]) :].strip()
    body_limit = max(1, max_parent_chars - len(heading) - 2)
    pieces = RecursiveChunker(chunk_size=body_limit).chunk(body)
    return [f"{heading}\n\n{piece}".strip() for piece in pieces if piece.strip()]


def build_parent_child_corpus(
    data_dir: Path,
    *,
    max_parent_chars: int = 800,
    child_chars: int = 250,
    child_overlap: int = 25,
) -> ParentChildCorpus:
    """Build parent sections and child Documents from cleaned corpus files."""

    if not 500 <= max_parent_chars <= 800:
        raise ValueError("max_parent_chars must be between 500 and 800")
    if not 200 <= child_chars <= 300:
        raise ValueError("child_chars must be between 200 and 300")
    if not 0 <= child_overlap < child_chars:
        raise ValueError("child_overlap must be smaller than child_chars")

    parents: dict[str, ParentSection] = {}
    children: list[Document] = []
    for path in sorted(data_dir.glob("*.md")):
        metadata, content = parse_frontmatter(path)
        doc_id = metadata["doc_id"]
        section_number = 0

        for section_title, section_text in _sections(content):
            for part in _parent_parts(section_title, section_text, max_parent_chars):
                parent_id = f"{doc_id}#parent-{section_number}"
                parent_metadata = {
                    **metadata,
                    "doc_id": doc_id,
                    "parent_id": parent_id,
                    "section": section_title,
                    "chunk_type": "parent",
                }
                parents[parent_id] = ParentSection(
                    parent_id=parent_id,
                    doc_id=doc_id,
                    section=section_title,
                    content=part,
                    metadata=parent_metadata,
                )

                first_line = part.splitlines()[0].strip() if part.splitlines() else section_title
                body = part[len(part.splitlines()[0]) :].strip() if part.splitlines() else part
                child_limit = max(1, child_chars - len(first_line) - 2)
                child_parts = FixedSizeChunker(
                    chunk_size=child_limit,
                    overlap=min(child_overlap, max(0, child_limit - 1)),
                ).chunk(body) or [body]
                for child_number, child_body in enumerate(child_parts):
                    child_content = f"{first_line}\n\n{child_body}".strip()
                    child_metadata = {
                        **metadata,
                        "doc_id": doc_id,
                        "parent_id": parent_id,
                        "section": section_title,
                        "chunk_type": "child",
                        "child_index": str(child_number),
                    }
                    children.append(
                        Document(
                            id=f"{parent_id}#child-{child_number}",
                            content=child_content,
                            metadata=child_metadata,
                        )
                    )
                section_number += 1

    return ParentChildCorpus(parents=parents, children=children)


class ParentChildRetriever:
    """Search child vectors and return their deduplicated parent sections."""

    def __init__(self, corpus: ParentChildCorpus, embedding_fn=None) -> None:
        self.corpus = corpus
        self.child_store = EmbeddingStore(
            collection_name="utsc-parent-child-children",
            embedding_fn=embedding_fn,
        )
        self.child_store.add_documents(corpus.children)

    def _expand(self, child_results: list[dict]) -> list[dict]:
        expanded: list[dict] = []
        seen: set[str] = set()
        for result in child_results:
            parent_id = result["metadata"].get("parent_id")
            if not parent_id or parent_id in seen or parent_id not in self.corpus.parents:
                continue
            parent = self.corpus.parents[parent_id]
            seen.add(parent_id)
            expanded.append(
                {
                    "id": parent.parent_id,
                    "content": parent.content,
                    "metadata": {
                        **parent.metadata,
                        "matched_child_id": result.get("id", ""),
                    },
                    "score": result["score"],
                }
            )
        return expanded

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        return self._expand(self.child_store.search(query, top_k=top_k * 2))[:top_k]

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict | None = None) -> list[dict]:
        return self._expand(
            self.child_store.search_with_filter(
                query, top_k=top_k * 2, metadata_filter=metadata_filter
            )
        )[:top_k]

    def get_collection_size(self) -> int:
        return self.child_store.get_collection_size()

    def delete_document(self, doc_id: str) -> bool:
        removed = self.child_store.delete_document(doc_id)
        for parent_id in list(self.corpus.parents):
            if self.corpus.parents[parent_id].doc_id == doc_id:
                del self.corpus.parents[parent_id]
        return removed
