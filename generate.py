#!/usr/bin/env python3
"""Generation stage: retrieve relevant chunks and answer via Groq llama-3.3-70b-versatile."""

import os
from dotenv import load_dotenv
from groq import Groq
from retrieve import retrieve, print_results

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a helpful assistant for students at San Jose State University \
choosing Computer Science courses. You answer questions using only the student reviews \
provided to you. Be specific and cite evidence from the reviews. \
If the reviews don't contain enough information to answer confidently, say so."""


def build_context(chunks: list[dict]) -> str:
    lines = []
    for i, chunk in enumerate(chunks, 1):
        m = chunk["metadata"]
        lines.append(
            f"[{i}] Professor: {m.get('professor_name')} | Course: {m.get('course')} | "
            f"Quality: {m.get('quality_rating')}/5 | Difficulty: {m.get('difficulty_rating')}/5 | "
            f"Grade: {m.get('grade')} | Would Take Again: {m.get('would_take_again')} | "
            f"Tags: {m.get('tags')}\n"
            f"Review: {chunk['text']}"
        )
    return "\n\n".join(lines)


def answer(query: str, verbose: bool = False) -> str:
    chunks = retrieve(query)

    if verbose:
        print("--- Retrieved chunks ---")
        print_results(chunks)
        print("--- Generating answer ---\n")

    context = build_context(chunks)
    user_message = f"Student reviews:\n\n{context}\n\nQuestion: {query}"

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import sys
    verbose = "--verbose" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--verbose"]
    query = " ".join(args) if args else "Which professor is best to take for CS 146?"
    print(f"Q: {query}\n")
    print(answer(query, verbose=verbose))
