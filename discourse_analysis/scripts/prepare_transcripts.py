"""Reconstructs one readable transcript per (username, condition, topic) conversation."""
import re
import shutil
from collections import defaultdict

from utils.constants import INTERACTIONS_PATH, TRANSCRIPTS_DIR
from utils.helpers import load_csv_rows, load_excluded_conversation_ids


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def group_conversations(rows):
    groups = defaultdict(list)
    for r in rows:
        key = (r["username"], r["condition"], r["topic"])
        groups[key].append(r)
    for turns in groups.values():
        turns.sort(key=lambda r: r["createdOn"])
    return groups


def write_transcripts(groups, excluded_ids):
    # avoid stale files if a conversation's status changes
    shutil.rmtree(TRANSCRIPTS_DIR, ignore_errors=True)  
    
    for (username, condition, topic), turns in groups.items():
        conv_dir = TRANSCRIPTS_DIR / slugify(condition) / slugify(topic)
        conv_dir.mkdir(parents=True, exist_ok=True)
        conversation_id = f"{username}_{condition}_{topic}"
        prefix = "INVALID_" if conversation_id in excluded_ids else ""
        out_path = conv_dir / f"{prefix}{username[:12]}.md"

        lines = [
            f"# {condition} / {topic} / user {username[:12]}",
            "",
        ]
        for i, r in enumerate(turns, 1):
            if r["role"] == "system":
                lines.append(f"**[{i}] SYSTEM ({r['content']})**")
            else:
                speaker = "USER" if r["role"] == "user" else "AGENT"
                lines.append(f"**[{i}] {speaker}**:")
                lines.append(r["content_en"].strip())
            lines.append("")
        out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows = load_csv_rows(INTERACTIONS_PATH)
    groups = group_conversations(rows)
    excluded_ids = load_excluded_conversation_ids()
    write_transcripts(groups, excluded_ids)


if __name__ == "__main__":
    main()