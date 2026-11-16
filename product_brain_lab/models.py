"""Download pinned public model files for offline inference."""

import argparse
import os
from pathlib import Path

MODEL_SNAPSHOTS = {
    "minilm": (
        "sentence-transformers/all-MiniLM-L6-v2",
        "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        (
            "1_Pooling/config.json",
            "modules.json",
            "sentence_bert_config.json",
            "config_sentence_transformers.json",
            "vocab.txt",
        ),
    ),
    "smollm": (
        "HuggingFaceTB/SmolLM2-135M-Instruct",
        "12fd25f77366fa6b3b4b768ec3050bf629380bac",
        ("generation_config.json", "merges.txt", "vocab.json"),
    ),
}
COMMON_FILES = (
    "config.json",
    "model.safetensors",
    "special_tokens_map.json",
    "tokenizer.json",
    "tokenizer_config.json",
)


def model_directory() -> Path:
    return Path(os.getenv("PBL_MODEL_DIR", "data/models"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", choices=MODEL_SNAPSHOTS)
    args = parser.parse_args()

    from huggingface_hub import snapshot_download

    repo, revision, files = MODEL_SNAPSHOTS[args.model]
    directory = snapshot_download(
        repo_id=repo,
        revision=revision,
        local_dir=model_directory() / args.model,
        token=False,
        allow_patterns=[*COMMON_FILES, *files],
    )
    print(f"Downloaded {repo}@{revision} to {directory}")


if __name__ == "__main__":
    main()
