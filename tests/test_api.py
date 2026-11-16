import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from product_brain_lab.answering import Draft, MockLLM
from product_brain_lab.api import Settings, create_app

QUESTION = "Why did guided setup lead with a teammate invitation instead of CSV import?"


@pytest.fixture
def config(corpus_dir: Path, tmp_path: Path) -> Settings:
    return Settings(
        data_dir=corpus_dir,
        feedback_db=tmp_path / "feedback.sqlite3",
        frontend_dir=tmp_path / "dist",
        embeddings="hash",
    )


@pytest.fixture
def client(config: Settings):
    with TestClient(create_app(config)) as session:
        yield session


def test_extractive_answer_links_to_verbatim_evidence(client: TestClient):
    response = client.post("/api/ask", json={"question": QUESTION})
    assert response.status_code == 200
    result = response.json()
    assert result["answer_mode"] == "extractive"
    assert len(set(result["retrieved_source_ids"])) == 5
    assert {"CF-001", "SLACK-001"} <= set(result["retrieved_source_ids"])
    assert "lacked a sample file" in result["answer"]
    for citation in result["citations"]:
        doc = client.get(f"/api/sources/{citation['id']}").json()
        assert citation["id"] in result["retrieved_source_ids"]
        assert citation["quote"].rstrip("…") in doc["body"]
        assert f"[{citation['id']}]" in result["answer"]
    assert client.get("/api/sources/NO-000").status_code == 404


def test_source_and_date_filters_are_inclusive(client: TestClient):
    doc = client.get("/api/sources/CF-001").json()
    result = client.post(
        "/api/ask",
        json={
            "question": QUESTION,
            "sources": ["confluence"],
            "from_date": doc["date"],
            "to_date": doc["date"],
        },
    ).json()
    assert result["retrieved_source_ids"] == ["CF-001"]
    assert [citation["id"] for citation in result["citations"]] == ["CF-001"]


@pytest.mark.parametrize(
    "body",
    [
        {"question": "What is the weather in Tokyo?"},
        {"question": QUESTION, "to_date": "2000-01-01"},
    ],
)
def test_unavailable_evidence_abstains(client: TestClient, body: dict):
    result = client.post("/api/ask", json=body).json()
    assert result["answer_mode"] == "insufficient"
    assert result["citations"] == []


@pytest.mark.parametrize(
    "body",
    [
        {"question": "   "},
        {"question": "q" * 481},
        {"question": QUESTION, "sources": ["unknown"]},
        {"question": QUESTION, "from_date": "2025-02-01", "to_date": "2025-01-01"},
    ],
)
def test_rejects_invalid_queries(client: TestClient, body: dict):
    assert client.post("/api/ask", json=body).status_code == 422


def test_mock_llm_is_injected_without_model_files(config: Settings):
    with TestClient(create_app(config, provider=MockLLM())) as client:
        result = client.post("/api/ask", json={"question": QUESTION}).json()
    assert result["answer_mode"] == "mock"
    assert len(result["citations"]) == 1
    assert result["citations"][0]["id"] == result["retrieved_source_ids"][0]


def test_provider_cannot_cite_an_unknown_source(config: Settings):
    class InvalidProvider(MockLLM):
        def draft(self, question, evidence):
            return Draft(answer="An unsupported draft.", citation_ids=["INVENTED-007"])

    with TestClient(create_app(config, provider=InvalidProvider())) as client:
        result = client.post("/api/ask", json={"question": QUESTION}).json()
    assert result["answer_mode"] == "extractive"
    assert "INVENTED-007" not in [citation["id"] for citation in result["citations"]]


def test_missing_optional_llm_uses_extractive_mode(config: Settings, tmp_path: Path):
    from dataclasses import replace

    selected = replace(config, model_dir=tmp_path / "models", answer_model="smollm")
    with TestClient(create_app(selected)) as client:
        assert client.get("/api/status").json()["provider"] == "extractive"


def test_feedback_is_updated_in_sqlite_and_validates_types(client: TestClient, config: Settings):
    answer_id = client.post("/api/ask", json={"question": QUESTION}).json()["answer_id"]
    for useful in (True, False):
        response = client.post("/api/feedback", json={"answer_id": answer_id, "useful": useful})
        assert response.status_code == 204
        assert response.content == b""
    assert (
        client.post("/api/feedback", json={"answer_id": answer_id, "useful": "true"}).status_code
        == 422
    )
    with closing(sqlite3.connect(config.feedback_db)) as db:
        assert db.execute("SELECT answer_id, useful FROM feedback").fetchall() == [(answer_id, 0)]


def test_built_frontend_and_api_share_an_origin(config: Settings):
    config.frontend_dir.mkdir()
    (config.frontend_dir / "index.html").write_text("<h1>Lab</h1>", encoding="utf-8")
    with TestClient(create_app(config)) as client:
        assert client.get("/?source=CF-001").text == "<h1>Lab</h1>"
        status = client.get("/api/status").json()
        assert status["embeddings"] == "hash"
        assert sum(status["documents"].values()) == 410
        assert status["chunks"] > 410
