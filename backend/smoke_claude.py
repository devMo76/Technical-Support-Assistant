from backend.claude_service import ask_claude


def main():
    response = ask_claude(
        "Reply only with: Connection successful.",
        max_tokens=32,
    )

    for block in response.content:
        if block.type == "text":
            print(block.text)

    print("Output tokens:", response.usage.output_tokens)
    print("Stop reason:", response.stop_reason)


if __name__ == "__main__":
    main()
