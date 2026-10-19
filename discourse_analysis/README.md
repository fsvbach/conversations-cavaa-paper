# Conversation analysis

Scripts behind the conversation-pattern table of the paper. Run from `scripts/`, in this order:

1. `prepare_transcripts.py` writes one Markdown transcript per conversation to `transcripts/` (not committed).
2. `compute_turn.py` computes the rule-based turn tags.
3. `compute_llm_judgments.py` tags turns with an LLM judge via a local Ollama server (`qwen3.6:35b-a3b`, about one hour). Its output `results/llm_judgments.csv` is included, so this step can be skipped.
4. `compute_sequences.py` computes the sequence tags.
5. `compute_overall.py` writes `results/overall_comparison.csv` and the n-gram and message-frequency tables.

The judge prompt is documented in `../prompts/llm_judge_prompts.md`.
