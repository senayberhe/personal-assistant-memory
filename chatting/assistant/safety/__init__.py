"""
Safety checks shared across the assistant.

- sensitive_data: find and redact secrets (API keys, passwords,
  card numbers, ...) so they are never stored or logged.
- text: clean and bound untrusted text before it is used.
"""

from assistant.safety.sensitive_data import (
    SensitiveDataDetector,
    SensitiveFinding,
)
from assistant.safety.text import clean_text

__all__ = [
    "SensitiveDataDetector",
    "SensitiveFinding",
    "clean_text",
]
