import re


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, chunk_size: int = 120) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []

    words = normalized.split(" ")
    return [
        " ".join(words[index:index + chunk_size])
        for index in range(0, len(words), chunk_size)
    ]
