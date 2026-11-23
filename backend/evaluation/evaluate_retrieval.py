import json
import time
from pathlib import Path

from backend.retrieval.hybrid_search import retrieve

PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUESTIONS_PATH = PROJECT_ROOT / "evals" / "paperless" / "questions.json"


def load_cases():
    data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return data["cases"]


def evidence_found(evidence, results):
    expected_start, expected_end = evidence["lines"]
    expected_lines = set(range(expected_start, expected_end + 1))
    retrieved_lines = set()

    for result in results:
        record = result["record"]

        if record["source_file"] != evidence["file"]:
            continue

        overlap_start = max(expected_start, record["start_line"])
        overlap_end = min(expected_end, record["end_line"])

        retrieved_lines.update(range(overlap_start, overlap_end + 1))

    return expected_lines.issubset(retrieved_lines)


def main():
    cases = load_cases()
    answerable = [case for case in cases if case["answerable"]]
    successful_questions = 0

    for case in answerable:
        if not case["evidence"]:
            raise SystemExit(f"Missing evidence labels: {case['id']}")

        results = retrieve(case["question"])[:5]

        found = sum(evidence_found(evidence, results) for evidence in case["evidence"])

        hit = found > 0
        successful_questions += int(hit)

        print(
            f"{case['id']} | Hit@5: {'YES' if hit else 'NO'} | "
            f"Evidence covered: {found}/{len(case['evidence'])}",
            flush=True,
        )

        time.sleep(4)

    total = len(answerable)

    if not total:
        raise SystemExit("No answerable cases found.")

    print(
        f"\nHit Rate@5: {successful_questions}/{total} "
        f"({successful_questions / total:.1%})"
    )
    print("Development cases only; answer quality is not evaluated here.")


if __name__ == "__main__":
    main()
