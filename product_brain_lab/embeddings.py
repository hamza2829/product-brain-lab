import logging
import re
from collections import Counter
from collections.abc import Sequence
from hashlib import blake2b
from itertools import pairwise
from pathlib import Path
from threading import Lock
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

LOGGER = logging.getLogger(__name__)
WORD = re.compile(r"[a-z0-9]+")
STOP_WORDS = frozenset(
    "a about after all an and are as at be been but by can could did do does for from had has "
    "have how i in is it its of on or our say so than that the their them they this to up use "
    "was we were what when which who why will with would you your".split()
)


def terms(text: str) -> list[str]:
    return [word for word in WORD.findall(text.lower()) if word not in STOP_WORDS]


class Embedder(Protocol):
    name: str
    dimensions: int
    min_score: float

    def encode(self, texts: Sequence[str]) -> NDArray[np.float32]: ...


class HashEmbedder:
    name = "hash"
    dimensions = 4096
    min_score = 0.12

    def encode(self, texts: Sequence[str]) -> NDArray[np.float32]:
        vectors = np.zeros((len(texts), self.dimensions), dtype=np.float32)
        for row, content in zip(vectors, texts, strict=True):
            words = terms(content)
            bigrams = (f"{a} {b}" for a, b in pairwise(words))
            for token, count in Counter([*words, *bigrams]).items():
                value = int.from_bytes(blake2b(token.encode(), digest_size=8).digest(), "little")
                weight = 0.65 if " " in token else 1.0
                row[value % self.dimensions] += (1 if value >> 63 else -1) * weight * count**0.5
            norm = np.linalg.norm(row)
            if norm:
                row /= norm
        return vectors


class MiniLMEmbedder:
    name = "minilm"
    min_score = 0.28

    def __init__(self, path: Path) -> None:
        if not (path / "model.safetensors").is_file():
            raise FileNotFoundError(
                f"Run python -m product_brain_lab.models minilm to populate {path}"
            )

        import torch
        from sentence_transformers import SentenceTransformer

        torch.set_num_threads(4)
        self._model = SentenceTransformer(
            str(path.resolve()),
            device="cpu",
            local_files_only=True,
            trust_remote_code=False,
            model_kwargs={"use_safetensors": True},
        )
        self.dimensions = self._model.get_embedding_dimension()
        self._lock = Lock()

    def encode(self, texts: Sequence[str]) -> NDArray[np.float32]:
        with self._lock:
            return self._model.encode(
                list(texts),
                batch_size=32,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )


def select_embedder(mode: str, model_dir: Path) -> Embedder:
    path = model_dir / "minilm"
    match mode:
        case "hash":
            return HashEmbedder()
        case "minilm":
            return MiniLMEmbedder(path)
        case "auto":
            if (path / "model.safetensors").is_file():
                try:
                    return MiniLMEmbedder(path)
                except (ImportError, OSError, RuntimeError, ValueError) as exc:
                    LOGGER.warning("MiniLM unavailable, using hash embeddings: %s", exc)
            return HashEmbedder()
        case _:
            raise ValueError("PBL_EMBEDDINGS must be auto, hash, or minilm")
