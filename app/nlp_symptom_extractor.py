
from __future__ import annotations

from typing import List


# Very simple keyword-based extractor (for demo only!)
# You can replace this by spaCy / transformers in future.
KEYWORDS = [
    "orange spots",
    "orange pustules",
    "yellow spots",
    "powdery",
    "powdery mildew",
    "brown streaks",
    "rust",
    "yellowing",
    "blight",
]


def extract_symptoms(text: str | None) -> List[str]:
    if not text:
        return []
    text_l = text.lower()
    found = []
    for kw in KEYWORDS:
        if kw in text_l:
            found.append(kw)
    # Also keep a short version of the text itself (truncated) as a generic symptom description
    if text.strip():
        found.append(text.strip()[:120])
    return list(dict.fromkeys(found))  # unique preserve order
