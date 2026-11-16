"""Score document recall at five and citation precision on the fictional question set."""

import argparse
import json
from hashlib import sha256
from pathlib import Path
from statistics import mean

from pydantic import Field

from product_brain_lab.answering import TOP_K, AnswerEngine
from product_brain_lab.api import AskRequest
from product_brain_lab.corpus import Document, load_documents, mock_connectors
from product_brain_lab.embeddings import select_embedder
from product_brain_lab.generate import DEFAULT_DATA_DIR
from product_brain_lab.models import model_directory
from product_brain_lab.retrieval import VectorIndex


class Case(AskRequest):
    id: str = Field(min_length=1)
    expected_ids: list[str] = Field(min_length=1)


def load_cases(text: str, documents: dict[str, Document]) -> list[Case]:
    cases = []
    seen: set[str] = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        case = Case.model_validate_json(line)
        if case.id in seen or len(case.expected_ids) != len(set(case.expected_ids)):
            raise ValueError(f"{case.id}: duplicate case ID or expected source ID")
        filters = case.filters()
        for key in case.expected_ids:
            if key not in documents or not filters.accepts(documents[key]):
                raise ValueError(f"{case.id}: expected source {key} is missing or excluded")
        cases.append(case)
        seen.add(case.id)
    if not cases:
        raise ValueError("Evaluation needs at least one labeled question")
    return cases


def evaluate(engine: AnswerEngine, cases: list[Case]) -> dict:
    outcomes = []
    for case in cases:
        result = engine.ask(case.question, case.filters())
        retrieved = result.retrieved_source_ids
        cited = [citation.id for citation in result.citations]
        missed = [key for key in case.expected_ids if key not in retrieved]
        non_gold = [key for key in cited if key not in case.expected_ids]
        outcomes.append(
            {
                **case.model_dump(mode="json", exclude_defaults=True),
                "retrieved_ids": retrieved,
                "cited_ids": cited,
                "missed_ids": missed,
                "non_gold_citations": non_gold,
                "recall_at_5": (len(case.expected_ids) - len(missed)) / len(case.expected_ids),
                "answer_mode": result.answer_mode,
            }
        )
    total_citations = sum(len(row["cited_ids"]) for row in outcomes)
    off_label = sum(len(row["non_gold_citations"]) for row in outcomes)
    matched_citations = total_citations - off_label
    return {
        "summary": {
            "questions": len(outcomes),
            "recall_at_5": mean(row["recall_at_5"] for row in outcomes),
            "citation_precision": matched_citations / total_citations if total_citations else None,
            "matched_citations": matched_citations,
            "total_citations": total_citations,
            "questions_with_retrieval_misses": sum(bool(row["missed_ids"]) for row in outcomes),
            "questions_with_non_gold_citations": sum(
                bool(row["non_gold_citations"]) for row in outcomes
            ),
            "abstentions": sum(row["answer_mode"] == "insufficient" for row in outcomes),
        },
        "cases": outcomes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--questions", type=Path, default=Path("evaluation/questions.jsonl"))
    parser.add_argument("--embeddings", choices=("hash", "minilm"), default="hash")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    documents = load_documents(mock_connectors(args.data_dir))
    labels = args.questions.read_bytes()
    cases = load_cases(labels.decode("utf-8"), documents)
    embedder = select_embedder(args.embeddings, model_directory())
    index = VectorIndex(documents.values(), embedder)
    corpus_hash = sha256()
    for key in sorted(documents):
        corpus_hash.update(f"{documents[key].model_dump_json()}\n".encode())
    report = {
        "embeddings": embedder.name,
        "top_k": TOP_K,
        "embedding_dimensions": embedder.dimensions,
        "documents": len(documents),
        "chunks": len(index.chunks),
        "corpus_sha256": corpus_hash.hexdigest(),
        "questions_sha256": sha256(labels).hexdigest(),
        **evaluate(AnswerEngine(index), cases),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"{embedder.name}: {json.dumps(report['summary'])}")


if __name__ == "__main__":
    main()
