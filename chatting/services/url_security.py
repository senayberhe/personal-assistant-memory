from urllib.parse import urlparse


ALLOWED_SCHEMES = {
    "http",
    "https",
}


def validate_url(url: str) -> str:

    url = url.strip()

    if not url:
        raise ValueError(
            "URL cannot be empty."
        )

    parsed = urlparse(url)

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise ValueError(
            "Only HTTP and HTTPS URLs are allowed."
        )

    if not parsed.netloc:
        raise ValueError(
            "URL must contain a hostname."
        )

    return url