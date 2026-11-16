# Product Brain Lab

Ask why a product decision was made, what customers said, or how a pilot will be measured. The React app shows excerpts, links to complete source records, filters by source and date, and saves useful/not-useful votes to SQLite.

The workspace belongs to **Aster Quay**, a fictional product organization. The seed builds 150 Jira-style tickets, 40 Confluence-style pages, 200 Slack-style threads, and 20 SharePoint-style playbooks and worksheets. The four connectors are file-backed mocks. Running the app requires Python 3.12 and Node 22.13 or later. It runs locally without Docker, service accounts, or API keys.

## Run locally

From the repository root on macOS or Linux:

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m product_brain_lab.generate
npm ci --prefix frontend
npm run build --prefix frontend
python -m uvicorn product_brain_lab.api:app --host 127.0.0.1 --port 8000
```

On Windows with the Python launcher:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m product_brain_lab.generate
npm.cmd ci --prefix frontend
npm.cmd run build --prefix frontend
.\.venv\Scripts\python.exe -m uvicorn product_brain_lab.api:app --host 127.0.0.1 --port 8000
```

Open [the app](http://127.0.0.1:8000/) or [the interactive API docs](http://127.0.0.1:8000/docs). For frontend development, keep the API running and use `npm run dev --prefix frontend`. Vite proxies `/api` to port 8000.

Try “Why did guided setup lead with a teammate invitation instead of CSV import?” or “What did agency coordinators say about sharing with a client who has no login?”

### CPU models

The base install uses deterministic hash embeddings when MiniLM weights are absent. To use the small [all-MiniLM-L6-v2 sentence-transformers model](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2), stop the API, download the pinned public files, and start the API again from the repository root. On Linux and Windows use the CPU wheel index. On macOS, install `'.[models]'` directly using PyPI.

```sh
python -m pip install --index-url https://download.pytorch.org/whl/cpu 'torch==2.15.0'
python -m pip install -e '.[models]'
python -m product_brain_lab.models minilm
```

Set `PBL_EMBEDDINGS=minilm` to require MiniLM, or `PBL_EMBEDDINGS=hash` to force hashing. The default `auto` uses the downloaded MiniLM model when it can load it. Inference uses local weights on CPU.

The API uses extractive answers by default. For the experimental [SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) provider, run `python -m product_brain_lab.models smollm` after installing the model dependencies and set `PBL_ANSWER_MODEL=smollm` before starting the API. For example, use `export PBL_ANSWER_MODEL=smollm` in a POSIX shell or `$env:PBL_ANSWER_MODEL = 'smollm'` in PowerShell. The provider drafts from the top passage and attaches that passage's source ID. If loading fails or the draft fails a basic check for overlap with the passage, the API uses the extractive path.

## Architecture

1. `product_brain_lab.generate` writes four JSONL files using seed 43 by default. `--seed` and `--out` support other reproducible runs. Every record has a source ID, date, initiative, and resolvable links to other records.
2. Each mock connector implements `Connector.documents()` and normalizes records to `Document`. A future connector can supply that same type. `PBL_DATA_DIR` overrides the default `data/synthetic` input directory.
3. The API builds an in-memory FAISS `IndexFlatIP` on startup. It embeds 90-word chunks with an 18-word overlap, includes the record title in each embedding, and searches normalized vectors by inner product. The index scores all chunks at this corpus size, applies inclusive source/date filters, and keeps the best chunk per document before taking the top five documents.
4. `POST /api/ask` accepts a question and optional `sources`, `from_date`, and `to_date`. It returns an answer, its mode, up to two cited records, and the ranked retrieval IDs. Below the similarity cutoff, the API reports insufficient evidence. The answer provider interface has a deterministic mock for tests and the optional local model. The extractive path quotes retrieved text.
5. Source cards open full records with `GET /api/sources/{id}`. `POST /api/feedback` writes the answer UUID, vote, and update time to `data/feedback.sqlite3`. A second vote replaces the prior vote for that UUID. Set `PBL_FEEDBACK_DB` to choose a different file.

## Tests and evaluation

```sh
python -m ruff check .
python -m ruff format --check .
python -m pytest
npm run lint --prefix frontend
npm test --prefix frontend
npm run build --prefix frontend
python -m product_brain_lab.evaluate --embeddings hash --out evaluation/results/hash.json
python -m product_brain_lab.evaluate --embeddings minilm --out evaluation/results/minilm.json
```

The [evaluation report](evaluation/README.md) describes 50 labeled questions, the measured scores and misses, and how to reproduce them. [GitHub Actions](.github/workflows/ci.yml) runs lint, the backend tests, the frontend tests and production build, and both evaluations. It uploads the per-question JSON reports as `retrieval-evaluation`.

## Product and boundaries

- [Personas](docs/product/personas.md), [user stories](docs/product/user-stories.md), and a [study plan and success metrics](docs/product/validation.md) cover the product manager and chief product officer workflows. Real-user validation is still pending.
- The records and benchmark are synthetic. Mock sources carry no real connector behavior such as access permissions or synchronization. This prototype is built for a single local workspace.
- The corpus is small and the index rebuilds on each startup. Similarity cutoffs are heuristics. The small models can retrieve irrelevant evidence or generate an unsupported claim even when a returned source ID is valid. The benchmark checks citation IDs against labels. It does not perform claim-level fact checking.
- OpenAI Codex wrote the code, synthetic records, evaluation questions, and product documentation.
