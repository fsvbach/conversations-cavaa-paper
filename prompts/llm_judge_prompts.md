# LLM-as-a-judge prompt

Prompt of `discourse_analysis/scripts/compute_llm_judgments.py`, one request per turn and tag, sent to Ollama with `think: false` and the system message `Reasoning: low`. Model: Qwen3.6-35B-A3B-FP8 (Ollama tag `qwen3.6:35b-a3b`). `{transcript}` is the conversation in English, one `USER:` or `AGENT:` line per turn, the judged turn prefixed with `>>> `.

## Prompt 16: LLM judge

```text
You are annotating a conversation between a user and a political voting-advice chatbot.

Definition:
- {tag}: {definition}

Transcript (the turn marked with >>> is the one to judge):
{transcript}

Judge only the marked {USER|AGENT} turn.
Respond with only a JSON object of the form {"{tag}": {answer format}}. No other text.
```

## Tags

| Tag | Judged on | `{definition}` | `{answer format}` |
|---|---|---|---|
| `topic_drift` | all turns | true if the turn changes the subject away from the current VAA statement | `<true or false>` |
| `dialogue_act` | chatbot turns | classify the marked turn using exactly one of these labels: yes_no_question, open_question, opinion, statement, answer | `<one of ['yes_no_question', 'open_question', 'opinion', 'statement', 'answer']>` |
| `dialogue_act` | user turns annotated as questions | classify the form of the marked question using exactly one of these labels: yes_no_question, open_question | `<one of ['yes_no_question', 'open_question']>` |
| `context_break` | chatbot turns | true if the agent ignores, contradicts, or fails to build on prior turns | `<true or false>` |
| `stance_leak` | chatbot turns | true if the agent expresses its own political position rather than reporting party positions | `<true or false>` |
| `directive_framing` | chatbot turns | true if the agent steers the user toward a conclusion or emphasizes one side | `<true or false>` |
