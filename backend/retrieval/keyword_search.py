import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNKS_PATH = PROJECT_ROOT / "data" / "paperless" / "processed" / "chunks.jsonl"


def tokenize(text):
    return re.findall(r"\w+", text.lower())


def load_chunks():
    with CHUNKS_PATH.open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file if line.strip()]

    if not records:
        raise SystemExit("No document chunks found.")

    return records


def main():
    records = load_chunks()

    tokenized_documents = [tokenize(record["text"]) for record in records]
    index = BM25Okapi(tokenized_documents)

    print(f"Loaded chunks: {len(records)}")

    question = input("Enter your question: ").strip()
    query_tokens = tokenize(question)

    if not query_tokens:
        raise SystemExit("Please enter searchable words.")

    scores = index.get_scores(query_tokens)

    ranked_results = sorted(
        enumerate(scores),
        key=lambda item: item[1],
        reverse=True,
    )

    matches = [(position, score) for position, score in ranked_results if score > 0][:5]

    if not matches:
        print("No keyword matches found.")
        return

    for rank, (position, score) in enumerate(matches, start=1):
        record = records[position]
        heading = " > ".join(record["heading_path"]) or "(No heading)"

        print(f"\nResult {rank} | BM25 score: {score:.4f}")
        print(f"Source: {record['source_file']}")
        print(f"Section: {heading}")
        print(f"Lines: {record['start_line']}–{record['end_line']}")
        print(f"Text preview:\n{record['text'][:800]}")


if __name__ == "__main__":
    main()
