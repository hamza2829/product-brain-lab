from pathlib import Path

import pytest

from product_brain_lab.generate import generate


@pytest.fixture(scope="session")
def corpus_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("corpus")
    generate(directory)
    return directory
