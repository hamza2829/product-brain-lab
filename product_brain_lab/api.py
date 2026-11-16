import os
from collections import Counter
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Annotated, Self
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from product_brain_lab.answering import Answer, AnswerEngine, AnswerProvider, select_provider
from product_brain_lab.corpus import Document, Source, load_documents, mock_connectors
from product_brain_lab.embeddings import select_embedder
from product_brain_lab.feedback import FeedbackStore
from product_brain_lab.generate import DEFAULT_DATA_DIR
from product_brain_lab.models import model_directory
from product_brain_lab.retrieval import SearchFilters, VectorIndex


@dataclass(frozen=True)
class Settings:
    data_dir: Path = DEFAULT_DATA_DIR
    feedback_db: Path = Path("data/feedback.sqlite3")
    model_dir: Path = Path("data/models")
    frontend_dir: Path = Path("frontend/dist")
    embeddings: str = "auto"
    answer_model: str = "extractive"

    @classmethod
    def from_environment(cls) -> Self:
        return cls(
            data_dir=Path(os.getenv("PBL_DATA_DIR", str(DEFAULT_DATA_DIR))),
            feedback_db=Path(os.getenv("PBL_FEEDBACK_DB", "data/feedback.sqlite3")),
            model_dir=model_directory(),
            frontend_dir=Path(os.getenv("PBL_FRONTEND_DIR", "frontend/dist")),
            embeddings=os.getenv("PBL_EMBEDDINGS", "auto"),
            answer_model=os.getenv("PBL_ANSWER_MODEL", "extractive"),
        )


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: Annotated[str, Field(min_length=3, max_length=480)]
    sources: Annotated[set[Source], Field(max_length=len(Source))] = Field(default_factory=set)
    from_date: date | None = None
    to_date: date | None = None

    @model_validator(mode="after")
    def ordered_dates(self) -> Self:
        if self.from_date and self.to_date and self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        return self

    def filters(self) -> SearchFilters:
        return SearchFilters(tuple(self.sources), self.from_date, self.to_date)


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_id: UUID
    useful: StrictBool


class Status(BaseModel):
    embeddings: str
    provider: str
    documents: dict[Source, int]
    chunks: int


@dataclass(frozen=True)
class Services:
    docs: dict[str, Document]
    engine: AnswerEngine
    feedback: FeedbackStore


def create_app(
    settings: Settings | None = None, *, provider: AnswerProvider | None = None
) -> FastAPI:
    config = settings or Settings.from_environment()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        documents = load_documents(mock_connectors(config.data_dir))
        embedder = select_embedder(config.embeddings, config.model_dir)
        index = VectorIndex(documents.values(), embedder)
        answer_provider = provider or select_provider(config.answer_model, config.model_dir)
        app.state.services = Services(
            docs=documents,
            engine=AnswerEngine(index, answer_provider),
            feedback=FeedbackStore(config.feedback_db),
        )
        yield

    app = FastAPI(title="Product Brain Lab", version="0.1.0", lifespan=lifespan)

    @app.get("/api/status")
    def status(request: Request) -> Status:
        services: Services = request.app.state.services
        engine = services.engine
        return Status(
            embeddings=engine.index.embedder.name,
            provider=engine.provider.mode if engine.provider else "extractive",
            documents=dict(Counter(doc.source for doc in services.docs.values())),
            chunks=len(engine.index.chunks),
        )

    @app.post("/api/ask")
    def ask(body: AskRequest, request: Request) -> Answer:
        services: Services = request.app.state.services
        return services.engine.ask(body.question, body.filters())

    @app.get("/api/sources/{source_id}")
    def source(source_id: str, request: Request) -> Document:
        services: Services = request.app.state.services
        doc = services.docs.get(source_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Source record not found")
        return doc

    @app.post("/api/feedback", status_code=204)
    def feedback(body: FeedbackRequest, request: Request) -> Response:
        services: Services = request.app.state.services
        services.feedback.save(body.answer_id, body.useful)
        return Response(status_code=204)

    if (config.frontend_dir / "index.html").is_file():
        app.mount("/", StaticFiles(directory=config.frontend_dir, html=True), name="frontend")
    return app


app = create_app()
