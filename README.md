# Comparing Dialogue Management Strategies in CAVAAs

Data, prompts, and analysis code of the paper

> Báez Santamaría, S., Salvisberg, P., Bachmann, F.: Comparing Dialogue Management Strategies with a Modular Platform for Conversational Agent Voting Advice Applications. In: CONVERSATIONS 2026. Lecture Notes in Computer Science, Springer (2026). https://doi.org/10.1007/placeholder

## Contents

| Folder | Content | Paper |
|---|---|---|
| `prompts/` | the chatbot's system prompts (Prompts 1 to 15) and the LLM-judge prompt | Sections 3 and 4 |
| `evaluation/` | module benchmarks: evaluated messages, retrieval corpus, run reports | Section 3 |
| `data/` | the user-study data, see below | Sections 4 and 5 |
| `notebooks/` | `stance_classification.ipynb` (stance module on user turns and the smartvote benchmark), `dropout_analysis.ipynb`, `dialogue_strategies.ipynb` (post-survey effects, `figures/effect_sizes.pdf`), `covariate_analysis.ipynb` (adjusted effects) | Section 5 |
| `discourse_analysis/` | rule-based and LLM-judge tagging of the conversations, `results/overall_comparison.csv` | Section 5, conversation patterns |

## Reproducing

Python 3.11 with `pip install -r requirements.txt`. Notebooks run from `notebooks/`, the discourse scripts from `discourse_analysis/scripts/` in the order given in `discourse_analysis/README.md`, the retrieval metrics with `python evaluation/results/retrieval/recompute_metrics.py`.

## Data

Participants are identified by a pseudonymous account id.

`data/final/`

- `user_interaction.csv`: every turn of the 229 conversations (user, chatbot, and system rows), German original and English translation, the stance module's label, and the message id.
- `annotations_export.csv`: the manual annotation of the 1,098 user turns (stance or dialogue act) and the conversations excluded from the analysis.
- `participant_demographics.csv`: one row per participant with condition, completion status, and the pre- and post-survey answers; `question_labels.csv` is the codebook.

`data/database/`: the chatbot's database tables the notebooks join on: `user.csv`, `survey.csv`, `question.csv`, `user_vote.csv` (the VAA answers), `chat_message.csv` (messages with the stance module's probabilities), `chat_retrieval.csv` (guardrail decisions per user message), `chat_predefined_message.csv` (the two suggested opening questions). `party_names.txt` and `candidate_names.txt` are the name lists used by the discourse scripts.

## Citation

If you use the data or code, please cite the paper:

```bibtex
@inproceedings{baezsantamaria2026dialogue,
  author    = {B{\'a}ez Santamar{\'i}a, Selene and Salvisberg, Patric and Bachmann, Fynn},
  title     = {Comparing Dialogue Management Strategies with a Modular Platform for Conversational Agent Voting Advice Applications},
  booktitle = {CONVERSATIONS 2026},
  series    = {Lecture Notes in Computer Science},
  publisher = {Springer},
  year      = {2026},
  doi       = {10.1007/placeholder}
}
```
