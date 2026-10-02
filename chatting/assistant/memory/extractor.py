"""Rule-based detection of facts worth remembering."""

import re

# (pattern, memory_type). The first matching rule wins, so one
# message produces at most one memory.
_RULES: list[tuple[re.Pattern[str], str]] = [
    # "Remember that X" / "Please remember X": store just X.
    (
        re.compile(r"^(?:please\s+)?remember(?:\s+that)?\s+(?P<fact>.+)$", re.I),
        "instruction",
    ),
    (re.compile(r"\bmy favou?rite\b", re.I), "preference"),
    (re.compile(r"\bi (?:prefer|like|love|hate|dislike)\b", re.I), "preference"),
]


_FILLER_WORDS = {"that", "this", "it", "me"}


class MemoryExtractor:
    """Extracts at most one memory candidate from a user message."""

    def extract(
        self,
        user_text: str,
    ) -> list[dict]:

        text = user_text.strip()

        for pattern, memory_type in _RULES:
            match = pattern.search(text)

            if match is None:
                continue

            fact = (match.groupdict().get("fact") or text).strip()

            # "remember that" / "remember this" alone is not a fact.
            if not fact or fact.lower().rstrip(".!") in _FILLER_WORDS:
                return []

            # "remember that I prefer tea" is a preference.
            if memory_type == "instruction" and _RULES[2][0].search(fact):
                memory_type = "preference"

            return [
                {
                    "content": fact[0].upper() + fact[1:],
                    "memory_type": memory_type,
                }
            ]

        return []
