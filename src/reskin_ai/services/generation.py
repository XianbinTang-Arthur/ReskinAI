from __future__ import annotations

import hashlib


def build_prompt_text(preference: dict[str, object]) -> str:
    parts = [
        str(preference.get("style", "")),
        ",".join(preference.get("motifs", [])),
        ",".join(preference.get("meaning_keywords", [])),
        ",".join(preference.get("avoid_list", [])),
        str(preference.get("mood", "")),
    ]
    return " | ".join(parts)


def compute_prompt_hash(prompt_text: str) -> str:
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

