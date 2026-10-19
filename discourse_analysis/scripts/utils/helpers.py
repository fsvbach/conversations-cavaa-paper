import csv

import pandas as pd

from utils.constants import GUARDRAIL_REFUSAL_PHRASES, INTERACTIONS_PATH, JUDGE_TAGS_PATH, MANUAL_ANNOTATIONS_PATH, \
    OUTPUT_SEPARATOR, TURN_TAGS_PATH


def load_csv_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def conversation_id_column(df):
    return df["username"] + "_" + df["condition"] + "_" + df["topic"]


def load_excluded_conversation_ids():
    # conversations manually flagged as useless
    raw = pd.read_csv(INTERACTIONS_PATH)
    all_ids = set(conversation_id_column(raw).unique())

    annotations = pd.read_csv(MANUAL_ANNOTATIONS_PATH)
    flagged_ids = set(conversation_id_column(annotations[annotations["conversation_excluded"] == 1]).unique())
    annotated_ids = set(conversation_id_column(annotations).unique())

    return flagged_ids | (all_ids - annotated_ids)


def excluded_conversations_by_condition():
    raw = pd.read_csv(INTERACTIONS_PATH)
    excluded_ids = load_excluded_conversation_ids()
    excluded = raw[conversation_id_column(raw).isin(excluded_ids)]
    unique_conversations = excluded.drop_duplicates(subset=["username", "condition", "topic"])
    return unique_conversations["condition"].value_counts()


def load_interactions():
    df = pd.read_csv(INTERACTIONS_PATH)
    df["content_en"] = df["content_en"].fillna("")
    excluded_ids = load_excluded_conversation_ids()
    return df[~conversation_id_column(df).isin(excluded_ids)]


def drop_system_rows(df):
    return df[df["role"] != "system"]


def add_conversation_metadata(df):
    df = df.copy()
    df["conversation_id"] = conversation_id_column(df)
    df = df.sort_values(["conversation_id", "createdOn"]).reset_index(drop=True)
    df["turn_index"] = df.groupby("conversation_id").cumcount() + 1
    return df


def contains_any(text, phrases):
    text = text.casefold()
    return any(phrase in text for phrase in phrases)


def tag_guardrail_refusal(text):
    return contains_any(text, GUARDRAIL_REFUSAL_PHRASES)


def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)


def load_judgments():
    return pd.read_csv(JUDGE_TAGS_PATH, sep=OUTPUT_SEPARATOR)


def load_turn_tags():
    return pd.read_csv(TURN_TAGS_PATH, sep=OUTPUT_SEPARATOR)


def load_manual_annotations():
    annotations = pd.read_csv(MANUAL_ANNOTATIONS_PATH)
    return annotations[["message_id", "stance", "label"]].rename(
        columns={"stance": "manual_stance", "label": "manual_label"})