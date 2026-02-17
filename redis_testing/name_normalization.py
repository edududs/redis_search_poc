from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from re import Pattern

MAX_NAME_SEARCH_LENGTH = 200

_NON_ALNUM_RE = re.compile(r"[^A-Z0-9]+")

STOP_WORDS: tuple[Pattern[str], ...] = (
    re.compile(r"^(?:DE|DA|DO|PARA|COM|E|OU|O|A|OS|AS)$"),
    re.compile(r"^(?:KG|UNID|UND|PT|ML|G|L|M|CM|METRO|LITRO|LITROS|LATA|X)$"),
    re.compile(r"^(?:PACOTE|UNIDADE|SEM)$"),
    re.compile(r"^\d+$"),
    re.compile(r"^\d+[A-Z]+$"),  # Remove números seguidos de unidades: 1L, 200ml, etc.
)


@lru_cache(maxsize=2048)
def _strip_accents(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )


def normalize_name_for_search(
    name: str,
    *,
    stopwords: tuple[Pattern[str], ...] = STOP_WORDS,
) -> str:
    """Normalize product names for consistent full-text lookup."""
    if not name:
        return ""

    normalized = _strip_accents(name).upper()
    normalized = _NON_ALNUM_RE.sub(" ", normalized)

    seen_tokens: set[str] = set()
    output_tokens: list[str] = []
    for token in normalized.split():
        if len(token) <= 1:
            continue
        if any(pattern.fullmatch(token) for pattern in stopwords):
            continue
        if token in seen_tokens:
            continue
        seen_tokens.add(token)
        output_tokens.append(token)

    return " ".join(output_tokens)[:MAX_NAME_SEARCH_LENGTH]
