#!/usr/bin/env python3
"""Retrieve top-k relevant review chunks from ChromaDB for a query."""

import re
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHROMA_DIR = "documents/chroma_db"
COLLECTION_NAME = "professor_reviews"
TOP_K = 5

# Maps name variants (lowercase) → canonical stored name
PROFESSOR_ALIASES: dict[str, str] = {
    "akther": "Sayma Akther", "sayma": "Sayma Akther",
    "attar": "Nada Attar", "nada": "Nada Attar",
    "austin": "Thomas Austin", "tom austin": "Thomas Austin",
    "potika": "Katerina Potika", "katerina": "Katerina Potika",
    "stamp": "Mark Stamp",
    "taylor": "David Taylor",
    "wood": "Mike Wood",
    "arabghalizi": "Tahereh Arabghalizi", "tahereh": "Tahereh Arabghalizi",
    "case": "Doug Case",
    "tsao": "Chung-Wen Tsao", "chung-wen": "Chung-Wen Tsao",
}

COURSE_RE = re.compile(r"\bcs\s*(\d+[a-z]*)\b", re.IGNORECASE)


def parse_filters(query: str) -> dict | None:
    """Detect professor names and course codes in query; return a ChromaDB where filter."""
    q = query.lower()

    seen = set()
    professors = []
    for alias in sorted(PROFESSOR_ALIASES, key=len, reverse=True):
        if alias in q:
            canonical = PROFESSOR_ALIASES[alias]
            if canonical not in seen:
                seen.add(canonical)
                professors.append(canonical)

    course = None
    m = COURSE_RE.search(query)
    if m:
        course = f"CS{m.group(1).upper()}"

    prof_filter = None
    if len(professors) == 1:
        prof_filter = {"professor_name": {"$eq": professors[0]}}
    elif len(professors) > 1:
        prof_filter = {"$or": [{"professor_name": {"$eq": p}} for p in professors]}

    if prof_filter and course:
        return {"$and": [prof_filter, {"course": {"$eq": course}}]}
    if prof_filter:
        return prof_filter
    if course:
        return {"course": {"$eq": course}}
    return None


def get_collection():
    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
    )


def retrieve(query: str, k: int = TOP_K, where: dict = None) -> list[dict]:
    """Return top-k chunks most similar to query.

    Auto-detects professor names and course codes in the query and applies
    a metadata filter unless where is explicitly provided.
    """
    collection = get_collection()
    if where is None:
        where = parse_filters(query)

    kwargs = {"query_texts": [query], "n_results": k, "include": ["documents", "metadatas", "distances"]}
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({"text": doc, "metadata": meta, "distance": dist})
    return chunks


def print_results(chunks: list[dict]) -> None:
    for i, chunk in enumerate(chunks, 1):
        m = chunk["metadata"]
        print(f"\n--- Result {i} (distance: {chunk['distance']:.4f}) ---")
        print(f"Professor: {m.get('professor_name')}  |  Course: {m.get('course')}  |  Date: {m.get('date')}")
        print(f"Quality: {m.get('quality_rating')}/5  |  Difficulty: {m.get('difficulty_rating')}/5  |  Grade: {m.get('grade')}")
        print(f"Would Take Again: {m.get('would_take_again')}  |  Tags: {m.get('tags')}")
        print(f"Review: {chunk['text']}")


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How difficult are the courses?"
    print(f"Query: {query}\n")
    results = retrieve(query)
    print_results(results)
