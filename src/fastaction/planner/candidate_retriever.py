from __future__ import annotations

from dataclasses import dataclass
import re

from fastaction.schemas import APIDefinition
from fastaction.schemas.common import text_value


@dataclass(frozen=True)
class Candidate:
    api: APIDefinition
    score: float
    reason: str


class CandidateRetriever:
    def retrieve(self, text: str, apis: list[APIDefinition], limit: int = 5) -> list[Candidate]:
        normalized = text.lower()
        candidates: list[Candidate] = []
        for api in apis:
            if api.status != "active":
                continue
            score = 0.0
            reasons: list[str] = []

            for keyword in api.intent.all_keywords():
                keyword_norm = keyword.lower()
                if keyword_norm and _phrase_matches(keyword_norm, normalized):
                    score += 2.0
                    reasons.append(f"keyword:{keyword}")

            for example in api.intent.all_examples():
                example_norm = example.lower()
                if example_norm and _phrase_matches(example_norm, normalized):
                    score += 3.0
                    reasons.append(f"example:{example}")

            name = text_value(api.name).lower()
            if name and any(part and part in normalized for part in name.split()):
                score += 0.5
                reasons.append("name")

            if score > 0:
                candidates.append(Candidate(api=api, score=score, reason=", ".join(reasons)))

        candidates.sort(key=lambda item: item.score, reverse=True)
        return candidates[:limit]


def _phrase_matches(phrase: str, text: str) -> bool:
    if phrase in text:
        return True
    compact_phrase = _compact_text(phrase)
    compact_text = _compact_text(text)
    if not compact_phrase:
        return False
    if compact_phrase in compact_text:
        return True
    if _has_cjk(compact_phrase) and len(compact_phrase) >= 3:
        return _ordered_cjk_match(compact_phrase, compact_text)
    return False


def _compact_text(value: str) -> str:
    return re.sub(r"[\s,，。.!！?？、:：;；\"'“”‘’（）()【】\\[\\]{}<>《》/-]+", "", value)


def _has_cjk(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def _ordered_cjk_match(phrase: str, text: str, max_gap: int = 4) -> bool:
    position = -1
    for char in phrase:
        next_position = text.find(char, position + 1)
        if next_position < 0:
            return False
        if position >= 0 and next_position - position > max_gap + 1:
            return False
        position = next_position
    return True
