"""Computes the automatic turn-level tags from analysis_plan.md."""
import re

import pandas as pd

from utils.constants import ATTRIBUTION_CUES, BOT_ADDRESS_WORDS, CANDIDATE_NAMES_PATH, FOLLOW_UP_QUESTIONS_PATH, \
    FRUSTRATION_LEXICON, HEDGE_LEXICON, OUTPUT_SEPARATOR, PARTY_NAMES_PATH, QUESTION_FILLER_PREFIXES, RESULTS_DIR, \
    SENTENCE_SPLIT_ABBREVIATIONS, TURN_TAGS_PATH, USER_QUESTIONS_PATH, WH_QUESTION_STARTERS, \
    YES_NO_QUESTION_STARTERS
from utils.helpers import contains_any, drop_system_rows, ensure_dir, load_interactions, load_manual_annotations, \
    tag_guardrail_refusal

SENTENCE_SPLIT_PATTERN = re.compile(
    # the trigger period is part of the abbreviation, so it must be included in the lookbehind
    "".join(rf"(?<!\b{re.escape(a)}\.)" for a in SENTENCE_SPLIT_ABBREVIATIONS) + r"(?<=[.!?])\s+"
)
FILLER_PREFIX_PATTERN = re.compile(
    r"^(" + "|".join(re.escape(p) for p in QUESTION_FILLER_PREFIXES) + r")\b[,\s]*", re.IGNORECASE
)


def load_names(path):
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line]


def name_pattern(names):
    # one regex that matches any of the given names as a whole word
    escaped = [re.escape(name) for name in names]
    return re.compile(r"\b(" + "|".join(escaped) + r")\b", re.IGNORECASE)


def tag_first_person(text):
    return bool(re.search(r"\bI\b", text))


def tag_source_attribution(text, party_pattern):
    if "according to" in text.casefold():
        return True
    return bool(party_pattern.search(text)) and contains_any(text, ATTRIBUTION_CUES)


def tag_hedging(text):
    return contains_any(text, HEDGE_LEXICON)


def tag_question_type(text, mentions_party_or_candidate):
    if not text.strip().endswith("?"):
        return "not_applicable"
    if mentions_party_or_candidate:
        return "content"
    if re.search(r"\b(" + "|".join(BOT_ADDRESS_WORDS) + r")\b", text, re.IGNORECASE):
        return "meta"
    return "content"


def tag_frustration(text):
    return contains_any(text, FRUSTRATION_LEXICON)


def to_manual_dialogue_act(row):
    # message carries a manually annotated stance -> "opinion"; "0" -> "general_statement"; else the label itself
    if pd.notna(row["manual_stance"]):
        return "opinion"
    if row["manual_label"] == "0":
        return "general_statement"
    return row["manual_label"]


def tag_follow_up(row):
    is_interview = row["condition"] == "Interview"
    is_agent = row["role"] == "assistant"
    ends_in_question = row["content_en"].strip().endswith("?")
    return is_interview and is_agent and ends_in_question


def extract_question(text):
    # the question is the last sentence of the turn, ending in "?"
    sentences = SENTENCE_SPLIT_PATTERN.split(text.strip())
    return sentences[-1] if sentences else ""


def strip_filler_prefix(question):
    # repeatedly drops leading connectors ("Or", "In your opinion, ", ...) to reach the real start
    stripped = question
    while True:
        without_prefix = FILLER_PREFIX_PATTERN.sub("", stripped, count=1)
        if without_prefix == stripped:
            return stripped
        stripped = without_prefix


def classify_question(question):
    question = strip_filler_prefix(question)
    first_word_match = re.match(r"[a-zA-Z']+", question)
    if not first_word_match:
        return "other"
    first_word = first_word_match.group().casefold()
    if first_word in WH_QUESTION_STARTERS:
        return "open_ended"
    if first_word in YES_NO_QUESTION_STARTERS:
        return "yes_no"
    return "other"


def save_question_counts(questions, path):
    questions = questions.copy()
    questions["question"] = questions["question"].str.casefold()
    counts = questions.value_counts().reset_index(name="count")
    counts = counts.sort_values("count", ascending=False)
    counts.to_csv(path, index=False, sep=OUTPUT_SEPARATOR)


def main():
    df = load_interactions()
    messages = drop_system_rows(df).copy()

    party_pattern = name_pattern(load_names(PARTY_NAMES_PATH))
    candidate_pattern = name_pattern(load_names(CANDIDATE_NAMES_PATH))

    messages["first_person"] = messages["content_en"].apply(tag_first_person)
    messages["party_mention"] = messages["content_en"].apply(lambda t: bool(party_pattern.search(t)))
    messages["candidate_mention"] = messages["content_en"].apply(lambda t: bool(candidate_pattern.search(t)))
    messages["guardrail_refusal"] = messages["content_en"].apply(tag_guardrail_refusal)
    messages["source_attribution"] = messages["content_en"].apply(
        lambda t: tag_source_attribution(t, party_pattern))
    messages["hedging"] = messages["content_en"].apply(tag_hedging)
    messages["question_type"] = messages.apply(
        lambda r: tag_question_type(r["content_en"], r["party_mention"] or r["candidate_mention"])
        if r["role"] == "user" else "not_applicable", axis=1)
    messages["frustration"] = messages.apply(
        lambda r: tag_frustration(r["content_en"]) if r["role"] == "user" else False, axis=1)
    messages["follow_up"] = messages.apply(tag_follow_up, axis=1)
    messages["follow_up_question"] = messages["content_en"].where(messages["follow_up"], "").apply(
        lambda t: extract_question(t) if t else "")
    messages["follow_up_question_type"] = messages["follow_up_question"].apply(
        lambda q: classify_question(q) if q else "")

    is_user_question = (messages["role"] == "user") & (messages["question_type"] != "not_applicable")
    messages["user_question"] = messages["content_en"].where(is_user_question, "").apply(
        lambda t: extract_question(t) if t else "")

    manual_annotations = load_manual_annotations()
    messages = messages.merge(manual_annotations, on="message_id", how="left")
    messages["manual_dialogue_act"] = messages.apply(to_manual_dialogue_act, axis=1)

    output = messages[
        ["message_id", "role", "content_en"] + ["first_person", "party_mention", "candidate_mention",
                                  "guardrail_refusal", "source_attribution", "hedging", "question_type",
                                  "frustration", "follow_up", "follow_up_question_type", "manual_dialogue_act",
                                  ]]

    ensure_dir(RESULTS_DIR)
    output.to_csv(TURN_TAGS_PATH, index=False, sep=OUTPUT_SEPARATOR)

    follow_up_questions = messages.loc[messages["follow_up"], ["follow_up_question", "follow_up_question_type"]]
    follow_up_questions = follow_up_questions.rename(
        columns={"follow_up_question": "question", "follow_up_question_type": "question_type"})
    save_question_counts(follow_up_questions, FOLLOW_UP_QUESTIONS_PATH)

    user_questions = messages.loc[messages["user_question"] != "", ["user_question", "question_type"]].copy()
    user_questions["question_form"] = user_questions["user_question"].apply(classify_question)
    user_questions = user_questions.rename(columns={"user_question": "question"})
    save_question_counts(user_questions, USER_QUESTIONS_PATH)


if __name__ == "__main__":
    main()
