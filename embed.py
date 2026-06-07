#!/usr/bin/env python3
"""Embed chunks with all-MiniLM-L6-v2 and store in ChromaDB."""

import json
from pathlib import Path
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CHUNKS_FILE = Path("documents/chunks.json")
CHROMA_DIR = "documents/chroma_db"
COLLECTION_NAME = "professor_reviews"
BATCH_SIZE = 100


def main():
    with open(CHUNKS_FILE) as f:
        chunks = json.load(f)

    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Drop and recreate so re-runs are idempotent
    client.delete_collection(COLLECTION_NAME) if COLLECTION_NAME in [
        c.name for c in client.list_collections()
    ] else None
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # Sanitize metadata: ChromaDB requires str/int/float/bool values only
    def clean_meta(meta: dict) -> dict:
        return {
            k: (v if isinstance(v, (str, int, float, bool)) else str(v))
            for k, v in meta.items()
            if v is not None
        }

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        prof_id = chunk["metadata"]["professor_id"]
        ids.append(f"{prof_id}_{i}")
        documents.append(chunk["text"])
        metadatas.append(clean_meta(chunk["metadata"]))

    # Batch insert
    for start in range(0, len(ids), BATCH_SIZE):
        end = start + BATCH_SIZE
        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"  Embedded {min(end, len(ids))}/{len(ids)} chunks...")

    print(f"\nDone. {collection.count()} chunks stored in '{COLLECTION_NAME}'.")


if __name__ == "__main__":
    main()
