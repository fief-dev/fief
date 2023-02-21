import re

LOCALHOST_HOST_PATTERN = re.compile(
    r"([^\.]+\.)?localhost(\d+)?|127\.0\.0\.1", flags=re.IGNORECASE
)


def is_localhost(host: str) -> bool:
    return LOCALHOST_HOST_PATTERN.match(host) is not None


__all__ = ["is_localhost"]
