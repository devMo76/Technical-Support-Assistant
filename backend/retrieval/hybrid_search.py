from rank_bm25 import BM25Okapi

from backend.retrieval.keyword_search import load_chunks, tokenize
from backend.retrieval.semantic_search import (
    cosine_similarity,
    embed_question,
    load_embeddings,
    validate_records,
)

CANDIDATE_LIMIT = 20
RESULT_LIMIT = 5
RRF_CONSTANT = 60


def validate_corpus(chunks, embeddings):
    chunk_lookup = {record["id"]: record for record in chunks}
    embedding_lookup = {record["id"]: record for record in embeddings}

    if len(chunk_lookup) != len(chunks) or len(embedding_lookup) != len(embeddings):
        raise SystemExit("Duplicate chunk IDs detected.")

    if chunk_lookup.keys() != embedding_lookup.keys():
        raise SystemExit("Chunks and embeddings differ. Update the embeddings first.")

    fields = (
        "text",
        "source_file",
        "source_version",
        "source_hash",
        "heading_path",
        "start_line",
        "end_line",
        "source_url",
    )

    for chunk_id, chunk in chunk_lookup.items():
        embedded = embedding_lookup[chunk_id]

        if any(chunk[field] != embedded[field] for field in fields):
            raise SystemExit(f"Chunk and embedding metadata differ: {chunk_id}")


def keyword_candidates(question, chunks):
    documents = [tokenize(record["text"]) for record in chunks]
    index = BM25Okapi(documents)
    scores = index.get_scores(tokenize(question))

    ranked = sorted(
        zip(scores, chunks),
        key=lambda item: (-float(item[0]), item[1]["id"]),
    )

    return [record for score, record in ranked if score > 0][:CANDIDATE_LIMIT]


def semantic_candidates(question, embeddings):
    model, dimensions = validate_records(embeddings)
    question_vector = embed_question(question, model, dimensions)

    ranked = sorted(
        embeddings,
        key=lambda record: (
            -cosine_similarity(question_vector, record["embedding"]),
            record["id"],
        ),
    )

    return ranked[:CANDIDATE_LIMIT]


def fuse_rankings(keyword_results, semantic_results):
    combined = {}

    for method, results in (
        ("keyword", keyword_results),
        ("semantic", semantic_results),
    ):
        for rank, record in enumerate(results, start=1):
            chunk_id = record["id"]

            if chunk_id not in combined:
                combined[chunk_id] = {
                    "record": record,
                    "rrf_score": 0.0,
                    "keyword_rank": None,
                    "semantic_rank": None,
                }

            combined[chunk_id]["rrf_score"] += 1 / (RRF_CONSTANT + rank)
            combined[chunk_id][f"{method}_rank"] = rank

    return sorted(
        combined.values(),
        key=lambda item: (-item["rrf_score"], item["record"]["id"]),
    )[:RESULT_LIMIT]


def retrieve(question):
    question = question.strip()

    if not question:
        raise ValueError("Please enter a question.")

    chunks = load_chunks()
    embeddings = load_embeddings()
    validate_corpus(chunks, embeddings)

    keyword_results = keyword_candidates(question, chunks)
    semantic_results = semantic_candidates(question, embeddings)

    return fuse_rankings(keyword_results, semantic_results)


def main():
    chunks = load_chunks()
    embeddings = load_embeddings()
    validate_corpus(chunks, embeddings)

    print(f"Loaded chunks: {len(chunks)}")
    question = input("Enter your question: ").strip()

    if not question:
        raise SystemExit("Please enter a question.")

    keyword_results = keyword_candidates(question, chunks)
    semantic_results = semantic_candidates(question, embeddings)
    results = fuse_rankings(keyword_results, semantic_results)

    print(f"\nKeyword candidates: {len(keyword_results)}")
    print(f"Semantic candidates: {len(semantic_results)}")

    for position, result in enumerate(results, start=1):
        record = result["record"]
        heading = " > ".join(record["heading_path"]) or "(No heading)"
        keyword_rank = result["keyword_rank"] or "Not in top candidates"
        semantic_rank = result["semantic_rank"] or "Not in top candidates"

        print(f"\nResult {position} | RRF: {result['rrf_score']:.6f}")
        print(f"Keyword rank: {keyword_rank}")
        print(f"Semantic rank: {semantic_rank}")
        print(f"Source: {record['source_file']}")
        print(f"Section: {heading}")
        print(f"Lines: {record['start_line']}–{record['end_line']}")
        print(f"URL: {record['source_url']}")
        print(f"Text preview:\n{record['text'][:800]}")


if __name__ == "__main__":
    main()
