from datetime import date
from pathlib import Path

import numpy as np
import pytest

from product_brain_lab.corpus import load_documents, mock_connectors
from product_brain_lab.embeddings import HashEmbedder, select_embedder
from product_brain_lab.retrieval import SearchFilters, VectorIndex, chunk_document


def test_chunking_keeps_source_and_overlap(corpus_dir: Path):
    source = load_documents(mock_connectors(corpus_dir))["CF-001"]
    doc = source.model_copy(update={"body": "one two\nthree four five six seven eight nine ten"})
    chunks = list(chunk_document(doc, size=5, overlap=2))

    assert [chunk.start_word for chunk in chunks] == [0, 3, 6]
    assert [chunk.text for chunk in chunks] == [
        "one two\nthree four five",
        "four five six seven eight",
        "seven eight nine ten",
    ]
    assert all(chunk.document is doc for chunk in chunks)
    with pytest.raises(ValueError, match="overlap"):
        list(chunk_document(doc, size=5, overlap=5))


def test_hash_vectors_are_deterministic_and_normalized(tmp_path: Path):
    texts = ["Weekly activity digest on Monday", "the and"]
    first = select_embedder("auto", tmp_path)
    second = HashEmbedder()
    assert first.name == "hash"
    assert np.array_equal(first.encode(texts), second.encode(texts))
    assert np.linalg.norm(first.encode(texts), axis=1) == pytest.approx([1.0, 0.0])


def test_filtering_happens_before_top_k_and_chunks_do_not_repeat_a_source(corpus_dir: Path):
    docs = load_documents(mock_connectors(corpus_dir))
    doc = docs["CF-001"]
    repeated = doc.model_copy(update={"body": doc.body * 4})
    other = docs["CF-002"]
    index = VectorIndex([repeated, other], HashEmbedder())
    assert len(index.chunks) > 2
    question = "Why did guided setup lead with a teammate invitation instead of CSV import?"
    assert {hit.document.id for hit in index.search(question, limit=5)} == {doc.id, other.id}
    filters = SearchFilters(from_date=other.date, to_date=other.date)
    assert [hit.document.id for hit in index.search(question, filters, limit=1)] == [other.id]
    assert index.search(question, SearchFilters(to_date=date(2000, 1, 1))) == []
