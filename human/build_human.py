#!/usr/bin/env python3
"""Render the human-facing browser from the vault.

The vault under `vault/` is written for Claude — dense frontmatter, wikilinks,
one note per entity. This script reads those notes back and emits a single
self-contained HTML page that a person can open in a browser and actually use:
search, filter, sort, and click through the co-author and topic graph.

Run it after every `python -m wellington_vault build`:

    python human/build_human.py

Stdlib only, same as the rest of the repo. No network access.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ABSTRACT_CHARS = 600  # keep the page a reasonable size; full text lives in the vault


def parse_note(path: str) -> tuple[dict, str]:
    """Split a vault note into (frontmatter dict, body).

    The frontmatter is emitted by `wellington_vault.util.yaml_emit`, so it is a
    known-narrow subset of YAML: scalars and `- item` lists, no nesting. That
    lets us parse it without a YAML dependency.
    """
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    data: dict = {}
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"^\s*-\s", line) and key:
            value = line.strip()[2:].strip().strip('"')
            if isinstance(data.get(key), list):
                data[key].append(value)
            else:
                data[key] = [value]
        else:
            k, sep, v = line.partition(":")
            if not sep:
                continue
            key = k.strip()
            v = v.strip().strip('"')
            data[key] = v if v else []
    return data, text[m.end():]


def clean_abstract(text: str) -> str:
    """Drop the vault's leading blockquote caveat, keep the prose.

    Paper notes prefix reconstructed abstracts with a `>` line explaining that
    OpenAlex stores them as an inverted index. That note is for Claude; a person
    reading the browser just wants the abstract.
    """
    lines = [ln for ln in text.strip().splitlines() if not ln.lstrip().startswith(">")]
    return "\n".join(lines).strip()


def unlink(values) -> list[str]:
    """`["[[Cheryl L. Wellington]]"]` -> `["Cheryl L. Wellington"]`."""
    if not isinstance(values, list):
        return []
    return [re.sub(r"^\[\[|\]\]$", "", v) for v in values]


def as_int(value, default=0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def collect(vault: str) -> dict:
    papers = []
    for path in sorted(glob.glob(os.path.join(vault, "papers", "*.md"))):
        fm, body = parse_note(path)
        abstract = re.search(r"## Abstract\n(.+?)(?:\n##|\Z)", body, re.S)
        papers.append({
            "t": fm.get("title", ""),
            "y": as_int(fm.get("year"), 0) or None,
            "v": fm.get("venue", ""),
            "doi": fm.get("doi", ""),
            "oa": fm.get("open_access") == "true",
            "c": as_int(fm.get("cited_by_count")),
            "r": fm.get("wellington_role", ""),
            "a": unlink(fm.get("authors", [])),
            "k": unlink(fm.get("topics", [])),
            "ab": clean_abstract(abstract.group(1))[:ABSTRACT_CHARS] if abstract else "",
        })

    people = []
    for path in sorted(glob.glob(os.path.join(vault, "people", "*.md"))):
        fm, _ = parse_note(path)
        people.append({
            "n": fm.get("name", ""),
            "r": fm.get("role", ""),
            "p": as_int(fm.get("papers_with_wellington_lab")),
            "f": fm.get("first_co_pub_year", ""),
            "l": fm.get("last_co_pub_year", ""),
        })

    topics = []
    for path in sorted(glob.glob(os.path.join(vault, "topics", "*.md"))):
        fm, _ = parse_note(path)
        topics.append({
            "n": fm.get("name", ""),
            "p": as_int(fm.get("wellington_lab_papers")),
            "f": fm.get("first_year", ""),
            "l": fm.get("last_year", ""),
        })

    theses = []
    for path in sorted(glob.glob(os.path.join(vault, "theses", "*.md"))):
        fm, _ = parse_note(path)
        theses.append({
            "t": fm.get("title", ""),
            "y": fm.get("year", ""),
            "c": fm.get("candidate", ""),
            "d": fm.get("degree", ""),
            "pr": fm.get("program", ""),
            "u": fm.get("circle_url", ""),
        })

    return {"papers": papers, "people": people, "topics": topics, "theses": theses}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", default=os.path.join(ROOT, "vault"),
                        help="Vault directory to read. (default: %(default)s)")
    parser.add_argument("--out", default=os.path.join(HERE, "index.html"),
                        help="HTML file to write. (default: %(default)s)")
    args = parser.parse_args(argv)

    if not os.path.isdir(os.path.join(args.vault, "papers")):
        print(f"ERROR: no papers/ under {args.vault}. Run the vault build first.",
              file=sys.stderr)
        return 2

    data = collect(args.vault)
    if not data["papers"]:
        print(f"ERROR: {args.vault}/papers is empty.", file=sys.stderr)
        return 2

    template = open(os.path.join(HERE, "_template.html"), encoding="utf-8").read()
    # `</script>` inside JSON would close the host <script> tag early.
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace("/*__DATA__*/", payload)
    html = html.replace("/*__BUILT__*/", dt.date.today().isoformat())

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    print(
        f"Wrote {args.out} — {len(data['papers'])} papers, {len(data['people'])} people, "
        f"{len(data['topics'])} topics, {len(data['theses'])} theses "
        f"({os.path.getsize(args.out) // 1024} KB)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
