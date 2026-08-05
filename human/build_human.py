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
import json
import os
import re
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Reuse the build's own merge-map loader rather than reimplementing the format,
# so the browser and the vault can never disagree about what a merge means.
sys.path.insert(0, ROOT)
try:
    from wellington_vault.build import load_merge_map
    from wellington_vault.notes import person_filename
    from wellington_vault.util import normalize_name
except ImportError:                                    # pragma: no cover
    load_merge_map = None
    normalize_name = None
    person_filename = None

DEFAULT_MERGE_MAP = os.path.join(ROOT, "people-merge-map.tsv")
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

    A key with nothing after the colon is either an empty scalar (`venue:` on a
    paper with no journal) or the header of a `- item` list on the lines below.
    It must stay an empty *string* until an item actually appears: an empty list
    survives into the page's JSON as `[]`, which is truthy in JavaScript, so
    `if (p.venue)` passes and renders nothing — a stray separator, or an `<a>`
    pointing at an empty href.
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
            if not isinstance(data.get(key), list):
                data[key] = []          # first item promotes the key to a list
            data[key].append(value)
        else:
            k, sep, v = line.partition(":")
            if not sep:
                continue
            key = k.strip()
            data[key] = v.strip().strip('"')
    return data, text[m.end():]


# Conference abstracts carry a session code from the meeting programme:
# "P4-218:", "O1-03-07", "S3-02-03:", "PL-04-01:", "[P3–182]:", "IC-P1", "LB-P4",
# "Abstract 245:", "0404 ", "2.16 ", "73 (13B) ", "A.1 ". Hyphens vary (ASCII,
# non-breaking, en/em dash) because the source records are inconsistent.
ABSTRACT_CODE = re.compile(r"""^\s*(
    \[?[A-Z]{1,2}[‐‑–—-]?\d{1,2}[‐‑–—.\- ]\s?\d   # P1-196, O1-03-07, S3-02-03, PL-04-01
  | (IC|LB|DT)[‐‑–—-]P?\d                          # IC-P1, LB-P4, DT-01
  | abstract\s+\d+                                 # Abstract 245:
  | \d{1,4}[. ]\d{1,3}\s+\w                        # 2.16 Blood biomarkers, 0404 Sleep
  | \d{1,3}\s*\(\d+[A-Za-z]?\)                     # 73 (13B) Sex, puberty
  | [A-Z]\.\d+\s                                   # A.1 Repurposing Ambroxol
)""", re.I | re.X)

# DOI shapes that identify a record as a meeting abstract rather than an article.
# Each was checked against this vault: every match has at most two citations,
# while the regular articles in the same journals sit in the hundreds.
ABSTRACT_DOI = re.compile(r"""(
    10\.1002/alz\.\d{6}\b        # Alzheimer's & Dementia supplement (articles use 4-5 digits)
  | 10\.1002/alz\d+_\d+          # its 2025 supplement form, alz70856_102379
  | 10\.1136/bjsports-\d+-concussion\.
  | 10\.58530/                    # ISMRM proceedings
  | 10\.1182/blood-\d{4}-\d+     # ASH meeting abstract (articles are blood.2023019876)
  | /vkaf\d+\.\d+$               # Journal of Immunology meeting supplement
  | \d+s\d{3}$                    # journal supplement suffix, ...05201s416
)""", re.X)

# Supplementary material deposited beside a paper — not a publication of its own.
SUPPLEMENT_DOI = re.compile(r"10\.6084/")           # Figshare

# Editorial furniture and peer-review artefacts.
NON_ARTICLE_TITLE = re.compile(r"^\s*(author response|preface|hotspots)\b", re.I)

PREPRINT_TYPES = frozenset({"preprint", "posted-content"})


def record_kind(title: str, work_type: str, venue: str, doi: str) -> str:
    """Classify a record by what kind of output it actually is.

    OpenAlex types nearly all of these as ordinary articles, so there is no
    field to read — the evidence is in the DOI, the venue and the title. Only
    "article" is counted by default; the page can include any combination.

    Returns one of: "article", "preprint", "abstract", "supplement", "other".

    Rules are chosen for precision, because wrongly demoting a real paper is
    worse than leaving a stray abstract in the count. Every rule was checked
    against this vault: nothing demoted has more than two citations, while the
    genuine articles in the same journals have hundreds.
    """
    title, doi = title or "", doi or ""
    work_type, venue = (work_type or "").lower(), venue or ""

    if SUPPLEMENT_DOI.search(doi) or title.lower().startswith("additional file"):
        return "supplement"
    if work_type == "peer-review" or NON_ARTICLE_TITLE.match(title):
        return "other"
    # Checked before the abstract rules so a shouty preprint title cannot be
    # mistaken for a proceedings abstract.
    if work_type in PREPRINT_TYPES:
        return "preprint"
    if ABSTRACT_DOI.search(doi):
        return "abstract"
    if venue.startswith("Proceedings on CD-ROM") or "Supplements" in venue:
        return "abstract"
    if ABSTRACT_CODE.match(title):
        return "abstract"
    # All-capitals titles are how several proceedings render abstracts.
    letters = [c for c in title if c.isalpha()]
    if len(letters) > 20 and sum(c.isupper() for c in letters) / len(letters) > 0.9:
        return "abstract"
    return "article"


def clean_abstract(text: str) -> str:
    """Drop the vault's leading blockquote caveat, keep the prose.

    Paper notes prefix reconstructed abstracts with a `>` line explaining that
    OpenAlex stores them as an inverted index. That note is for Claude; a person
    reading the browser just wants the abstract.
    """
    lines = [ln for ln in text.strip().splitlines() if not ln.lstrip().startswith(">")]
    return "\n".join(lines).strip()


def link_parts(value: str) -> tuple[str, str]:
    """`"[[Jose Rodriguez|José Rodríguez]]"` -> `("Jose Rodriguez", "José Rodríguez")`.

    Notes emit the aliased form `[[slug|Display Name]]` whenever the display
    name does not survive slugification — diacritics stripped, non-ASCII hyphens
    rewritten. `wikilink()` rewrites any `|` inside the target, so the first one
    is always the alias separator.

    The target is the note's filename, and so the vault's identity for that
    person. The alias is only how one paper happened to spell them.
    """
    v = re.sub(r"^\[\[|\]\]$", "", value.strip())
    target, _, alias = v.partition("|")
    return target.strip(), (alias.strip() or target.strip())


def link_pairs(values) -> list[tuple[str, str]]:
    return [link_parts(v) for v in values] if isinstance(values, list) else []


def resolve_labels(link_lists) -> dict[str, str]:
    """Settle on one display name per wikilink target.

    OpenAlex spells the same person differently across papers — "Ramon
    Diaz‐Arrastia" on six of them and "Ramon Diaz Arrastia" on a seventh — and
    the notes carry each spelling through as that link's alias. Keying people on
    the alias therefore splits one person into several, each with a share of the
    papers. Keying on the target does not, because the vault already resolved
    every spelling to a single person note; the split was only ever the
    browser's.

    Of the spellings pointing at one target, take the one the most papers use.
    Break ties toward the spelling carrying diacritics, since the plain form is
    the lossy one, then toward the longer, then alphabetically so that a rebuild
    from unchanged notes produces an unchanged page.
    """
    seen: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for pairs in link_lists:
        for target, alias in pairs:
            seen[target][alias] += 1
    return {
        target: sorted(aliases, key=lambda a: (-aliases[a],
                                               -sum(ord(c) > 127 for c in a),
                                               -len(a), a))[0]
        for target, aliases in seen.items()
    }


def unlink(values, labels: dict | None = None) -> list[str]:
    """`["[[Cheryl L. Wellington]]"]` -> `["Cheryl L. Wellington"]`.

    With `labels` from `resolve_labels()`, every link to a target resolves to
    that target's one agreed display name. Without it, each link keeps its own
    alias — which is what splits people; see `resolve_labels()`.
    """
    if not isinstance(values, list):
        return []
    out = []
    for target, alias in link_pairs(values):
        out.append(labels.get(target, alias) if labels else alias)
    return out


def as_int(value, default=0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def people_from_papers(papers: list, notes: list) -> tuple[list, int]:
    """Derive the people list from the papers rather than from `people/`.

    Once merges are applied, per-note `papers_with_wellington_lab` counts cannot
    simply be summed across a cluster: a paper that names two variants of one
    person would be counted twice. Counting distinct papers per canonical name
    is the only way to get this right, and it has the side benefit that the
    number shown always matches what clicking the person actually lists.

    `role` is carried over from the person notes, which is the only field the
    papers do not contain. Person notes with no paper in `papers/` — their
    papers were lost to filename collisions — are carried over as-is so nobody
    silently disappears; the count of those is returned alongside.
    """
    role_of = {}
    for note in notes:
        if note["n"]:
            role_of.setdefault(note["n"], note["r"])

    agg: dict[str, dict] = {}
    for paper in papers:
        for name in paper["a"]:                        # already merged + deduped
            entry = agg.setdefault(name, {"n": name, "p": 0, "years": []})
            entry["p"] += 1
            if paper["y"]:
                entry["years"].append(paper["y"])

    people = []
    for name, entry in agg.items():
        years = entry["years"]
        people.append({
            "n": name,
            "r": role_of.get(name, "co-author"),
            "p": entry["p"],
            "f": str(min(years)) if years else "",
            "l": str(max(years)) if years else "",
        })

    carried = [n for n in notes if n["n"] and n["n"] not in agg]
    people.extend(carried)
    people.sort(key=lambda p: p["n"])
    return people, len(carried)


def collect(vault: str, merge_map: dict | None = None) -> dict:
    merge_map = merge_map or {}

    parsed = [parse_note(p)
              for p in sorted(glob.glob(os.path.join(vault, "papers", "*.md")))]

    # Settle display names before counting anything — see resolve_labels().
    author_labels = resolve_labels(link_pairs(fm.get("authors", [])) for fm, _ in parsed)
    topic_labels = resolve_labels(link_pairs(fm.get("topics", [])) for fm, _ in parsed)

    def relabel(name: str) -> str:
        """Re-resolve a name through the labels, since the merge map names people
        by one particular spelling and that may not be the one that won."""
        return author_labels.get(person_filename(name), name) if person_filename else name

    def canonical(name: str) -> str:
        if not merge_map:
            return name
        return relabel(merge_map.get(name)
                       or (normalize_name and merge_map.get(normalize_name(name)))
                       or name)

    papers = []
    for fm, body in parsed:
        abstract = re.search(r"## Abstract\n(.+?)(?:\n##|\Z)", body, re.S)
        title = fm.get("title", "")
        work_type = fm.get("work_type", "")
        kind = record_kind(title, work_type, fm.get("venue", ""), fm.get("doi", ""))
        papers.append({
            "t": title,
            "kind": kind,
            "y": as_int(fm.get("year"), 0) or None,
            "v": fm.get("venue", ""),
            "doi": fm.get("doi", ""),
            "oa": fm.get("open_access") == "true",
            "c": as_int(fm.get("cited_by_count")),
            "r": fm.get("wellington_role", ""),
            # Fold merged variants together, then drop repeats: a paper can name
            # the same person twice once merges apply (consortium records list
            # some people individually and again as group members).
            "a": list(dict.fromkeys(
                canonical(n) for n in unlink(fm.get("authors", []), author_labels))),
            "k": unlink(fm.get("topics", []), topic_labels),
            "ab": clean_abstract(abstract.group(1))[:ABSTRACT_CHARS] if abstract else "",
        })

    note_people = []
    for path in sorted(glob.glob(os.path.join(vault, "people", "*.md"))):
        fm, _ = parse_note(path)
        # The filename is the target every paper links to, so it — not the
        # note's own `name:` — is what lines this note up with the papers.
        target = os.path.splitext(os.path.basename(path))[0]
        note_people.append({
            "n": canonical(author_labels.get(target, fm.get("name", ""))),
            "r": fm.get("role", ""),
            "p": as_int(fm.get("papers_with_wellington_lab")),
            "f": fm.get("first_co_pub_year", ""),
            "l": fm.get("last_co_pub_year", ""),
        })
    people, carried = people_from_papers(papers, note_people)

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
            "graph": {"authorCap": CONSORTIUM_AUTHORS,
                      "minPeopleWeight": MIN_COAUTHOR_WEIGHT,
                      "minTopicWeight": MIN_TOPIC_WEIGHT,
                      "consortiumSkipped": sum(1 for p in papers
                                               if len(p["a"]) > CONSORTIUM_AUTHORS)},
            "_notePeople": len(note_people), "_carried": carried}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", default=os.path.join(ROOT, "vault"),
                        help="Vault directory to read. (default: %(default)s)")
    parser.add_argument("--out", default=os.path.join(HERE, "index.html"),
                        help="HTML file to write. (default: %(default)s)")
    parser.add_argument("--merge-map", default=DEFAULT_MERGE_MAP,
                        help="TSV of curated variant→canonical author-name merges, "
                             "the same file the vault build uses. (default: %(default)s)")
    parser.add_argument("--no-merge-map", action="store_true",
                        help="Show people exactly as the vault has them, duplicates "
                             "and all.")
    args = parser.parse_args(argv)

    if not os.path.isdir(os.path.join(args.vault, "papers")):
        print(f"ERROR: no papers/ under {args.vault}. Run the vault build first.",
              file=sys.stderr)
        return 2

    merge_map = {}
    if not args.no_merge_map:
        if load_merge_map is None:
            print("WARNING: wellington_vault not importable; merges not applied.",
                  file=sys.stderr)
        else:
            merge_map = load_merge_map(Path(args.merge_map))
            if not merge_map:
                print(f"No merge map at {args.merge_map}; showing people as-is.",
                      file=sys.stderr)

    data = collect(args.vault, merge_map=merge_map)
    if not data["papers"]:
        print(f"ERROR: {args.vault}/papers is empty.", file=sys.stderr)
        return 2

    note_people = data.pop("_notePeople")
    carried = data.pop("_carried")

    template = open(os.path.join(HERE, "_template.html"), encoding="utf-8").read()
    # `</script>` inside JSON would close the host <script> tag early.
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    html = template.replace("/*__DATA__*/", payload)
    html = html.replace("/*__BUILT__*/", dt.date.today().isoformat())

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    kinds = collections.Counter(p["kind"] for p in data["papers"])
    print(
        f"Wrote {args.out} — {len(data['papers'])} records "
        f"({kinds['article']} articles, {kinds['preprint']} preprints, "
        f"{kinds['abstract']} abstracts, {kinds['supplement']} supplements, "
        f"{kinds['other']} other), "
        f"{len(data['people'])} people, "
        f"{len(data['topics'])} topics, {len(data['theses'])} theses "
        f"({os.path.getsize(args.out) // 1024} KB)"
    )
    if merge_map:
        print(
            f"  people: {len(data['people'])} shown, counted from the papers so merged "
            f"clusters are not double-counted (vault has {note_people} person notes; "
            f"{carried} note(s) carried over with no paper in papers/)."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
