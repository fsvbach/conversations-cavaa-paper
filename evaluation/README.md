# Module evaluation

Run reports of the chatbot modules behind Section 3 of the paper. Each run has a human-readable `*_report.txt` and a machine-readable `*_report.json` with per-case results.

| Paper number | Run | Value in the run |
|---|---|---|
| Guardrails: F1 0.91, recall 92%, precision 91%, 2.7% legitimate messages blocked; 1,298 messages, 286 to block | `results/guardrails/20260630_google_gemma-4-E4B-it_01` | TP 262, FN 24, TN 985, FP 27 |
| Routing: 89% correct, macro F1 0.94, 97% correct empty sets; 1,012 messages | `results/query_routing/20260630_google_gemma-4-E4B-it_01` | exact set match 897/1,012 = 88.6% |
| Retrieval: recall@20 69%, precision@20 19%, MRR 0.53, hit@20 93%, median first relevant rank 2; 682 messages | `results/retrieval/rewriting_v3`, recomputed with `results/retrieval/recompute_metrics.py` | `results/retrieval/recomputed_metrics.txt` |
| Stance: 56% four-class, 80% binary on 9,627 comments | `results/stance_classification/20260701_Qwen_Qwen3.6-35B-A3B-FP8_01`, post-processed in `../notebooks/stance_classification.ipynb`, section 7 | raw accuracy 54.1% on 11,295 comments; the paper drops the two categories with a neutral answer option |

`datasets/` holds the evaluated messages with their expected labels (`guardrail_eval.json`, `router_eval.json`, `retrieval_eval.json`: 118 hand-written German seed messages, each paraphrased ten times) and the retrieval corpus `passages.json` (1,550 passages). The stored `retrieval_report.txt` predates a fix of the retrieval metric, so the paper uses the recomputed numbers. The stance report lists per comment only its category, the candidate's answer and the module's label; the comment texts are smartvote data and not redistributed.
