# Evaluation

Measures how well AarogyaAI finds the right MedQuAD passage, declines off-topic
questions, and (with Ollama) how faithful its answers are to the passages it cites.

| File | Purpose |
|---|---|
| `eval_set.json` | 100 questions: dev and test splits, each with 40 MedQuAD questions (from 40 different documents) and 10 hand-written off-topic questions. Built by `build_eval_set.py` with a fixed seed. |
| `ood_questions.json` | The hand-written off-topic questions. |
| `run_eval.py` | Runs the evaluation and writes tables to `results/`. |

```bash
python scripts/prepare_medquad.py                         # once: dataset/medquad.json
python eval/run_eval.py --split dev  --chunk-sizes 500 1000 0   # tune on dev
python eval/run_eval.py --split test --chunk-sizes 500 1000 0   # report on test
# answer quality (needs `ollama pull llama3.1:8b qwen2.5:7b`):
python eval/run_eval.py --split test --chunk-sizes 500 1000 --models llama3.1:8b qwen2.5:7b
# dense retrieval (needs backend/requirements-embeddings.txt):
python eval/run_eval.py --split dev --retriever faiss --chunk-sizes 500 1000
```

The dev split is the only one used to choose settings (chunk size, decline threshold);
the test split is only used to report numbers. With 40 questions per split, a difference
of 0.05 is two questions, so treat small gaps as noise.
