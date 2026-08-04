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
import collections
import datetime as dt
import glob
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ABSTRACT_CHARS = 600  # keep the page a reasonable size; full text lives in the vault

# Papers with more authors than this are consortium/working-group outputs. Being
# named on one says little about who actually works with whom, and each such
# paper alone contributes up to n*(n-1)/2 edges — one 79-author paper is 3,081 —
# which drowns the real collaboration structure. Excluded from co-authorship
# edges only; the papers themselves are untouched everywhere else.
CONSORTIUM_AUTHORS = 30

# Edge weight = papers shared. Keeping only repeat collaborations is what makes
# the graph readable: at weight 1 the co-author network is ~12k edges of hairball.
MIN_COAUTHOR_WEIGHT = 2
MIN_TOPIC_WEIGHT = 3


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

    return {"papers": papers, "people": people, "topics": topics, "theses": theses,
            "graph": build_graphs(papers, people, topics)}


def build_graphs(papers: list, people: list, topics: list) -> dict:
    """Precompute the co-authorship and topic co-occurrence edge lists.

    Edges are `[i, j, weight]` where i and j index into `people` / `topics` —
    integer indices rather than names keep the payload small enough to embed.
    """
    person_at = {p["n"]: i for i, p in enumerate(people)}
    topic_at = {t["n"]: i for i, t in enumerate(topics)}

    coauthor: collections.Counter = collections.Counter()
    consortium_skipped = 0
    for paper in papers:
        names = sorted({n for n in paper["a"] if n in person_at})
        if len(names) > CONSORTIUM_AUTHORS:
            consortium_skipped += 1
            continue
        for a, b in itertools.combinations(names, 2):
            coauthor[(person_at[a], person_at[b])] += 1

    cooccur: collections.Counter = collections.Counter()
    for paper in papers:
        names = sorted({t for t in paper["k"] if t in topic_at})
        for a, b in itertools.combinations(names, 2):
            cooccur[(topic_at[a], topic_at[b])] += 1

    return {
        "people": [[i, j, w] for (i, j), w in coauthor.items() if w >= MIN_COAUTHOR_WEIGHT],
        "topics": [[i, j, w] for (i, j), w in cooccur.items() if w >= MIN_TOPIC_WEIGHT],
        "authorCap": CONSORTIUM_AUTHORS,
        "consortiumSkipped": consortium_skipped,
        "minPeopleWeight": MIN_COAUTHOR_WEIGHT,
        "minTopicWeight": MIN_TOPIC_WEIGHT,
    }


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

    g = data["graph"]
    print(
        f"Wrote {args.out} — {len(data['papers'])} papers, {len(data['people'])} people, "
        f"{len(data['topics'])} topics, {len(data['theses'])} theses; "
        f"map: {len(g['people'])} co-author edges "
        f"({g['consortiumSkipped']} consortium papers excluded), "
        f"{len(g['topics'])} topic edges "
        f"({os.path.getsize(args.out) // 1024} KB)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
