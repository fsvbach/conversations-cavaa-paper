"""Computes the automatic 'Sequence-level' tags from analysis_plan.md."""
import pandas as pd

from utils.constants import OUTPUT_SEPARATOR, RESULTS_DIR, SEQUENCE_TAGS_PATH
from utils.helpers import add_conversation_metadata, drop_system_rows, ensure_dir, load_interactions, \
    load_judgments, load_manual_annotations, load_turn_tags, tag_guardrail_refusal

QUESTION_DIALOGUE_ACTS = {"yes_no_question", "open_question"}
MANUAL_ANSWER_ACTS = {"answer", "opinion"}


def tag_disengagement_sequence(conversation):
    # the conversation's very last turn is an unanswered guardrail refusal
    last_turn = conversation.sort_values("turn_index").iloc[-1]
    is_unanswered_refusal = last_turn["role"] == "assistant" and tag_guardrail_refusal(last_turn["content_en"])
    flags = pd.Series(False, index=conversation.index)
    if is_unanswered_refusal:
        flags[last_turn.name] = True
    return flags


def tag_reflection(df):
    previous_dialogue_act = df.groupby("conversation_id")["dialogue_act"].shift(1)
    # user expresses a stance
    is_user_opinion = (df["role"] == "user") & df["manual_stance"].notna()
    # "prompted" if the previous turn asked a question, "unprompted" otherwise
    is_prompted = previous_dialogue_act.isin(QUESTION_DIALOGUE_ACTS)
    df["unprompted_reflection"] = is_user_opinion & ~is_prompted
    df["prompted_reflection"] = is_user_opinion & is_prompted
    return df


def tag_drift_compliance_sequence(df):
    # a user turn drifts topic, and the agent's very next turn follows along rather than redirecting back
    previous_role = df.groupby("conversation_id")["role"].shift(1)
    previous_topic_drift = df.groupby("conversation_id")["topic_drift"].shift(1)
    df["drift_compliance_sequence"] = (
        (df["role"] == "assistant")
        & (previous_role == "user")
        & (previous_topic_drift == True)
        & (df["topic_drift"] == True)
    )
    return df


def tag_resistance_sequence(df):
    # user's turn right after an agent follow-up question doesn't answer it
    previous_follow_up = df.groupby("conversation_id")["follow_up"].shift(1)
    df["resistance_sequence"] = (
        (df["role"] == "user")
        & (previous_follow_up == True)
        & ~df["manual_dialogue_act"].isin(MANUAL_ANSWER_ACTS)
    )
    return df


def main():
    df = load_interactions()
    df = add_conversation_metadata(df)
    df = drop_system_rows(df).copy()

    judgments = load_judgments()
    df = df.merge(judgments[["message_id", "dialogue_act", "topic_drift"]], on="message_id", how="left")

    turn_tags = load_turn_tags()
    df = df.merge(turn_tags[["message_id", "follow_up", "manual_dialogue_act"]], on="message_id", how="left")

    manual_annotations = load_manual_annotations()
    df = df.merge(manual_annotations[["message_id", "manual_stance"]], on="message_id", how="left")

    disengagement_flags = [tag_disengagement_sequence(conversation) for _, conversation in df.groupby("conversation_id")]
    df["disengagement_sequence"] = pd.concat(disengagement_flags)

    df = tag_reflection(df)
    df = tag_drift_compliance_sequence(df)
    df = tag_resistance_sequence(df)

    output = df[["message_id", "conversation_id", "condition", "disengagement_sequence", "unprompted_reflection",
                 "prompted_reflection", "drift_compliance_sequence", "resistance_sequence"]]
    ensure_dir(RESULTS_DIR)
    output.to_csv(SEQUENCE_TAGS_PATH, index=False, sep=OUTPUT_SEPARATOR)


if __name__ == "__main__":
    main()