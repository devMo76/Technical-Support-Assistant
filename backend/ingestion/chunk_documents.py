import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "paperless"
OUTPUT_PATH = DATA_DIR / "processed" / "chunks.jsonl"
TARGET_CHARS = 2000


def heading_details(line):
    match = re.match(r"^(#{1,6})[ \t]+(.+?)[ \t]*\r?\n?$", line)
    if not match:
        return None

    title = re.sub(r"[ \t]+#+[ \t]*$", "", match.group(2)).strip()
    return len(match.group(1)), title


def split_sections_with_headings(text):
    sections = []
    current_lines = []
    current_heading_path = []
    heading_stack = []
    fence_character = None
    fence_length = 0

    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        fence = re.match(r"^(`{3,}|~{3,})", stripped)

        if fence:
            marker = fence.group(1)

            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
            elif (
                marker[0] == fence_character
                and len(marker) >= fence_length
                and not stripped[len(marker) :].strip()
            ):
                fence_character = None

        heading = heading_details(line) if fence_character is None else None

        if heading:
            if current_lines:
                sections.append(("".join(current_lines), current_heading_path))
                current_lines = []

            level, title = heading
            heading_stack = [item for item in heading_stack if item[0] < level]
            heading_stack.append((level, title))
            current_heading_path = [item[1] for item in heading_stack]

        current_lines.append(line)

    if current_lines:
        sections.append(("".join(current_lines), current_heading_path))

    return sections


def split_sections(text):
    return [section for section, _heading_path in split_sections_with_headings(text)]


def chunk_section(section, max_chars=TARGET_CHARS):
    blocks = []
    current_block = []
    fence_character = None
    fence_length = 0

    for line in section.splitlines(keepends=True):
        stripped = line.lstrip()
        fence = re.match(r"^(`{3,}|~{3,})", stripped)

        if fence:
            marker = fence.group(1)

            if fence_character is None:
                fence_character = marker[0]
                fence_length = len(marker)
            elif (
                marker[0] == fence_character
                and len(marker) >= fence_length
                and not stripped[len(marker) :].strip()
            ):
                fence_character = None

        current_block.append(line)

        # A blank line outside a code block ends a paragraph or table block.
        if not line.strip() and fence_character is None:
            blocks.append("".join(current_block))
            current_block = []

    if current_block:
        blocks.append("".join(current_block))

    chunks = []
    current_chunk = ""

    for block in blocks:
        if current_chunk and len(current_chunk) + len(block) > max_chars:
            chunks.append(current_chunk)
            current_chunk = ""

        # A single large block stays intact; max_chars is deliberately soft.
        current_chunk += block

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def build_chunk_records():
    manifest = json.loads((DATA_DIR / "sources.json").read_text(encoding="utf-8"))
    documents = [
        item
        for item in manifest["files"]
        if item["file"].startswith("documents/") and item["file"].endswith(".md")
    ]

    if not documents:
        raise SystemExit("No Markdown guides listed in sources.json.")

    print(f"Document version: {manifest['tag']}\n")
    chunk_records = []

    for document in documents:
        path = DATA_DIR / document["file"]
        content = path.read_bytes()
        actual_hash = hashlib.sha256(content).hexdigest()

        if actual_hash != document["sha256"]:
            raise SystemExit(f"Content verification failed: {path.name}")

        text = content.decode("utf-8")
        chunks_with_headings = []

        for section, heading_path in split_sections_with_headings(text):
            chunks_with_headings.extend(
                (chunk, heading_path) for chunk in chunk_section(section)
            )

        chunks = [chunk for chunk, _heading_path in chunks_with_headings]
        if "".join(chunks) != text:
            raise SystemExit(f"Text preservation check failed: {path.name}")

        start_line = 1

        for index, (chunk, heading_path) in enumerate(chunks_with_headings):
            if not chunk.strip():
                raise SystemExit(f"Whitespace-only chunk detected: {path.name}")

            end_line = start_line + len(chunk.splitlines()) - 1
            identity = json.dumps(
                [document["file"], document["sha256"], index, chunk],
                ensure_ascii=False,
            )
            chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()

            chunk_records.append(
                {
                    "id": chunk_id,
                    "text": chunk,
                    "source_file": document["file"],
                    "source_version": manifest["tag"],
                    "source_hash": document["sha256"],
                    "source_url": document["source_url"],
                    "start_line": start_line,
                    "end_line": end_line,
                    "heading_path": heading_path,
                }
            )
            start_line = end_line + 1

        largest_chunk = max(len(chunk) for chunk in chunks)
        oversized = sum(len(chunk) > TARGET_CHARS for chunk in chunks)

        print(f"{path.name}: verified, {len(chunks)} chunks")
        print(f"  Largest chunk: {largest_chunk:,} characters")
        print(f"  Chunks above {TARGET_CHARS:,}-character target: {oversized}")
        if oversized:
            print("  WARNING: oversized blocks were preserved intact (soft limit).")

    chunk_ids = [record["id"] for record in chunk_records]
    if len(chunk_ids) != len(set(chunk_ids)):
        raise SystemExit("Duplicate chunk IDs detected.")

    print(f"\nTotal documents: {len(documents)}")
    print(f"Total chunk records: {len(chunk_records)}")
    print("Chunk IDs: all unique")
    return chunk_records


def write_jsonl_atomic(records, output_path=OUTPUT_PATH):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            for record in records:
                json.dump(record, temporary_file, ensure_ascii=False)
                temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        temporary_path.replace(output_path)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def main():
    chunk_records = build_chunk_records()
    write_jsonl_atomic(chunk_records)
    print(f"Saved UTF-8 JSONL: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
