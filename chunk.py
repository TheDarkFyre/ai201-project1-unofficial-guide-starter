#!/usr/bin/env python3
"""Chunk RMP review data for ingestion into ChromaDB."""

import json
from pathlib import Path
from transformers import AutoTokenizer

CHUNK_SIZE = 256
OVERLAP = 30
DATA_FILE = Path("documents/rmp_all_professors.json")
OUTPUT_FILE = Path("documents/chunks.json")
TOKENIZER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RMP_BASE_URL = "https://www.ratemyprofessors.com/professor/"

tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)


def tokenize(text: str) -> list[int]:
    return tokenizer.encode(text, add_special_tokens=False)


def decode(token_ids: list[int]) -> str:
    return tokenizer.decode(token_ids, skip_special_tokens=True)


def split_into_chunks(text: str) -> list[str]:
    """Split text into chunks of CHUNK_SIZE tokens with OVERLAP token overlap."""
    token_ids = tokenize(text)
    if len(token_ids) <= CHUNK_SIZE:
        return [text]

    chunks = []
    start = 0
    while start < len(token_ids):
        end = min(start + CHUNK_SIZE, len(token_ids))
        chunks.append(decode(token_ids[start:end]))
        if end == len(token_ids):
            break
        start = end - OVERLAP
    return chunks


def make_chunks(data: dict) -> list[dict]:
    chunks = []

    for prof_id, entry in data.items():
        prof = entry["professor"]
        professor_name = f"{prof['firstName']} {prof['lastName']}"
        source_url = f"{RMP_BASE_URL}{prof_id}"

        for rating in entry["ratings"]:
            comment = (rating.get("comment") or "").strip()
            if not comment:
                continue

            tags = rating.get("ratingTags") or ""
            tags_clean = ", ".join(t.strip() for t in tags.split("--") if t.strip())

            wta = rating.get("wouldTakeAgain")
            wta_str = {1: "Yes", 0: "No"}.get(wta, "N/A")

            date_raw = rating.get("date") or ""
            date_str = date_raw[:10]  # YYYY-MM-DD

            base_metadata = {
                "professor_name": professor_name,
                "professor_id": prof_id,
                "course": rating.get("class") or "N/A",
                "date": date_str,
                "quality_rating": rating.get("qualityRating"),
                "difficulty_rating": rating.get("difficultyRatingRounded"),
                "grade": rating.get("grade") or "N/A",
                "would_take_again": wta_str,
                "tags": tags_clean,
                "source_url": source_url,
            }

            text_chunks = split_into_chunks(comment)
            for i, chunk_text in enumerate(text_chunks):
                chunk = {
                    "text": chunk_text,
                    "metadata": {
                        **base_metadata,
                        "chunk_index": i,
                        "total_chunks": len(text_chunks),
                    },
                }
                chunks.append(chunk)

    return chunks


def main():
    with open(DATA_FILE) as f:
        data = json.load(f)

    chunks = make_chunks(data)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(chunks, f, indent=2)

    token_counts = [len(tokenize(c["text"])) for c in chunks]
    print(f"Total chunks:  {len(chunks)}")
    print(f"Token range:   {min(token_counts)}–{max(token_counts)}")
    print(f"Avg tokens:    {sum(token_counts) / len(token_counts):.1f}")
    print(f"Saved to:      {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
