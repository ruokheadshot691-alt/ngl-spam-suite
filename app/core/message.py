"""Spintax parser + placeholder resolution.

Syntax:
    {a|b|c}        → random pick salah satu
    {{index}}      → nomor urut job
    {{username}}   → target username
    {{timestamp}}  → unix timestamp
    {{random}}     → random string 6 char
"""

from __future__ import annotations

import random
import re
import string
import time

_SPINTAX_RE = re.compile(r"\{([^{}]+)\}")
_PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


def _rand_str(n: int = 6) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=n))


def parse_spintax(text: str) -> str:
    """Resolve spintax `{a|b|c}` secara rekursif.

    Args:
        text: String yang mungkin mengandung spintax.

    Returns:
        String dengan spintax sudah di-resolve.
    """
    def repl(match: re.Match[str]) -> str:
        options = match.group(1).split("|")
        return random.choice(options)

    prev = None
    current = text
    while prev != current:
        prev = current
        current = _SPINTAX_RE.sub(repl, current)
    return current


def resolve_placeholders(
    text: str,
    *,
    index: int = 0,
    username: str = "",
    timestamp: float | None = None,
) -> str:
    """Resolve placeholder `{{...}}`.

    Args:
        text: String yang mengandung placeholder.
        index: Nilai untuk `{{index}}`.
        username: Nilai untuk `{{username}}`.
        timestamp: Nilai untuk `{{timestamp}}`. Default = now.

    Returns:
        String dengan placeholder sudah di-resolve.
    """
    ts = int(timestamp if timestamp is not None else time.time())

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key == "index":
            return str(index)
        if key == "username":
            return username
        if key == "timestamp":
            return str(ts)
        if key == "random":
            return _rand_str(6)
        return match.group(0)

    return _PLACEHOLDER_RE.sub(repl, text)


def render(
    template: str,
    *,
    index: int = 0,
    username: str = "",
    timestamp: float | None = None,
) -> str:
    """Render template: resolve placeholder lalu spintax.

    Args:
        template: Template pesan.
        index: Nomor urut.
        username: Target username.
        timestamp: Unix ts opsional.

    Returns:
        Pesan final.
    """
    with_ph = resolve_placeholders(
        template, index=index, username=username, timestamp=timestamp
    )
    return parse_spintax(with_ph)