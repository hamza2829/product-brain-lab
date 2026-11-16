from pathlib import Path

import pytest

from product_brain_lab.answering import Answer, Citation
from product_brain_lab.corpus import load_documents, mock_connectors
from product_brain_lab.evaluate import Case, evaluate, load_cases


def test_all_50_case_labels_resolve(corpus_dir: Path):
    docs = load_documents(mock_connectors(corpus_dir))
    label_path = Path(__file__).resolve().parents[1] / "evaluation/questions.jsonl"
    cases = load_cases(label_path.read_text(encoding="utf-8"), docs)
    assert len(cases) == 50
    assert {docs[key].source for case in cases for key in case.expected_ids} == {
        "confluence",
        "slack",
        "jira",
        "sharepoint",
    }


def test_case_validation_checks_filters(corpus_dir: Path):
    docs = load_documents(mock_connectors(corpus_dir))
    text = '{"id":"bad","question":"What decision?","sources":["jira"],"expected_ids":["CF-001"]}'
    with pytest.raises(ValueError, match="CF-001 is missing or excluded"):
        load_cases(text, docs)


def test_metrics_count_misses_non_gold_citations_and_abstentions(corpus_dir: Path):
    docs = load_documents(mock_connectors(corpus_dir))

    def cite(key: str) -> Citation:
        doc = docs[key]
        return Citation(
            id=key,
            title=doc.title,
            source=doc.source,
            date=doc.date,
            kind=doc.kind,
            quote=doc.body[:20],
            score=0.5,
        )

    class ExampleEngine:
        def ask(self, question, filters):
            if question == "First question?":
                return Answer(
                    answer="Partial evidence.",
                    answer_mode="extractive",
                    citations=[cite("CF-001"), cite("CF-002")],
                    retrieved_source_ids=["CF-001", "CF-002"],
                )
            return Answer(
                answer="No evidence.",
                answer_mode="insufficient",
                citations=[],
                retrieved_source_ids=[],
            )

    report = evaluate(
        ExampleEngine(),
        [
            Case(id="one", question="First question?", expected_ids=["CF-001", "SLACK-001"]),
            Case(id="two", question="Other question?", expected_ids=["JIRA-001"]),
        ],
    )
    assert report["summary"]["recall_at_5"] == 0.25
    assert report["summary"]["citation_precision"] == 0.5
    assert report["summary"]["abstentions"] == 1
    assert report["cases"][0]["non_gold_citations"] == ["CF-002"]
    assert report["cases"][0]["missed_ids"] == ["SLACK-001"]
