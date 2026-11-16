from collections.abc import Iterable, Iterator
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, ValidationError


class Source(StrEnum):
    JIRA = "jira"
    CONFLUENCE = "confluence"
    SLACK = "slack"
    SHAREPOINT = "sharepoint"


class Document(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source: Source
    title: str
    date: date
    initiative: str
    kind: str
    author: str
    body: str
    related_ids: tuple[str, ...]


class Connector(Protocol):
    def documents(self) -> Iterable[Document]: ...


class MockFileConnector:
    source: Source

    def __init__(self, directory: Path) -> None:
        self.path = directory / f"{self.source.value}.jsonl"

    def documents(self) -> Iterator[Document]:
        try:
            with self.path.open(encoding="utf-8") as records:
                for line_number, line in enumerate(records, 1):
                    if not line.strip():
                        continue
                    try:
                        doc = Document.model_validate_json(line)
                        if doc.source != self.source:
                            raise ValueError(f"expected {self.source} but found {doc.source}")
                    except (ValidationError, ValueError) as exc:
                        raise ValueError(f"{self.path}:{line_number}: {exc}") from exc
                    yield doc
        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"{self.path} is missing. Run python -m product_brain_lab.generate first."
            ) from exc


class MockJiraConnector(MockFileConnector):
    source = Source.JIRA


class MockConfluenceConnector(MockFileConnector):
    source = Source.CONFLUENCE


class MockSlackConnector(MockFileConnector):
    source = Source.SLACK


class MockSharePointConnector(MockFileConnector):
    source = Source.SHAREPOINT


def mock_connectors(directory: Path) -> tuple[Connector, ...]:
    return (
        MockJiraConnector(directory),
        MockConfluenceConnector(directory),
        MockSlackConnector(directory),
        MockSharePointConnector(directory),
    )


def load_documents(connectors: Iterable[Connector]) -> dict[str, Document]:
    documents: dict[str, Document] = {}
    for connector in connectors:
        for doc in connector.documents():
            if doc.id in documents:
                raise ValueError(f"Duplicate source ID: {doc.id}")
            documents[doc.id] = doc
    return documents
