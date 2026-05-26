import re
import uuid
from difflib import SequenceMatcher
from typing import Dict, Any, List


def new_run_id() -> str:
    return str(uuid.uuid4())


def ensure_outputs_bucket(outputs: Dict[str, Any], hat: str, role: str) -> None:
    if hat not in outputs:
        outputs[hat] = {}
    if role not in outputs[hat]:
        outputs[hat][role] = []


def uniq_extend(target: List[str], items: List[str]) -> None:
    """
    Keeps backward compatibility with the previous exact-match deduplication.
    """
    seen = set(target)
    for x in items or []:
        x = (x or "").strip()
        if x and x not in seen:
            target.append(x)
            seen.add(x)


def split_bullet_items(value: Any) -> List[str]:
    """
    Splits LLM-generated bullet-like content into clean individual items.

    Handles:
    - arrays of strings
    - newline bullets
    - inline bullet symbols
    - numbered bullets
    - semicolon-separated lists
    """

    if not value:
        return []

    if isinstance(value, list):
        items: List[str] = []
        for item in value:
            items.extend(split_bullet_items(item))
        return items

    text = str(value).strip()
    if not text:
        return []

    # Convert inline bullet symbols into line breaks.
    text = re.sub(r"\s*[•]\s*", "\n", text)

    # Convert numbered inline bullets into line breaks:
    # "1. item 2. item" -> "1. item\n2. item"
    text = re.sub(r"\s+(?=\d+[\.\)]\s+)", "\n", text)

    candidates: List[str] = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Remove common bullet prefixes.
        line = re.sub(r"^[-*•]\s*", "", line)
        line = re.sub(r"^\d+[\.\)]\s*", "", line)
        line = line.strip()

        if not line:
            continue

        # Split semicolon-separated lists when they clearly contain several ideas.
        if ";" in line:
            parts = [p.strip() for p in line.split(";") if p.strip()]
            if len(parts) > 1:
                candidates.extend(parts)
            else:
                candidates.append(line)
        else:
            candidates.append(line)

    cleaned: List[str] = []

    for item in candidates:
        item = item.strip(" -•;\n\t")
        if item:
            cleaned.append(item)

    return cleaned


def normalize_item(value: str) -> str:
    """
    Normalizes text to improve duplicate detection.

    This is intentionally lightweight and deterministic.
    It avoids external dependencies and embeddings.
    """

    text = (value or "").lower().strip()

    # Remove bullet/numbering leftovers.
    text = re.sub(r"^\d+[\.\)]\s*", "", text)
    text = re.sub(r"^[-*•]\s*", "", text)

    # Normalize punctuation and whitespace.
    text = re.sub(r"[^a-z0-9áéíóúüñç\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Remove very common filler words that create false differences.
    stopwords = {
        "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "with",
        "by", "from", "among", "during", "how", "what", "which", "who",
        "will", "we", "our", "their", "this", "that", "these", "those",
        "do", "does", "can", "could", "should", "would",
        "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o",
        "de", "del", "para", "por", "en", "con", "durante", "como", "qué",
        "cual", "cuál", "quién", "este", "esta", "estos", "estas",
    }

    tokens = [token for token in text.split() if token not in stopwords]

    return " ".join(tokens)


def are_similar_items(a: str, b: str, threshold: float = 0.82) -> bool:
    """
    Returns True when two items are probably the same idea.

    Uses:
    - exact normalized match
    - token containment
    - SequenceMatcher similarity
    """

    na = normalize_item(a)
    nb = normalize_item(b)

    if not na or not nb:
        return False

    if na == nb:
        return True

    tokens_a = set(na.split())
    tokens_b = set(nb.split())

    if not tokens_a or not tokens_b:
        return False

    overlap = len(tokens_a & tokens_b)
    smaller = min(len(tokens_a), len(tokens_b))

    # Catches cases where one sentence is a slightly expanded version of another.
    if smaller >= 4 and overlap / smaller >= 0.80:
        return True

    return SequenceMatcher(None, na, nb).ratio() >= threshold


def uniq_extend_semantic(
    target: List[str],
    items: List[str],
    threshold: float = 0.82,
    max_items: int | None = None,
) -> None:
    """
    Extends a list while removing exact and near-duplicate items.
    """

    for raw_item in items or []:
        item = str(raw_item or "").strip()

        if not item:
            continue

        exists = any(are_similar_items(item, existing, threshold=threshold) for existing in target)

        if not exists:
            target.append(item)

        if max_items is not None and len(target) >= max_items:
            break


def consolidate_items(
    items: List[str],
    max_items: int = 12,
    threshold: float = 0.82,
) -> List[str]:
    """
    Produces a clean, deduplicated, capped list from raw LLM items.
    """

    consolidated: List[str] = []
    uniq_extend_semantic(
        consolidated,
        split_bullet_items(items),
        threshold=threshold,
        max_items=max_items,
    )
    return consolidated