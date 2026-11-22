import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from backend.ingestion.chunk_documents import (
    DATA_DIR,
    TARGET_CHARS,
    build_chunk_records,
    chunk_section,
    split_sections_with_headings,
    write_jsonl_atomic,
)


class HeadingTests(unittest.TestCase):
    def test_heading_hierarchy_and_continuation_chunks(self):
        text = (
            "# Parent\n\n"
            "## Child\n\n"
            "First paragraph has enough text to split.\n\n"
            "Second paragraph continues under the child heading.\n"
        )
        sections = split_sections_with_headings(text)
        child_section, heading_path = sections[1]
        chunks = chunk_section(child_section, max_chars=55)

        self.assertGreater(len(chunks), 1)
        self.assertEqual(heading_path, ["Parent", "Child"])
        self.assertEqual("".join(chunks), child_section)

    def test_heading_like_text_in_fence_is_ignored(self):
        text = "# Parent\n\n```md\n# Not a heading\n```\n\n## Child\nBody\n"
        sections = split_sections_with_headings(text)

        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0][1], ["Parent"])
        self.assertIn("# Not a heading", sections[0][0])
        self.assertEqual(sections[1][1], ["Parent", "Child"])


class DocumentChunkingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with contextlib.redirect_stdout(io.StringIO()):
            cls.records = build_chunk_records()

    def test_all_guides_only_and_no_blank_chunks(self):
        represented = {record["source_file"] for record in self.records}
        self.assertEqual(
            represented,
            {
                "documents/usage.md",
                "documents/setup.md",
                "documents/configuration.md",
                "documents/troubleshooting.md",
                "documents/administration.md",
            },
        )
        self.assertTrue(all(record["text"].strip() for record in self.records))

    def test_text_and_line_ranges_match_sources(self):
        for source_file in {record["source_file"] for record in self.records}:
            source_text = (DATA_DIR / source_file).read_bytes().decode("utf-8")
            source_lines = source_text.splitlines(keepends=True)
            records = [
                record
                for record in self.records
                if record["source_file"] == source_file
            ]

            self.assertEqual("".join(record["text"] for record in records), source_text)
            for record in records:
                expected = "".join(
                    source_lines[record["start_line"] - 1 : record["end_line"]]
                )
                self.assertEqual(record["text"], expected)

    def test_ids_are_unique(self):
        ids = [record["id"] for record in self.records]
        self.assertEqual(len(ids), len(set(ids)))

    def test_permissions_table_remains_intact(self):
        oversized = [
            record for record in self.records if len(record["text"]) > TARGET_CHARS
        ]
        self.assertEqual(len(oversized), 1)
        self.assertEqual(oversized[0]["source_file"], "documents/usage.md")
        self.assertIn("Permissions", oversized[0]["heading_path"])
        self.assertTrue(oversized[0]["text"].startswith("| Type"))

    def test_jsonl_is_valid_and_identical_across_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "chunks.jsonl"
            write_jsonl_atomic(self.records, output)
            first = output.read_bytes()
            parsed = [json.loads(line) for line in first.decode("utf-8").splitlines()]

            write_jsonl_atomic(self.records, output)
            second = output.read_bytes()

        self.assertEqual(parsed, self.records)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
