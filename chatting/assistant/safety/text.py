"""Helpers for cleaning untrusted text."""

import re
import unicodedata

# Control characters except tab and newline. These can hide text in
# terminals and logs (for example ANSI escape sequences).
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


def clean_text(
    text: str,
    max_length: int,
) -> str:
    """
    Normalize untrusted text for safe use.

    - Unicode is normalized (NFKC), so look-alike characters
      cannot be used to dodge pattern checks.
    - Control characters are removed.
    - Surrounding whitespace is stripped.
    - The result is cut to max_length characters.
    """

    if max_length <= 0:
        raise ValueError("max_length must be greater than zero.")

    text = unicodedata.normalize("NFKC", text)
    text = _CONTROL_CHARACTERS.sub("", text)
    text = text.strip()

    return text[:max_length]
