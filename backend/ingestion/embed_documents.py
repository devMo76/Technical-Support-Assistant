import argparse
import hashlib
import json
import math
import os
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "paperless" / "processed"
INPUT_PATH = DATA_DIR / "chunks.jsonl"
OUTPUT_PATH = DATA_DIR / "embeddings.jsonl"
DIMENSIONS = 768


def read_jsonl(path):
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def save_progress(records):
    """Replace the output only after the temporary file is fully written."""
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=DATA_DIR,
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)

            for record in records:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

            file.flush()
            os.fsync(file.fileno())

        temporary_path.replace(OUTPUT_PATH)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def valid_vector(values):
    return (
        isinstance(values, list)
        and len(values) == DIMENSIONS
        and all(
            isinstance(value, (int, float)) and math.isfinite(value) for value in values
        )
        and any(value != 0 for value in values)
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Maximum number of new embeddings to generate.",
    )
    args = parser.parse_args()

    if args.limit < 1:
        raise SystemExit("--limit must be at least 1.")

    load_dotenv(PROJECT_ROOT / "backend" / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_EMBEDDING_MODEL")

    if not api_key or not model:
        raise SystemExit("Gemini API key or model is missing.")

    chunks = read_jsonl(INPUT_PATH)
    chunk_ids = [chunk["id"] for chunk in chunks]

    if not chunks or len(chunk_ids) != len(set(chunk_ids)):
        raise SystemExit("Input is empty or contains duplicate chunk IDs.")

    previous = read_jsonl(OUTPUT_PATH) if OUTPUT_PATH.exists() else []
    cached = {record["id"]: record for record in previous}
    completed = []
    pending = []

    for chunk in chunks:
        if not chunk["text"].strip():
            raise SystemExit(f"Empty chunk: {chunk['id']}")

        title = " > ".join(chunk["heading_path"]) or chunk["source_file"]
        prepared_text = f"title: {title} | text: {chunk['text']}"
        input_hash = hashlib.sha256(prepared_text.encode("utf-8")).hexdigest()
        existing = cached.get(chunk["id"])

        if (
            existing
            and existing.get("embedding_model") == model
            and existing.get("embedding_dimensions") == DIMENSIONS
            and existing.get("embedding_input_hash") == input_hash
            and valid_vector(existing.get("embedding"))
        ):
            completed.append(
                {
                    **chunk,
                    **{
                        key: existing[key]
                        for key in (
                            "embedding_model",
                            "embedding_dimensions",
                            "embedding_input_hash",
                            "embedding",
                        )
                    },
                }
            )
        else:
            pending.append((chunk, prepared_text, input_hash))

    print(f"Chunks: {len(chunks)}")
    print(f"Already completed: {len(completed)}")
    print(f"Remaining: {len(pending)}")

    with genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=30_000),
    ) as client:
        for chunk, prepared_text, input_hash in pending[: args.limit]:
            # Check the complete input, including its heading.
            count = client.models.count_tokens(
                model=model,
                contents=prepared_text,
            )

            if count.total_tokens is None or count.total_tokens > 8192:
                raise SystemExit(
                    f"Input limit check failed: {chunk['id']}. No text was cut."
                )

            response = client.models.embed_content(
                model=model,
                contents=prepared_text,
                config=types.EmbedContentConfig(
                    output_dimensionality=DIMENSIONS,
                ),
            )

            if not response.embeddings or len(response.embeddings) != 1:
                raise SystemExit("Expected exactly one embedding.")

            values = response.embeddings[0].values

            if not valid_vector(values):
                raise SystemExit("Google returned an invalid embedding.")

            completed.append(
                {
                    **chunk,
                    "embedding_model": model,
                    "embedding_dimensions": DIMENSIONS,
                    "embedding_input_hash": input_hash,
                    "embedding": values,
                }
            )

            save_progress(completed)
            print(f"Saved {len(completed)}/{len(chunks)}")

            # Space requests out; your actual free-tier quota may differ.
            time.sleep(4)

    print(f"\nSaved embeddings: {len(completed)}/{len(chunks)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
