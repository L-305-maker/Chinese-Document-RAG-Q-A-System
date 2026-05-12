import re
from typing import Dict, Any


class PromptValidator:
    def __init__(self,max_length: int = 1000,garbled_threshold: float = 0.5,):
        self.max_length = max_length
        self.garbled_threshold = garbled_threshold

        self.garbled_patterns = [
            "�",
            "锟斤拷",
            "Ã",
            "Â",
            "¤",
            "½",
            "¥",
            "æ",
            "ç",
            "è",
            "å",
            "ï¼",
            "ã",
        ]

    def validate(self, prompt: str) -> Dict[str, Any]:
        result = {
            "is_valid": True,
            "score": 0.0,
            "reasons": [],
            "normalized_prompt": None,
        }

        if prompt is None:
            result["is_valid"] = False
            result["score"] = 1.0
            result["reasons"].append("prompt_is_none")
            return result

        prompt = prompt.strip()

        if len(prompt) == 0:
            result["is_valid"] = False
            result["reasons"].append("empty_prompt")
            return result

        if len(prompt) > self.max_length:
            result["is_valid"] = False
            result["reasons"].append("prompt_too_long")
            return result

        garbled_score = self._compute_garbled_score(prompt)

        if garbled_score >= self.garbled_threshold:
            result["is_valid"] = False
            result["score"] = garbled_score
            result["reasons"].append("prompt_may_be_garbled")
            return result

        result["normalized_prompt"] = prompt
        return result

    def _compute_garbled_score(self, text: str) -> float:
        length = max(len(text), 1)
        score = 0.0

        garbled_hit_count = sum(text.count(p) for p in self.garbled_patterns)

        if garbled_hit_count > 0:
            score += min(0.5, garbled_hit_count * 0.15)

        non_printable_count = sum(1 for ch in text if not ch.isprintable())
        non_printable_ratio = non_printable_count / length

        if non_printable_ratio > 0.05:
            score += 0.3

        symbol_count = sum(
            1 for ch in text
            if not ch.isalnum()
            and not ("\u4e00" <= ch <= "\u9fff")
            and not ch.isspace()
        )

        symbol_ratio = symbol_count / length

        if length >= 10 and symbol_ratio > 0.5:
            score += 0.3

        if re.search(r"(.)\1{8,}", text):
            score += 0.25

        unique_char_ratio = len(set(text)) / length

        if length >= 20 and unique_char_ratio < 0.15:
            score += 0.25

        return min(score, 1.0)