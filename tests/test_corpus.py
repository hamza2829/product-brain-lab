from collections import Counter
from datetime import date
from pathlib import Path

import pytest

from product_brain_lab.corpus import MockJiraConnector, Source, load_documents, mock_connectors
from product_brain_lab.generate import DEFAULT_SEED, generate


def test_seeded_files_have_fixed_counts_and_resolving_links(corpus_dir: Path, tmp_path: Path):
    same_seed = tmp_path / "same"
    different_seed = tmp_path / "different"
    generate(same_seed, DEFAULT_SEED)
    generate(different_seed, DEFAULT_SEED + 1)
    for source in Source:
        filename = f"{source}.jsonl"
        assert (same_seed / filename).read_bytes() == (corpus_dir / filename).read_bytes()
        assert (different_seed / filename).read_bytes() != (corpus_dir / filename).read_bytes()

    docs = load_documents(mock_connectors(corpus_dir))
    assert Counter(doc.source for doc in docs.values()) == {
        Source.JIRA: 150,
        Source.CONFLUENCE: 40,
        Source.SLACK: 200,
        Source.SHAREPOINT: 20,
    }
    assert all(
        doc.related_ids and doc.id not in doc.related_ids and set(doc.related_ids) <= docs.keys()
        for doc in docs.values()
    )
    assert docs["CF-002"].date < docs["CF-001"].date < docs["SP-002"].date
    assert docs["CF-001"].date.year == 2025
    assert all(isinstance(doc.date, date) for doc in docs.values())


def test_mock_connector_rejects_a_record_from_the_wrong_source(corpus_dir: Path, tmp_path: Path):
    first_line = (corpus_dir / "slack.jsonl").read_text(encoding="utf-8").splitlines()[0]
    (tmp_path / "jira.jsonl").write_text(first_line, encoding="utf-8")
    with pytest.raises(ValueError, match=r"jira\.jsonl:1:.*expected jira but found slack"):
        list(MockJiraConnector(tmp_path).documents())


def test_loading_duplicate_ids_fails(corpus_dir: Path):
    mock = MockJiraConnector(corpus_dir)
    with pytest.raises(ValueError, match="Duplicate source ID: JIRA-001"):
        load_documents([mock, mock])
