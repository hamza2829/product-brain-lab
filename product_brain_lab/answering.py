import logging
import math
from datetime import date
from pathlib import Path
from threading import Lock
from typing import Literal, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from product_brain_lab.corpus import Source
from product_brain_lab.embeddings import terms
from product_brain_lab.retrieval import NO_FILTERS, Hit, SearchFilters, VectorIndex

LOGGER = logging.getLogger(__name__)
TOP_K = 5
MAX_CITATIONS = 2
ProviderMode = Literal["local-model", "mock"]
AnswerMode = Literal["extractive", "insufficient"] | ProviderMode


class Draft(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    answer: str = Field(min_length=1, max_length=1500)
    citation_ids: list[str] = Field(min_length=1, max_length=MAX_CITATIONS)


class AnswerProvider(Protocol):
    mode: ProviderMode

    def draft(self, question: str, evidence: list[Hit]) -> Draft | None: ...


class MockLLM:
    mode: ProviderMode = "mock"

    def draft(self, question: str, evidence: list[Hit]) -> Draft:
        hit = evidence[0]
        return Draft(
            answer=f"Mock answer from {hit.document.title}.",
            citation_ids=[hit.document.id],
        )


class SmolLMProvider:
    mode: ProviderMode = "local-model"

    def __init__(self, path: Path) -> None:
        if not (path / "model.safetensors").is_file():
            raise FileNotFoundError(
                f"Run python -m product_brain_lab.models smollm to populate {path}"
            )

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        torch.set_num_threads(4)
        self._tokenizer = AutoTokenizer.from_pretrained(
            path, local_files_only=True, trust_remote_code=False
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            path, local_files_only=True, trust_remote_code=False, use_safetensors=True
        ).eval()
        self._inference_mode = torch.inference_mode
        self._lock = Lock()

    def draft(self, question: str, evidence: list[Hit]) -> Draft | None:
        hit = evidence[0]
        excerpt = evidence_quote(question, hit.chunk.text)
        messages = [
            {
                "role": "system",
                "content": (
                    "Answer using only the note. Write one or two sentences. "
                    'If the note does not answer the question, write "Insufficient evidence."'
                ),
            },
            {"role": "user", "content": f"Workspace note:\n{excerpt}\n\nQuestion: {question}"},
        ]
        with self._lock, self._inference_mode():
            inputs = self._tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
            )
            generated = self._model.generate(**inputs, max_new_tokens=96, do_sample=False)
            output = self._tokenizer.decode(
                generated[0, inputs["input_ids"].shape[1] :], skip_special_tokens=True
            )
        answer = output.strip().split("\n\n", 1)[0]
        answer_terms = set(terms(answer))
        if (
            answer.lower().startswith(("insufficient evidence", "question:", "workspace note:"))
            or len(answer_terms) < 3
            or len(answer_terms & set(terms(excerpt))) < len(answer_terms) * 0.5
        ):
            return None
        return Draft(answer=answer, citation_ids=[hit.document.id])


def select_provider(mode: str, model_dir: Path) -> AnswerProvider | None:
    match mode:
        case "extractive":
            return None
        case "smollm":
            try:
                return SmolLMProvider(model_dir / "smollm")
            except (ImportError, OSError, RuntimeError, ValueError) as exc:
                LOGGER.warning("Local answer model unavailable, using extractive answers: %s", exc)
                return None
        case _:
            raise ValueError("PBL_ANSWER_MODEL must be extractive or smollm")


class Citation(BaseModel):
    id: str
    title: str
    source: Source
    date: date
    kind: str
    quote: str
    score: float


class Answer(BaseModel):
    answer_id: UUID = Field(default_factory=uuid4)
    answer: str
    answer_mode: AnswerMode
    citations: list[Citation]
    retrieved_source_ids: list[str]


def evidence_quote(question: str, passage: str) -> str:
    query_terms = set(terms(question))
    lines = [line.strip() for line in passage.splitlines() if len(line.split()) > 3]

    def overlap(line: str) -> float:
        words = set(terms(line))
        return len(query_terms & words) / math.sqrt(max(1, len(words)))

    best = max(lines, key=overlap, default=passage)
    if len(best) > 420:
        best = best[:420].rsplit(" ", 1)[0] + "…"
    return best


class AnswerEngine:
    def __init__(self, index: VectorIndex, provider: AnswerProvider | None = None) -> None:
        self.index = index
        self.provider = provider

    def ask(self, question: str, filters: SearchFilters = NO_FILTERS) -> Answer:
        hits = self.index.search(question, filters, limit=TOP_K)
        retrieved = [hit.document.id for hit in hits]
        minimum = self.index.embedder.min_score
        if not hits or hits[0].score < minimum:
            return Answer(
                answer="I couldn't find enough evidence in the selected sources.",
                answer_mode="insufficient",
                citations=[],
                retrieved_source_ids=retrieved,
            )

        cutoff = max(minimum, hits[0].score * 0.65)
        evidence = [hit for hit in hits if hit.score >= cutoff][:MAX_CITATIONS]
        citations = {
            hit.document.id: Citation(
                id=hit.document.id,
                title=hit.document.title,
                source=hit.document.source,
                date=hit.document.date,
                kind=hit.document.kind,
                quote=evidence_quote(question, hit.chunk.text),
                score=round(hit.score, 6),
            )
            for hit in evidence
        }
        if self.provider is not None:
            try:
                draft = self.provider.draft(question, evidence)
                if draft is not None and set(draft.citation_ids) <= citations.keys():
                    return Answer(
                        answer=draft.answer,
                        answer_mode=self.provider.mode,
                        citations=[citations[key] for key in dict.fromkeys(draft.citation_ids)],
                        retrieved_source_ids=retrieved,
                    )
                LOGGER.warning("Answer provider returned no draft or cited unavailable sources")
            except (OSError, RuntimeError, ValueError) as exc:
                LOGGER.warning("Answer provider failed, using extractive answer: %s", exc)

        return Answer(
            answer="\n\n".join(f"{cite.quote} [{cite.id}]" for cite in citations.values()),
            answer_mode="extractive",
            citations=list(citations.values()),
            retrieved_source_ids=retrieved,
        )
