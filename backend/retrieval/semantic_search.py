import json
import math
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "paperless" / "processed" / "embeddings.jsonl"


def load_embeddings():
    with EMBEDDINGS_PATH.open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file if line.strip()]

    if not records:
        raise SystemExit("No saved embeddings found.")

    return records


def validate_records(records):
    model = records[0]["embedding_model"]
    dimensions = records[0]["embedding_dimensions"]

    for record in records:
        values = record["embedding"]

        if (
            record["embedding_model"] != model
            or record["embedding_dimensions"] != dimensions
            or len(values) != dimensions
            or not all(math.isfinite(value) for value in values)
            or not any(value != 0 for value in values)
        ):
            raise SystemExit("Saved embeddings contain incompatible or invalid data.")

    return model, dimensions


def embed_question(question, model, dimensions):
    load_dotenv(PROJECT_ROOT / "backend" / ".env")
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise SystemExit("GEMINI_API_KEY is missing.")

    prepared_question = f"task: search result | query: {question}"

    with genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=30_000),
    ) as client:
        response = client.models.embed_content(
            model=model,
            contents=prepared_question,
            config=types.EmbedContentConfig(
                output_dimensionality=dimensions,
            ),
        )

    if not response.embeddings or len(response.embeddings) != 1:
        raise SystemExit("Expected one question embedding.")

    values = response.embeddings[0].values

    if (
        not values
        or len(values) != dimensions
        or not all(math.isfinite(value) for value in values)
        or not any(value != 0 for value in values)
    ):
        raise SystemExit("Google returned an invalid question embedding.")

    return values


def cosine_similarity(first, second):
    dot_product = sum(a * b for a, b in zip(first, second))
    first_length = math.sqrt(sum(value * value for value in first))
    second_length = math.sqrt(sum(value * value for value in second))

    return dot_product / (first_length * second_length)


def main():
    records = load_embeddings()
    model, dimensions = validate_records(records)

    print(f"Loaded chunks: {len(records)}")

    question = input("Enter your question: ").strip()

    if not question:
        raise SystemExit("Please enter a question.")

    question_embedding = embed_question(question, model, dimensions)

    scored_records = []

    for record in records:
        score = cosine_similarity(
            question_embedding,
            record["embedding"],
        )
        scored_records.append((score, record))

    scored_records.sort(key=lambda item: item[0], reverse=True)

    for position, (score, record) in enumerate(scored_records[:5], start=1):
        heading = " > ".join(record["heading_path"]) or "(No heading)"

        print(f"\nResult {position} | Similarity: {score:.4f}")
        print(f"Source: {record['source_file']}")
        print(f"Section: {heading}")
        print(f"Lines: {record['start_line']}–{record['end_line']}")
        print(f"URL: {record['source_url']}")
        print(f"Text preview:\n{record['text'][:800]}")


if __name__ == "__main__":
    main()
