from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent

REPO_ROOT = PROJECT_ROOT.parent
DATA_DIR = REPO_ROOT / "data"
PARTICIPANT_DATA_PATH = DATA_DIR / "final" / "participant_demographics.csv"
INTERACTIONS_PATH = DATA_DIR / "final" / "user_interaction.csv"
MANUAL_ANNOTATIONS_PATH = DATA_DIR / "final" / "annotations_export.csv"

# unique party/candidate names, extracted from the smartvote candidate table
PARTY_NAMES_PATH = DATA_DIR / "party_names.txt"
CANDIDATE_NAMES_PATH = DATA_DIR / "candidate_names.txt"

TRANSCRIPTS_DIR = PROJECT_ROOT / "transcripts"
RESULTS_DIR = PROJECT_ROOT / "results"

TURN_TAGS_PATH = RESULTS_DIR / "turn_tags.csv"
JUDGE_TAGS_PATH = RESULTS_DIR / "llm_judgments.csv"
SEQUENCE_TAGS_PATH = RESULTS_DIR / "sequence_tags.csv"
SCALAR_METRICS_PATH = RESULTS_DIR / "overall_comparison.csv"
NGRAMS_PATH = RESULTS_DIR / "top_ngrams.csv"
TOP_MESSAGES_PATH = RESULTS_DIR / "top_user_messages.csv"
FOLLOW_UP_QUESTIONS_PATH = RESULTS_DIR / "follow_up_questions.csv"
USER_QUESTIONS_PATH = RESULTS_DIR / "user_questions.csv"

TOP_N_MESSAGES = 20
TOP_N_NGRAMS = 5
OUTPUT_SEPARATOR = ";"

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3.6:35b-a3b"

# MIDAS-inspired taxonomy, agent turns only
DIALOGUE_ACT_LABELS = ["yes_no_question", "open_question", "opinion", "statement", "answer"]

# manualannotation labels that mark a user turn as a question
QUESTION_MANUAL_LABELS = {"content_q", "meta_q"}

# classify the question's form only
QUESTION_FORM_LABELS = ["yes_no_question", "open_question"]

# user-turn categories from the manual annotation
# message carries a stance -> "opinion"
# "0" -> "general_statement"
MANUAL_USER_ACT_LABELS = ["opinion", "general_statement", "content_q", "meta_q", "command", "answer"]

# template opening questions in assistant condition
SUGGESTED_OPENINGS = ["what are the arguments for and against raising the retirement age?",
                      "what are the positions of the various parties on this?"]

# template refusal for guardrails
GUARDRAIL_REFUSAL_PHRASES = [
    "lies outside my subject area",
    "not allowed to express an opinion of my own",
    "i cannot comment on this topic",
    "i do not give voting recommendations",
]

ATTRIBUTION_CUES = {
    "argues", "argue", "favours", "favors", "favor", "rejects", "reject", "calls for", "call for",
    "prefers", "prefer", "wants", "want", "demands", "demand", "supports", "support", "opposes",
    "oppose", "position", "stance",
}

YES_NO_QUESTION_STARTERS = {
    "am", "is", "are", "was", "were", "do", "does", "did", "have", "has", "had",
    "can", "could", "will", "would", "shall", "should", "might", "may", "must",
}

WH_QUESTION_STARTERS = {"what", "which", "who", "whom", "whose", "when", "where", "why", "how"}

# leading connector phrases that get stripped before classifying a follow-up question
QUESTION_FILLER_PREFIXES = [
    "or", "and", "so", "well", "now", "also",
    "in your opinion", "in your view", "for example", "for instance",
]

# abbreviations that shouldn't be mistaken for a sentence boundary
SENTENCE_SPLIT_ABBREVIATIONS = ["e.g", "i.e", "etc"]

BOT_ADDRESS_WORDS = {"you", "your", "yourself"}

FRUSTRATION_LEXICON = {
    "useless", "annoying", "pointless", "waste of time", "not helpful", "unhelpful",
    "frustrating", "ridiculous", "stupid", "boring", "again and again", "same thing",
    "don't understand", "doesn't understand", "not answering",
}

HEDGE_LEXICON = {
    "might", "may", "could", "possibly", "perhaps", "likely", "unlikely", "seems", "seem",
    "appears", "appear", "suggest", "suggests", "tend to", "tends to", "generally", "typically",
    "often", "sometimes", "somewhat", "relatively", "roughly", "approximately", "arguably",
    "presumably", "in some cases", "to some extent", "it is possible", "not necessarily",
}

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "so", "because", "as", "of", "at", "by", "for",
    "with", "about", "against", "between", "into", "through", "to", "from", "in", "on", "is",
    "are", "was", "were", "be", "been", "being", "am", "do", "does", "did", "doing", "have",
    "has", "had", "having", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their", "this", "that", "these", "those",
    "what", "which", "who", "whom", "would", "could", "should", "will", "can", "not",
    "than", "too", "very", "just", "there", "here", "when", "where", "why", "how",
}
