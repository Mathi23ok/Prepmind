import json
import os
import re
from typing import Any

from openai import OpenAI

from schemas import Flashcard

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_answer(context: str, question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an exam assistant. Answer only from the provided context. "
                    "Keep the response clear, direct, and student-friendly. "
                    "Prefer short paragraphs or numbered points. Avoid markdown bold, bullet clutter, "
                    "and decorative formatting. If the answer is not present in the context, reply exactly: "
                    "'Not found in document'."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()


def _build_flashcards(items: list[dict[str, Any]]) -> list[Flashcard]:
    cards: list[Flashcard] = []

    for item in items:
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if question and answer:
            cards.append(Flashcard(question=question, answer=answer))

    return cards


def _extract_json_candidate(raw_content: str) -> str:
    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_content, flags=re.DOTALL)
    if fenced_match:
        return fenced_match.group(1).strip()

    object_match = re.search(r"(\{.*\})", raw_content, flags=re.DOTALL)
    if object_match:
        return object_match.group(1).strip()

    array_match = re.search(r"(\[.*\])", raw_content, flags=re.DOTALL)
    if array_match:
        return array_match.group(1).strip()

    return raw_content.strip()


def _parse_flashcards_from_json(raw_content: str) -> list[Flashcard]:
    candidate = _extract_json_candidate(raw_content)

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return []

    if isinstance(parsed, dict):
        flashcards = parsed.get("flashcards")
        if isinstance(flashcards, list):
            return _build_flashcards(flashcards)
        return []

    if isinstance(parsed, list):
        return _build_flashcards(parsed)

    return []


def _parse_flashcards_from_text(raw_content: str) -> list[Flashcard]:
    cards: list[Flashcard] = []

    matches = re.findall(
        r"(?:^|\n)(?:Q(?:uestion)?[:\-]\s*)(.*?)(?:\n)(?:A(?:nswer)?[:\-]\s*)(.*?)(?=\n(?:Q(?:uestion)?[:\-])|\Z)",
        raw_content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    for question, answer in matches:
        question = question.strip(" -\n\t")
        answer = answer.strip(" -\n\t")
        if question and answer:
            cards.append(Flashcard(question=question, answer=answer))

    return cards


def _parse_flashcards(raw_content: str) -> list[Flashcard]:
    raw_content = raw_content.strip()
    if not raw_content:
        return []

    json_cards = _parse_flashcards_from_json(raw_content)
    if json_cards:
        return json_cards

    return _parse_flashcards_from_text(raw_content)


def generate_flashcards(context: str) -> list[Flashcard]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Create exactly 5 revision flashcards from the provided content. "
                    'Return valid JSON in this shape: {"flashcards":[{"question":"...","answer":"..."}]}. '
                    "Do not include markdown fences, extra commentary, or any keys other than flashcards. "
                    "Keep questions crisp and answers concise but complete."
                ),
            },
            {
                "role": "user",
                "content": context,
            },
        ],
    )
    raw_content = (response.choices[0].message.content or "").strip()
    cards = _parse_flashcards(raw_content)

    if cards:
        return cards[:5]

    return [
        Flashcard(
            question="Flashcards unavailable",
            answer="The model returned an unexpected format. Please try generating them again.",
        )
    ]
