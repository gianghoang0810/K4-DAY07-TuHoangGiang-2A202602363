import math
from src.chunking import compute_similarity
from bench_gemini import BatchGeminiEmbedder, JsonCache
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
cache = JsonCache(Path(".cache/gemini_embeddings.json"))
embedder = BatchGeminiEmbedder(os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004") if not os.getenv("GEMINI_EMBEDDING_MODEL") else os.getenv("GEMINI_EMBEDDING_MODEL"), cache)

pairs = [
    ("What time does the library open on weekdays?", "When are the library's regular Monday-to-Friday opening hours?"),
    ("Where can a student find physical course reserves?", "Where are course readings placed on reserve located?"),
    ("Where should I return a borrowed laptop?", "Large electronic devices must be returned to the Info Desk."),
    ("What is the item limit for undergraduate students?", "Which repository preserves University of Toronto research?"),
    ("What are the library's borrowing rules?", "What is the weather forecast for tomorrow?")
]

texts = [text for pair in pairs for text in pair]
embedder.preload(texts)

for i, (a, b) in enumerate(pairs, 1):
    vec_a = embedder(a)
    vec_b = embedder(b)
    sim = compute_similarity(vec_a, vec_b)
    print(f"Pair {i}: {sim:.4f}")
