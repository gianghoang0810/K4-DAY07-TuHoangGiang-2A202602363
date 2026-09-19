"""Run the UTSC Parent-child benchmark with Gemini embedding and generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv

from benchmark_parent_child import ParentChildRetriever, build_parent_child_corpus
from src import KnowledgeBaseAgent


QUERIES = [
    {
        "id": 1,
        "query": "What are the UTSC Library's regular opening hours from Monday to Friday between September 8 and December 22, 2026?",
        "gold": "The library's regular weekday hours are 8:00 AM to 10:00 PM. It is closed on October 12, 2026.",
        "doc_id": "utsc-library-hours",
        "evidence": "8:00 AM - 10:00 PM",
    },
    {
        "id": 2,
        "query": "As an undergraduate student, how long can I borrow regular library items, and what is my item limit?",
        "gold": "Undergraduate students have a regular loan period of 14 days and an item limit of 50.",
        "doc_id": "utsc-borrowing-policy",
        "evidence": "14 days",
    },
    {
        "id": 3,
        "query": "Where should a user return a borrowed laptop from the Technology Loans collection?",
        "gold": "A borrowed laptop should be returned directly to the Info Desk.",
        "doc_id": "utsc-technology-loans",
        "evidence": "returned directly to the Info Desk",
    },
    {
        "id": 4,
        "query": "A student needs to find a physical course reading placed on reserve. Where is it located?",
        "gold": "Physical course reserves are located 20 steps to the left of the InfoDesk at the UTSC Library.",
        "doc_id": "utsc-course-reserves",
        "evidence": "20 steps to the left of the InfoDesk",
    },
    {
        "id": 5,
        "query": "Which service provides a free and secure University of Toronto repository for disseminating and preserving faculty and graduate-student research?",
        "gold": "TSpace – University of Toronto Research Repository.",
        "doc_id": "utsc-research-publishing",
        "evidence": "TSpace is a free and secure research repository",
    },
]


class JsonCache:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.values: dict[str, object] = {}
        if path.exists():
            self.values = json.loads(path.read_text(encoding="utf-8"))

    def get(self, key: str):
        return self.values.get(key)

    def put(self, key: str, value: object) -> None:
        self.values[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.values, ensure_ascii=False), encoding="utf-8")


class BatchGeminiEmbedder:
    def __init__(self, model_name: str, cache: JsonCache) -> None:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is required")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.cache = cache
        self._backend_name = model_name

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def preload(self, texts: list[str], batch_size: int = 50) -> None:
        missing = [text for text in texts if self.cache.get(self._key(text)) is None]
        for start in range(0, len(missing), batch_size):
            batch = missing[start : start + batch_size]
            response = self.client.models.embed_content(model=self.model_name, contents=batch)
            embeddings = response.embeddings or []
            if len(embeddings) != len(batch):
                raise RuntimeError(
                    f"Gemini returned {len(embeddings)} embeddings for a batch of {len(batch)} texts"
                )
            for text, embedding in zip(batch, embeddings):
                self.cache.put(self._key(text), list(embedding.values))

    def __call__(self, text: str) -> list[float]:
        key = self._key(text)
        cached = self.cache.get(key)
        if cached is not None:
            return [float(value) for value in cached]
        raise RuntimeError("Embedding was not preloaded; call preload() before creating the store")


class GeminiLLM:
    def __init__(self, model_name: str, cache: JsonCache) -> None:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is required")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.cache = cache

    def __call__(self, prompt: str) -> str:
        key = hashlib.sha256((self.model_name + "\n" + prompt).encode("utf-8")).hexdigest()
        cached = self.cache.get(key)
        if isinstance(cached, str):
            return cached
        response = None
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name, contents=prompt
                )
                break
            except Exception as exc:  # retry transient 503/429 responses
                last_error = exc
                if attempt == 2 or not any(code in str(exc) for code in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED")):
                    raise
                time.sleep(5 * (attempt + 1))
        if response is None:
            raise RuntimeError("Gemini did not return a response") from last_error
        answer = (response.text or "").strip()
        self.cache.put(key, answer)
        return answer


class FilteredRetriever:
    def __init__(self, retriever: ParentChildRetriever, metadata_filter: dict[str, str]) -> None:
        self.retriever = retriever
        self.metadata_filter = metadata_filter

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        return self.retriever.search_with_filter(query, top_k=top_k, metadata_filter=self.metadata_filter)


def evaluate_query(item: dict, retriever, agent: KnowledgeBaseAgent) -> dict:
    results = retriever.search(item["query"], top_k=3)
    relevant = [
        result
        for result in results
        if result["metadata"].get("doc_id") == item["doc_id"]
        and item["evidence"].lower() in result["content"].lower()
    ]
    answer = agent.answer(item["query"], top_k=3)
    answer_grounded = item["evidence"].lower() in answer.lower()
    score = 2 if relevant and answer_grounded else 1 if relevant else 0
    return {
        "id": item["id"],
        "query": item["query"],
        "gold": item["gold"],
        "top3": [
            {
                "id": result["id"],
                "doc_id": result["metadata"].get("doc_id"),
                "parent_id": result["metadata"].get("parent_id"),
                "section": result["metadata"].get("section"),
                "score": result["score"],
                "contains_evidence": item["evidence"].lower() in result["content"].lower(),
            }
            for result in results
        ],
        "answer": answer,
        "relevant_in_top3": bool(relevant),
        "answer_contains_evidence": answer_grounded,
        "score": score,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/utsc-library-services"))
    parser.add_argument("--output", type=Path, default=Path("benchmark_results_gemini.json"))
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    if os.getenv("EMBEDDING_PROVIDER", "").strip().lower() != "gemini":
        raise SystemExit("Set EMBEDDING_PROVIDER=gemini in .env before running this benchmark")

    cache_dir = Path(".cache")
    embed_cache = JsonCache(cache_dir / "gemini_embeddings.json")
    answer_cache = JsonCache(cache_dir / "gemini_answers.json")
    if args.no_cache:
        embed_cache.values.clear()
        answer_cache.values.clear()

    corpus = build_parent_child_corpus(args.data_dir)
    embedder = BatchGeminiEmbedder(
        os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"), embed_cache
    )
    embedder.preload(
        [document.content for document in corpus.children]
        + [item["query"] for item in QUERIES]
    )
    retriever = ParentChildRetriever(corpus, embedding_fn=embedder)
    llm = GeminiLLM(os.getenv("GEMINI_CHAT_MODEL", "gemini-3.6-flash"), answer_cache)
    agent = KnowledgeBaseAgent(store=retriever, llm_fn=llm)

    results = [evaluate_query(item, retriever, agent) for item in QUERIES]
    filtered_retriever = FilteredRetriever(retriever, {"audience": "student"})
    filtered_agent = KnowledgeBaseAgent(store=filtered_retriever, llm_fn=llm)
    ab = {
        "unfiltered": evaluate_query(QUERIES[3], retriever, agent),
        "audience_student": evaluate_query(QUERIES[3], filtered_retriever, filtered_agent),
    }

    payload = {
        "embedding_backend": embedder._backend_name,
        "chat_model": llm.model_name,
        "parent_count": len(corpus.parents),
        "child_count": len(corpus.children),
        "results": results,
        "ab_test_query_4": ab,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Embedding backend: {payload['embedding_backend']}")
    print(f"Chat model: {payload['chat_model']}")
    print(f"Parents: {payload['parent_count']} | Children: {payload['child_count']}")
    print(f"Saved: {args.output}")
    print(f"Scores: {[result['score'] for result in results]}")
    print("A/B query 4:", {key: value["score"] for key, value in ab.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
