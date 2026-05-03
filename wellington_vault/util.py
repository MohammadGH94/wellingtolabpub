"""Small shared utilities — slugify, frontmatter emit, abstract reconstruction."""

from __future__ import annotations

import datetime as dt
import re
import unicodedata
from typing import Any


def slugify(text: str, max_len: int = 80) -> str:
    """Filesystem-safe slug. Preserves spaces (Obsidian-friendly) but strips bad chars."""
    if not text:
        return "untitled"
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\s\-—'’.,&()]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -—._,")
    if len(text) > max_len:
        text = text[:max_len].rsplit(" ", 1)[0].rstrip(" -—._,")
    return text or "untitled"


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """OpenAlex stores abstracts as {token: [positions]} (Elsevier compliance).

    Rebuild the linear text. Returns "" if the field is missing.
    """
    if not inverted_index:
        return ""
    positions: list[tuple[int, str]] = []
    for token, idxs in inverted_index.items():
        for i in idxs:
            positions.append((i, token))
    positions.sort()
    return " ".join(tok for _, tok in positions)


def yaml_emit(d: dict[str, Any]) -> str:
    """Minimal YAML emitter for frontmatter. Handles strings, ints, bools, lists, None.

    We control the schema so we don't need full YAML — just safe quoting.
    """
    lines: list[str] = []
    for key, value in d.items():
        lines.append(_yaml_kv(key, value, indent=0))
    return "\n".join(lines)


def _yaml_kv(key: str, value: Any, indent: int) -> str:
    pad = "  " * indent
    if value is None:
        return f"{pad}{key}:"
    if isinstance(value, bool):
        return f"{pad}{key}: {'true' if value else 'false'}"
    if isinstance(value, (int, float)):
        return f"{pad}{key}: {value}"
    if isinstance(value, list):
        if not value:
            return f"{pad}{key}: []"
        items = "\n".join(f"{pad}  - {_yaml_scalar(v)}" for v in value)
        return f"{pad}{key}:\n{items}"
    return f"{pad}{key}: {_yaml_scalar(value)}"


def _yaml_scalar(value: Any) -> str:
    if isinstance(value, str):
        return _yaml_string(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def _yaml_string(s: str) -> str:
    """Quote a string for YAML if it contains anything risky."""
    if s == "":
        return '""'
    if re.search(r'[:#\[\]\{\},&\*\!\|\>\'"%@`\n]', s) or s.strip() != s or s.lower() in {
        "yes", "no", "true", "false", "null", "~",
    } or s[0] in "-?":
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s


def today_iso() -> str:
    return dt.date.today().isoformat()


def frontmatter(meta: dict[str, Any]) -> str:
    return f"---\n{yaml_emit(meta)}\n---\n"


def wikilink(target: str, alias: str | None = None) -> str:
    """Render an Obsidian wikilink. `target` is the note basename (no .md)."""
    target = target.replace("[", "(").replace("]", ")").replace("|", "-")
    if alias and alias != target:
        return f"[[{target}|{alias}]]"
    return f"[[{target}]]"


def pluck(d: dict | None, *keys: str, default: Any = None) -> Any:
    """Safe nested dict access: pluck(work, 'host_venue', 'display_name')."""
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur if cur is not None else default
