"""Computes the automatic 'Overall comparison of conditions' metrics from analysis_plan.md."""
import re
from collections import Counter

import pandas as pd

from utils.constants import DIALOGUE_ACT_LABELS, MANUAL_USER_ACT_LABELS, NGRAMS_PATH, OUTPUT_SEPARATOR, \
    PARTICIPANT_DATA_PATH, QUESTION_FORM_LABELS, RESULTS_DIR, SCALAR_METRICS_PATH, SEQUENCE_TAGS_PATH, STOPWORDS, \
    SUGGESTED_OPENINGS, TOP_MESSAGES_PATH, TOP_N_MESSAGES, TOP_N_NGRAMS
from utils.helpers import add_conversation_metadata, drop_system_rows, ensure_dir, excluded_conversations_by_condition, \
    load_interactions, load_judgments, load_turn_tags


def word_tokens(text):
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.casefold())


def ngrams(tokens, n):
    return list(zip(*[tokens[i:] for i in range(n)]))


def drop_stopwords(tokens):
    return [token for token in tokens if token not in STOPWORDS]


def turns_before_voting(df, conversation_ids, condition):
    # counts turns before voting
    counts = []
    for conversation_id in conversation_ids:
        conversation = df[df["conversation_id"] == conversation_id]
        vote_rows = conversation[conversation["content"] == "vote_prompt"]

        if vote_rows.empty:
            if condition == "Assistant" and conversation["status"].iloc[0] == "COMPLETE":
                # assume voting happened at the end in completed assistant conversations
                counts.append(len(conversation))
            else:
                continue
        # voting is marked by the first vote_prompt
        else:
            first_vote_turn = vote_rows["turn_index"].min()
            counts.append((conversation["turn_index"] < first_vote_turn).sum())
    return pd.Series(counts)


def tokens_per_turn(texts):
    return texts.apply(lambda text: len(word_tokens(text))).mean()


def mattr(texts, window=50):
    # moving-average type-token ratio: average TTR over sliding windows of fixed size,
    # so it isn't confounded by corpus size the way a raw corpus-level TTR is
    tokens = word_tokens(" ".join(texts))
    if not tokens:
        return 0.0
    if len(tokens) <= window:
        return len(set(tokens)) / len(tokens)
    ratios = [len(set(tokens[i:i + window])) / window for i in range(len(tokens) - window + 1)]
    return sum(ratios) / len(ratios)


def repeated_message_stats(user_rows):
    # messages that appear more than 3 times: their share of all messages, and their breakdown by act
    counts = user_rows["message_casefold"].value_counts()
    repeated_messages = set(counts[counts > 3].index)
    is_repeated = user_rows["message_casefold"].isin(repeated_messages)
    total = len(user_rows)

    type_counts = user_rows.loc[is_repeated, "manual_dialogue_act"].value_counts()
    type_total = type_counts.sum()

    return {
        "pct_repeated_messages": (is_repeated.sum() / total * 100) if total else 0.0,
        "n_distinct_repeated_messages": len(repeated_messages),
        **{
            f"pct_repeated_{label}": (type_counts.get(label, 0) / type_total * 100) if type_total else 0.0
            for label in MANUAL_USER_ACT_LABELS
        },
    }


def pct_conversations_with_flag(group, column):
    flagged = group.groupby("conversation_id")[column].any()
    return flagged.mean() * 100 if len(flagged) else 0.0


def act_percentages(group, role, column, labels, suffix):
    acts = group.loc[group["role"] == role, column].dropna()
    counts = acts.value_counts()
    total = len(acts)
    return {
        f"pct_{label}_{suffix}": (counts.get(label, 0) / total * 100) if total else 0.0
        for label in labels
    }


def summarize_condition(condition, df, messages, invalid_counts):
    group = messages[messages["condition"] == condition]
    conversation_ids = group["conversation_id"].unique()
    turns_per_conversation = group.groupby("conversation_id").size()

    user_rows = group[group["role"] == "user"].copy()
    user_rows["message_casefold"] = user_rows["content_en"].str.casefold()
    typed_user_rows = user_rows[~user_rows["message_casefold"].isin(SUGGESTED_OPENINGS)]

    user_texts = user_rows["content_en"]
    agent_texts = group.loc[group["role"] == "assistant", "content_en"]
    typed_user_texts = typed_user_rows["content_en"]

    user_tokens = drop_stopwords(word_tokens(" ".join(typed_user_texts)))
    top_ngrams = {n: Counter(ngrams(user_tokens, n)).most_common(TOP_N_NGRAMS) for n in (1, 2, 3)}
    top_user_messages = typed_user_texts.str.casefold().value_counts().head(TOP_N_MESSAGES)

    summary = {
        "condition": condition,
        "n_unique_users": group["username"].nunique(),
        "n_valid_conversations": len(conversation_ids),
        "n_invalid_conversations": invalid_counts.get(condition, 0),
        "avg_turns_per_conversation": turns_per_conversation.mean(),
        "avg_tokens_per_turn_user": tokens_per_turn(typed_user_texts),
        "avg_tokens_per_turn_agent": tokens_per_turn(agent_texts),
        "avg_turns_before_voting": turns_before_voting(df, conversation_ids, condition).mean(),
        "mattr_user": mattr(typed_user_texts),
        "mattr_agent": mattr(agent_texts),
        **repeated_message_stats(typed_user_rows),
        "turn_level": "",
        **act_percentages(group, "user", "manual_dialogue_act", MANUAL_USER_ACT_LABELS, "user"),
        **act_percentages(group, "user", "dialogue_act", QUESTION_FORM_LABELS, "user_llm"),
        **act_percentages(group, "assistant", "dialogue_act", DIALOGUE_ACT_LABELS, "agent"),
        "conversation_level": "",
        "pct_topic_drift": pct_conversations_with_flag(group, "topic_drift"),
        "pct_context_break": pct_conversations_with_flag(group, "context_break"),
        "pct_guardrail_refusal": pct_conversations_with_flag(group, "guardrail_refusal"),
        "pct_stance_leak": pct_conversations_with_flag(group, "stance_leak"),
        "pct_directive_framing": pct_conversations_with_flag(group, "directive_framing"),
        "pct_source_attribution": pct_conversations_with_flag(group, "source_attribution"),
        "pct_hedging": pct_conversations_with_flag(group, "hedging"),
        "pct_disengagement_sequence": pct_conversations_with_flag(group, "disengagement_sequence"),
        "pct_unprompted_reflection": pct_conversations_with_flag(group, "unprompted_reflection"),
        "pct_prompted_reflection": pct_conversations_with_flag(group, "prompted_reflection"),
        "pct_drift_compliance_sequence": pct_conversations_with_flag(group, "drift_compliance_sequence"),
        "pct_resistance_sequence": pct_conversations_with_flag(group, "resistance_sequence"),
    }
    return summary, top_ngrams, top_user_messages, len(typed_user_texts)


def ngrams_to_rows(condition, top_ngrams):
    rows = []
    for n, grams in top_ngrams.items():
        for gram, count in grams:
            rows.append({"condition": condition, "n": n, "ngram": " ".join(gram), "count": count})
    return rows


def top_messages_to_rows(condition, top_user_messages, total_typed_user_messages):
    return [
        {
            "condition": condition,
            "message": message,
            "count": count,
            "pct": (count / total_typed_user_messages * 100) if total_typed_user_messages else 0.0,
        }
        for message, count in top_user_messages.items()
    ]


def main():
    df = load_interactions()
    participant_status = pd.read_csv(PARTICIPANT_DATA_PATH)[["username", "status"]]
    df = df.merge(participant_status, on="username", how="left")
    df = add_conversation_metadata(df)

    messages = drop_system_rows(df)
    judgments = load_judgments()
    messages = messages.merge(judgments, on="message_id", how="left")

    turn_tags = load_turn_tags()
    turn_tags = turn_tags[["message_id", "guardrail_refusal", "source_attribution", "hedging",
                            "manual_dialogue_act"]]
    messages = messages.merge(turn_tags, on="message_id", how="left")

    sequence_tags = pd.read_csv(SEQUENCE_TAGS_PATH, sep=OUTPUT_SEPARATOR)
    sequence_tags = sequence_tags[["message_id", "disengagement_sequence", "unprompted_reflection",
                                    "prompted_reflection", "drift_compliance_sequence", "resistance_sequence"]]
    messages = messages.merge(sequence_tags, on="message_id", how="left")

    invalid_counts = excluded_conversations_by_condition()

    summaries = []
    ngram_rows = []
    top_message_rows = []
    for condition in df["condition"].unique():
        summary, top_ngrams, top_user_messages, total_typed_user_messages = summarize_condition(
            condition, df, messages, invalid_counts)
        summaries.append(summary)
        ngram_rows += ngrams_to_rows(condition, top_ngrams)
        top_message_rows += top_messages_to_rows(condition, top_user_messages, total_typed_user_messages)

    ensure_dir(RESULTS_DIR)
    pd.DataFrame(summaries).round(2).to_csv(SCALAR_METRICS_PATH, index=False)
    pd.DataFrame(ngram_rows).to_csv(NGRAMS_PATH, index=False)
    pd.DataFrame(top_message_rows).round(2).to_csv(TOP_MESSAGES_PATH, index=False)


if __name__ == "__main__":
    main()