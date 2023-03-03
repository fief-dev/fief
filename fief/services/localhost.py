import ipaddress
import re

LOCALHOST_HOST_PATTERN = re.compile(
    r"([^\.]+\.)?localhost(\d+)?", flags=re.IGNORECASE
)


def is_localhost(host: str) -> bool:
    try:
        return ipaddress.IPv4Address(host).is_private
    except ValueError:
        return LOCALHOST_HOST_PATTERN.match(host) is not None


__all__ = ["is_localhost"]
