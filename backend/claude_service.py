import os
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv


def ask_claude(
    message: str,
    *,
    max_tokens: int = 512,
    system: str = "",
):
    load_dotenv(Path(__file__).parent / ".env")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ANTHROPIC_MODEL")
    effort = os.getenv("ANTHROPIC_EFFORT", "low")

    if not api_key or not model:
        raise RuntimeError("Claude API key or model is missing.")

    if effort != "low":
        raise RuntimeError("This project requires low effort.")

    with Anthropic(
        api_key=api_key,
        timeout=30.0,
        max_retries=0,
    ) as client:
        return client.messages.create(
            system=system,
            model=model,
            max_tokens=max_tokens,
            output_config={"effort": effort},
            thinking={"type": "disabled"},
            messages=[{"role": "user", "content": message}],
        )
