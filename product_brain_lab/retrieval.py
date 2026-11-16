import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date

import faiss
import numpy as np

from product_brain_lab.corpus import Document, Source
from product_brain_lab.embeddings import Embedder

WORD_SPAN = re.compile(r"\S+")


@dataclass(frozen=True)
class Chunk:
    document: Document
    text: str
    start_word: int


def chunk_document(doc: Document, *, size: int = 90, overlap: int = 18) -> Iterator[Chunk]:
    if not 0 <= overlap < size:
        raise ValueError("Chunk overlap must be smaller than the positive size")
    words = list(WORD_SPAN.finditer(doc.body))
    for start in range(0, len(words), size - overlap):
        stop = min(start + size, len(words))
        yield Chunk(doc, doc.body[words[start].start() : words[stop - 1].end()], start)
        if stop == len(words):
            break


@dataclass(frozen=True)
class SearchFilters:
    sources: tuple[Source, ...] = ()
    from_date: date | None = None
    to_date: date | None = None

    def accepts(self, doc: Document) -> bool:
        return (
            (not self.sources or doc.source in self.sources)
            and (self.from_date is None or doc.date >= self.from_date)
            and (self.to_date is None or doc.date <= self.to_date)
        )


NO_FILTERS = SearchFilters()


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float

    @property
    def document(self) -> Document:
        return self.chunk.document


class VectorIndex:
    def __init__(self, documents: Iterable[Document], embedder: Embedder) -> None:
        self.embedder = embedder
        self.chunks = [chunk for doc in documents for chunk in chunk_document(doc)]
        self._index = faiss.IndexFlatIP(embedder.dimensions)
        if self.chunks:
            vectors = embedder.encode(
                [f"{chunk.document.title}\n{chunk.text}" for chunk in self.chunks]
            )
            self._index.add(np.ascontiguousarray(vectors, dtype=np.float32))

    def search(
        self, question: str, filters: SearchFilters = NO_FILTERS, *, limit: int = 5
    ) -> list[Hit]:
        if not self.chunks or limit <= 0:
            return []
        query = np.ascontiguousarray(self.embedder.encode([question]), dtype=np.float32)
        # This corpus is small. Score all chunks, then apply filters and document deduplication
        # before taking the top k, so irrelevant chunks cannot consume the result budget.
        scores, positions = self._index.search(query, self._index.ntotal)
        hits = sorted(
            (
                Hit(self.chunks[position], float(score))
                for score, position in zip(scores[0], positions[0], strict=True)
            ),
            key=lambda hit: (-hit.score, hit.document.id, hit.chunk.start_word),
        )
        selected: dict[str, Hit] = {}
        for hit in hits:
            if filters.accepts(hit.document):
                selected.setdefault(hit.document.id, hit)
                if len(selected) == limit:
                    break
        return list(selected.values())
