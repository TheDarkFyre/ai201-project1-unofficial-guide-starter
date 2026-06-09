# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

This unofficial guide compiles and makes searchable student reviews, difficulty ratings, and classroom experiences for Computer Science professors at San Jose State University. This specific knowledge is typically fragmented across dozens of individual profile pages, making it difficult to directly compare teaching styles, workload expectations, and grading policies. Centralizing this data allows students to quickly query and cross-reference qualitative insights that are impossible to find in official university course catalogs or by manually clicking through separate review sites.

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | RMP | Student Reviews of Sayma Akther | https://www.ratemyprofessors.com/professor/2926663 |
| 2 | RMP | Student Reviews of Nada Attar | https://www.ratemyprofessors.com/professor/2445092 |
| 3 | RMP | Student Reviews of Thomas Austin | https://www.ratemyprofessors.com/professor/2000580 |
| 4 | RMP | Student Reviews of Katerina Potika | https://www.ratemyprofessors.com/professor/2099184 |
| 5 | RMP | Student Reviews of Mark Stamp | https://www.ratemyprofessors.com/professor/281383 |
| 6 | RMP | Student Reviews of David Taylor | https://www.ratemyprofessors.com/professor/214947 |
| 7 | RMP | Student Reviews of Mike Wood | https://www.ratemyprofessors.com/professor/2922737 |
| 8 | RMP | Student Reviews of Tahereh Arabghalizi | https://www.ratemyprofessors.com/professor/2926378 |
| 9 | RMP | Student Reviews of Doug Case | https://www.ratemyprofessors.com/professor/3015141 |
| 10 | RMP | Student Reviews of Chung-Wen Tsao | https://www.ratemyprofessors.com/professor/2318479 |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** 256 tokens — the maximum input length of `all-MiniLM-L6-v2`. RateMyProfessors caps each review at 350 characters (~50–100 words), so almost every review fits in a single chunk.

**Overlap:** 30 tokens (~10% of chunk size). This is a safety margin for the rare case where a review maps to more tokens than expected. In practice, almost no review spans two chunks, but overlap ensures semantic continuity when one does.

**Why these choices fit your documents:** Each review is an independent unit of opinion from a single student about a specific professor and course. Keeping each review in its own chunk preserves that context — a chunk won't blend sentiment from two different students. Preprocessing strips empty comments, normalizes tag separators (`--` → `, `), and extracts structured metadata (professor name, course code, ratings, grade, would-take-again) stored alongside each chunk rather than embedded in the text.

**Final chunk count:** 569 chunks across 10 professors.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`, stored in ChromaDB with cosine similarity.

**Production tradeoff reflection:** For a production deployment, I would evaluate `text-embedding-3-large` (OpenAI) or `multilingual-e5-large` for their much larger context windows and stronger semantic accuracy on domain-specific short text. The main tradeoffs are latency and hosting: `all-MiniLM-L6-v2` runs locally and is fast, but its 256-token limit means it can't handle longer queries well. An API-hosted model adds network latency and cost per query, but would return more accurate similarity rankings on nuanced phrasing like "lenient grader" vs. "easy A," which is the kind of language students actually use. Multilingual support is not a concern here since all reviews are in English.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** The system prompt reads: *"You are a helpful assistant for students at San Jose State University choosing Computer Science courses. You answer questions using only the student reviews provided to you. Be specific and cite evidence from the reviews. If the reviews don't contain enough information to answer confidently, say so."* The key mechanism is the phrase "using **only** the student reviews provided to you" — this directly forbids the model from drawing on its training knowledge about professors or universities, and the instruction to say so when evidence is insufficient prevents confident-sounding hallucinations.

**How source attribution is surfaced in the response:** Each retrieved chunk is formatted as a numbered block (`[1]`, `[2]`, …) containing professor name, course code, quality/difficulty ratings, grade, would-take-again flag, and tags, followed by the review text. The model is instructed to cite evidence and naturally references these numbered reviews in its answer (e.g., "Review [2] states…"). The Gradio UI also displays the raw retrieved sources in a separate "Retrieved from" panel showing professor name and course for each chunk.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | How difficult are Mark Stamp's courses, and which course is the most difficult? | Average difficulty ~2.8/5; CS 166 is the hardest. | Retrieved reviews for CS265 (2/5), CS166 (3–4/5), CS158B (1/5), CS165 (2/5). Correctly identified CS166 as most difficult (4/5 in one review), with appropriate caveats about variability. | Relevant | Accurate |
| 2 | How hard of a grader is Tom Austin? | Lenient grader, very clear on criteria. | Retrieved reviews confirming he grades incredibly leniently on exams, curves the class, and gives credit for incomplete homework. Consistent with expected answer. | Relevant | Accurate |
| 3 | Is it better to take Katerina Potika or Chung-Wen Tsao for my elective? | Potika is better; higher take-again % (48% vs. 16%). | Retrieved reviews for both but could not surface take-again percentages. Gave a hedged qualitative comparison rather than a clear recommendation. | Partially relevant | Partially accurate |
| 4 | What is the average grade in Sayma Akther's classes? | Average grade is a B+. | Correctly retrieved grades (A, B−, A+, B+, A). Computed a numerical GPA average (~3.66, between B+ and A−) rather than simply naming the most common grade. | Relevant | Partially accurate |
| 5 | Which professor is best to take for CS 146? | Doug Case is better for CS 146. | Returned David Taylor and Katerina Potika reviews tagged CS146; did not surface Doug Case. Gave a mixed recommendation leaning toward Taylor, with no mention of Case. | Off-target | Inaccurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "Which professor is best to take for CS 146?"

**What the system returned:** Reviews for David Taylor and Katerina Potika tagged with CS146, with a mixed recommendation leaning toward Taylor. Doug Case — the expected better choice — was not retrieved at all.

**Root cause (tied to a specific pipeline stage):** The failure is in the retrieval stage, specifically how metadata filters interact with the course code parser. The `retrieve.py` course regex extracts "CS146" and applies a `where: {"course": {"$eq": "CS146"}}` filter. Doug Case's reviews in the source data likely used a different course code format (e.g., `"CS 146"` with a space, or left the course field as `"N/A"`), so they were excluded by the equality filter. Taylor had more reviews explicitly tagged "CS146," so he dominated the results even though students rate Case more favorably for that course.

**What you would change to fix it:** Replace the strict `$eq` filter with a fuzzy course match — either normalize all stored course codes to a canonical format (strip spaces, uppercase) at ingestion time in `chunk.py`, or use a `$contains` operator in the ChromaDB query. Normalizing at ingestion is the cleaner fix: `"CS 146"` → `"CS146"` across all metadata before storing.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** The Chunking Strategy section of `planning.md` specified the exact chunk size (256 tokens) and overlap (30 tokens) with the reasoning already written out, so giving it directly to Copilot as a prompt produced a working `split_into_chunks()` function on the first try with no size adjustments needed. Having the rationale documented meant I could also verify the output was correct — not just that it ran, but that the token counts matched the spec.

**One way your implementation diverged from the spec, and why:** The retrieval approach in the spec said "top-k = 5 with no filtering," but the implementation added a professor-name and course-code metadata filter in `retrieve.py`. During testing I found that semantic similarity alone returned off-topic reviews when a query named a specific professor — the model would retrieve reviews for similarly-rated professors instead. Adding explicit metadata filtering was necessary to keep results scoped to the professor or course the student actually asked about, even though it introduced the course-code normalization bug seen in the failure case above.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* The Chunking Strategy section from `planning.md` (chunk size 256 tokens, overlap 30 tokens, reasoning about review length) and asked Copilot to implement `chunk_text()` using the `sentence-transformers/all-MiniLM-L6-v2` tokenizer.
- *What it produced:* A function that tokenized text, split it into windows of 256 tokens with 30-token stride, and decoded each window back to a string.
- *What I changed or overrode:* The generated function operated on plain text strings but didn't handle the per-review metadata (course code, grade, ratings). I restructured it into `make_chunks()` in `chunk.py` which wraps each text chunk with a `metadata` dict, and added logic to skip reviews with empty comments.

**Instance 2**

- *What I gave the AI:* The generation requirements — system prompt text, the structured context format (numbered review blocks with professor/course/rating headers), and the constraint to use Groq's `llama-3.3-70b-versatile` model — and asked Claude to implement `answer()` in `generate.py`.
- *What it produced:* A complete `generate.py` with `build_context()` formatting numbered review blocks and `answer()` calling the Groq API with `temperature=0.2`.
- *What I changed or overrode:* The initial context format didn't include the "Would Take Again" field, which is important for comparison questions. I added `would_take_again` to the context line in `build_context()`. I also added a `--verbose` flag to the `__main__` block for debugging retrieval during evaluation.
