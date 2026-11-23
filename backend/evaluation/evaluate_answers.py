import argparse
import json
from pathlib import Path

from backend.answer_question import generate_answer
from backend.evaluation.evaluate_retrieval import load_cases

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "evals" / "paperless" / "results" / "answers"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", default="Q01")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    case = next(
        (item for item in load_cases() if item["id"] == args.case),
        None,
    )

    if case is None:
        raise SystemExit(f"Unknown case: {args.case}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{case['id']}.json"

    if output_path.exists() and not args.overwrite:
        raise SystemExit(
            f"Result already exists: {output_path}\n"
            "Use --overwrite only if you want a new API request."
        )

    print(f"Generating answer for {case['id']}...", flush=True)

    # Only the question reaches the assistant—not the expected answer.
    result = generate_answer(case["question"])

    report = {
        "case_id": case["id"],
        "question": case["question"],
        "expected_language": case["language"],
        "answerable": case["answerable"],
        "expected_answer": case["expected_answer"],
        "expected_evidence": case["evidence"],
        "generated_result": result,
        "review": {
            "correctness": None,
            "citation_support": None,
            "language": None,
            "abstention": None,
            "notes": "",
        },
    }

    temporary_path = output_path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(output_path)

    print(f"\nExpected answer:\n{case['expected_answer']}")
    print(f"\nGenerated answer:\n{result['answer']}")
    print(f"\nInput tokens: {result['input_tokens']}")
    print(f"Output tokens: {result['output_tokens']}")
    print(f"Saved report: {output_path}")
    print("Review status: pending")


if __name__ == "__main__":
    main()
