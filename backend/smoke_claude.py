import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv


def main():
    load_dotenv(Path(__file__).parent / ".env")

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is missing.")

    with Anthropic(timeout=30.0, max_retries=0) as client:
        response = client.messages.create(
            model=os.environ["ANTHROPIC_MODEL"],
            max_tokens=32,
            output_config={"effort": os.getenv("ANTHROPIC_EFFORT", "low")},
            thinking={"type": "disabled"},
            messages=[
                {
                    "role": "user",
                    "content": "Reply only with: Connection successful.",
                }
            ],
        )

    for block in response.content:
        if block.type == "text":
            print(block.text)


if __name__ == "__main__":
    main()
