"""
Detect and redact sensitive data in free text.

Used to keep secrets out of long-term memory and out of log files.
Detection is pattern based: it catches common, well-structured
secrets with few false positives, but it is not a guarantee.
"""

import re
from dataclasses import dataclass

REDACTED = "[REDACTED]"


@dataclass(frozen=True)
class SensitiveFinding:
    """One piece of sensitive data found in a text."""

    kind: str
    start: int
    end: int


# (kind, pattern). Patterns are matched case-sensitively unless
# they carry their own (?i) flag.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "private_key",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
            r".*?-----END [A-Z ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
    ),
    # --- Provider keys with a recognisable format ---
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("stripe_key", re.compile(r"\b[sr]k_(?:live|test)_[A-Za-z0-9]{16,}")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    (
        "jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
        ),
    ),
    (
        "bearer_token",
        re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{20,}=*"),
    ),
    (
        "url_credentials",
        # https://user:secret@host
        re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s:/@]+:[^\s@/]+@", re.I),
    ),
    # --- Secrets introduced by a keyword ---
    (
        "password",
        # "my password is hunter2", "password: hunter2", "pin = 1234",
        # "the password for the wifi is sunflower"
        re.compile(
            r"(?i)\b(?:password|passcode|passphrase|passwd|pwd|pin)\b"
            r"(?:\s+(?:for|to|of|on)\s+(?:the\s+|my\s+)?\S+)?"
            r"\s*(?:is|:|=)\s*\S+"
        ),
    ),
    (
        "credential",
        # "my api key is abc123...", "token: ...", "secret = ..."
        re.compile(
            r"(?i)\b(?:api[ _-]?key|access[ _-]?key|secret(?:[ _-]?key)?"
            r"|auth[ _-]?token|token)\b\s*(?:is|:|=)\s*\S{8,}"
        ),
    ),
    ("us_ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
]

# 13-19 digits, optionally separated by single spaces or dashes.
_CARD_CANDIDATE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")

# Country code, 2 check digits, then 11-30 letters/digits (spaces
# allowed in groups of four, as IBANs are usually written).
_IBAN_CANDIDATE = re.compile(r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{1,4}){3,8}\b")


def _is_valid_iban(text: str) -> bool:
    """ISO 13616 mod-97 check, so random codes are not flagged."""

    iban = text.replace(" ", "")

    if not 15 <= len(iban) <= 34:
        return False

    rearranged = iban[4:] + iban[:4]
    digits = "".join(str(int(character, 36)) for character in rearranged)

    return int(digits) % 97 == 1


def _passes_luhn(digits: str) -> bool:
    """Luhn checksum used by payment card numbers."""

    total = 0

    for index, character in enumerate(reversed(digits)):
        value = int(character)

        if index % 2 == 1:
            value *= 2

            if value > 9:
                value -= 9

        total += value

    return total % 10 == 0


class SensitiveDataDetector:
    """Finds and redacts secrets in text."""

    def find(
        self,
        text: str,
    ) -> list[SensitiveFinding]:
        """Return all sensitive spans, sorted by position."""

        findings = [
            SensitiveFinding(kind, match.start(), match.end())
            for kind, pattern in _PATTERNS
            for match in pattern.finditer(text)
        ]

        for match in _CARD_CANDIDATE.finditer(text):
            digits = re.sub(r"\D", "", match.group())

            if 13 <= len(digits) <= 19 and _passes_luhn(digits):
                findings.append(
                    SensitiveFinding(
                        "payment_card",
                        match.start(),
                        match.end(),
                    )
                )

        for match in _IBAN_CANDIDATE.finditer(text):
            if _is_valid_iban(match.group()):
                findings.append(
                    SensitiveFinding(
                        "bank_account",
                        match.start(),
                        match.end(),
                    )
                )

        return sorted(findings, key=lambda finding: finding.start)

    def contains_sensitive_data(
        self,
        text: str,
    ) -> bool:
        return bool(self.find(text))

    def kinds(
        self,
        text: str,
    ) -> list[str]:
        """Distinct kinds of sensitive data, in order of appearance."""

        return list(
            dict.fromkeys(finding.kind for finding in self.find(text))
        )

    def redact(
        self,
        text: str,
    ) -> str:
        """Replace every sensitive span with [REDACTED]."""

        findings = self.find(text)

        if not findings:
            return text

        parts: list[str] = []
        position = 0

        for finding in findings:
            # Overlapping findings: skip what is already redacted.
            if finding.end <= position:
                continue

            parts.append(text[position : max(position, finding.start)])
            parts.append(REDACTED)
            position = finding.end

        parts.append(text[position:])

        return "".join(parts)
