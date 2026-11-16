# Retrieval evaluation

The labeled set covers 50 questions across 10 fictional initiatives. It includes decision rationale, customer insights, rollout strategy, success measures, support handoffs, and source/date constraints. The evaluator checks that every gold ID exists and is eligible under that question's filters.

- **Recall at five** is the mean, across questions, of the fraction of expected document IDs in the first five distinct retrieved IDs.
- **Citation precision** is the number of cited IDs that are in the corresponding gold set divided by all cited IDs across the run. Abstentions return zero citations and are reported separately. An off-label citation may contain overlapping information. This metric measures agreement with the source labels.

## Local run

Both embedding modes used the same 410 records, 420 chunks, seed 43, and extractive answers. The optional answer model was outside this benchmark.

| Embeddings | Recall at five | Citation precision | Questions with a retrieval miss | Abstentions |
| --- | ---: | ---: | ---: | ---: |
| [Hash](results/hash.json) | 87.00% | 75.28% (67/89) | 11/50 | 1 |
| [MiniLM on CPU](results/minilm.json) | 89.67% | 70.00% (70/100) | 8/50 | 0 |

Both modes missed CF-004 and SP-002 on `q04`, a question that paraphrases the guided setup success measure without naming the initiative. MiniLM returned unrelated QA records in its first five. Hash retrieval abstained on `q25`, the Jira-only question about an incorrect intake merge. The JSON files list the retrieved IDs, cited IDs, missed gold IDs, and off-label citations for every question.

During development, the three-citation cap produced 66.09% precision for hash embeddings (76/115) and 51.33% for MiniLM (77/150). The final cap is two. Both runs informed the prototype, so treat this set as a development benchmark.

A separate CPU smoke check exercised the optional SmolLM2 answer provider through FastAPI with hash retrieval. It returned a draft on the guided setup question and fell back to excerpts on the expiring-link and audit-export questions. These three requests were a path check. They do not estimate answer quality.

To reproduce, run `python -m product_brain_lab.generate` and the two evaluation commands in the [root README](../README.md#tests-and-evaluation). CI generates independent reports from the default seed and retains them under `retrieval-evaluation` in the Actions run.
