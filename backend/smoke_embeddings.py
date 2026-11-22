import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


def main():
    load_dotenv(Path(__file__).resolve().parent / ".env")

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_EMBEDDING_MODEL")

    if not api_key or not model:
        raise SystemExit("Gemini API key or embedding model is missing.")

    with genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=30_000),
    ) as client:
        response = client.models.embed_content(
            model=model,
            contents="Paperless stores and organizes documents.",
        )

    if not response.embeddings or not response.embeddings[0].values:
        raise SystemExit("Google returned no embedding.")

    values = response.embeddings[0].values

    print("Embedding connection successful.")
    print(f"Model: {model}")
    print(f"Embedding dimensions: {len(values)}")


if __name__ == "__main__":
    main()
