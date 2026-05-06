"""CLI entry point: `python -m wellington_vault build [...]`."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .build import (
    build_indexes,
    canonicalize_authorships,
    extract_trainee_candidates,
    resolve_author,
    write_vault,
)
from .circle import CircleClient, CircleError, from_lastname_first, to_lastname_first
from .openalex import OpenAlexClient
from .util import normalize_name, pluck
from .wordcloud_gen import collect_abstracts, render_wordcloud


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wellington-vault",
        description="Build an Obsidian second-brain vault from Dr. Cheryl Wellington's "
                    "OpenAlex publication record.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    build = sub.add_parser("build", help="Resolve author, fetch works, render vault notes.")
    build.add_argument("--author-name", default="Cheryl Wellington",
                       help="Author display name to search for. (default: %(default)s)")
    build.add_argument("--author-id", default=None,
                       help="OpenAlex author ID (e.g. A1234567890). Skips name resolution.")
    build.add_argument("--institution-hint", default="British Columbia",
                       help="Substring to filter author search by institution. "
                            "(default: %(default)s)")
    build.add_argument("--out", type=Path, default=Path("vault"),
                       help="Output vault directory. (default: %(default)s)")
    build.add_argument("--cache", type=Path, default=Path(".cache/openalex"),
                       help="OpenAlex response cache directory. (default: %(default)s)")
    build.add_argument("--mailto", default="research@example.com",
                       help="Email for OpenAlex polite pool. (default: %(default)s)")
    build.add_argument("--refresh", action="store_true",
                       help="Re-fetch from OpenAlex (ignore cache).")
    build.add_argument("--dry-run", action="store_true",
                       help="Print what would be written; don't touch disk.")
    build.add_argument("--limit", type=int, default=None,
                       help="Stop after N works (for testing).")
    build.add_argument("--circle-api-key", default=None,
                       help="UBC Open Collections API key for cIRcle thesis lookups. "
                            "Falls back to the CIRCLE_API_KEY env var. If neither is "
                            "set, cIRcle ingestion is skipped and only OpenAlex-typed "
                            "dissertations (if any) are written to theses/.")
    build.add_argument("--circle-cache", type=Path, default=Path(".cache/circle"),
                       help="cIRcle response cache directory. (default: %(default)s)")
    build.add_argument("--circle-hits-per-trainee", type=int, default=5,
                       help="Max cIRcle hits to keep per trainee candidate. "
                            "(default: %(default)s)")
    build.add_argument("--circle-max-trainees", type=int, default=None,
                       help="Cap the number of trainee candidates queried against "
                            "cIRcle (most-frequent first). Default: no cap.")
    build.add_argument("--circle-pi-mention-size", type=int, default=50,
                       help="Max thesis hits to fetch from the PI-name phrase-match "
                            "leg (filtered to creators in the Wellington OpenAlex "
                            "co-author graph; the raw query is noisy because it "
                            "also matches examining-committee acknowledgments). "
                            "(default: %(default)s)")
    build.add_argument("--trainees-file", type=Path, default=None,
                       help="Optional path to a UTF-8 text file listing known "
                            "trainee names (one per line, '#' for comments) in "
                            "OpenAlex 'Forename Surname' format. Each name is "
                            "queried against cIRcle alongside the auto-derived "
                            "candidates — use this for trainees who never "
                            "co-authored a paper.")
    build.add_argument("--no-wordcloud", action="store_true",
                       help="Skip the abstracts → vault/wordcloud.png render at "
                            "end of build. Requires the optional `wordcloud` "
                            "package (pip install wordcloud); without it the "
                            "step is skipped automatically.")

    resolve = sub.add_parser("resolve", help="Resolve author and print top candidates only.")
    resolve.add_argument("--author-name", default="Cheryl Wellington")
    resolve.add_argument("--institution-hint", default="British Columbia")
    resolve.add_argument("--cache", type=Path, default=Path(".cache/openalex"))
    resolve.add_argument("--mailto", default="research@example.com")
    resolve.add_argument("--refresh", action="store_true")

    args = parser.parse_args(argv)

    client = OpenAlexClient(mailto=args.mailto, cache_dir=args.cache, refresh=args.refresh)

    if args.cmd == "resolve":
        author = resolve_author(client, args.author_name, args.institution_hint)
        print(_format_author(author))
        return 0

    if args.cmd == "build":
        if args.author_id:
            author = client.get_author(args.author_id)
            print(f"Resolved (by ID): {_format_author(author)}", file=sys.stderr)
        else:
            author = resolve_author(client, args.author_name, args.institution_hint)
            print(f"Selected: {_format_author(author)}", file=sys.stderr)

        author_id = (author.get("id") or "").rstrip("/").rsplit("/", 1)[-1]
        if not author_id:
            print("ERROR: resolved author has no OpenAlex ID.", file=sys.stderr)
            return 2

        print(f"Fetching works for {author_id}...", file=sys.stderr)
        works: list[dict] = []
        for i, w in enumerate(client.iter_works(author_id), 1):
            works.append(w)
            if i % 50 == 0:
                print(f"  fetched {i} works...", file=sys.stderr)
            if args.limit and len(works) >= args.limit:
                break
        print(f"Fetched {len(works)} works.", file=sys.stderr)

        # Collapse author display-name variants ("Cheryl Wellington" /
        # "Cheryl L. Wellington") to one canonical name per OpenAlex author ID
        # before indexing — otherwise variants fragment into duplicate person
        # notes and break the co-author graph.
        canonical_names = canonicalize_authorships(works)
        pi_id = (author.get("id") or "").rstrip("/").rsplit("/", 1)[-1] or None

        indexes = build_indexes(works)
        print(
            f"Indexed: {len(indexes['by_person'])} unique authors "
            f"(by OpenAlex ID), {len(indexes['by_topic'])} unique topics.",
            file=sys.stderr,
        )

        pi_name = author.get("display_name") or args.author_name
        circle_theses = _fetch_circle_theses(args, works, pi_name, pi_id=pi_id)

        stats = write_vault(
            works, indexes, pi_name, args.out,
            dry_run=args.dry_run, circle_theses=circle_theses,
            pi_id=pi_id, canonical_names=canonical_names,
        )
        action = "Would write" if args.dry_run else "Wrote"
        print(
            f"{action}: {stats['papers']} papers, {stats['theses']} theses, "
            f"{stats['people']} people, {stats['topics']} topics → {args.out}/",
            file=sys.stderr,
        )

        if not args.dry_run and not args.no_wordcloud:
            wc_path = args.out / "wordcloud.png"
            text = collect_abstracts(works, circle_theses)
            if render_wordcloud(text, wc_path):
                print(f"Wrote word cloud → {wc_path}", file=sys.stderr)
            else:
                print(
                    "(word cloud skipped: install with `pip install wordcloud` "
                    "to auto-generate vault/wordcloud.png on the next build)",
                    file=sys.stderr,
                )
        return 0

    return 1


def _load_trainees_file(path: Path) -> list[str]:
    """Parse a trainees file: one name per line, blank lines and `#` comments ignored."""
    if not path.exists():
        print(f"  trainees-file not found: {path}", file=sys.stderr)
        return []
    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        names.append(line)
    return names


def _accept_thesis_hit(
    hit: dict, seen_ids: set[str], out: list[dict]
) -> None:
    """Defensively confirm the hit is a thesis, dedupe by _id, and append."""
    src = hit.get("_source") or {}
    genres = [(g or "").lower() for g in (src.get("genre") or [])]
    if not any("thesis" in g or "dissertation" in g for g in genres):
        return
    cid = hit.get("_id") or ""
    if cid and cid in seen_ids:
        return
    if cid:
        seen_ids.add(cid)
    out.append(hit)


def _coauthor_name_keys(works: list[dict]) -> set[str]:
    """Set of normalized author display names across all OpenAlex works.

    Used to filter cIRcle PI-mention hits to people Wellington has actually
    published with. The PI-mention leg is otherwise noisy: cIRcle's phrase
    match fires on examining-committee acknowledgments, surfacing theses
    whose author has no real Wellington connection.
    """
    keys: set[str] = set()
    for w in works:
        for a in pluck(w, "authorships", default=[]) or []:
            name = pluck(a, "author", "display_name", default="") or ""
            if name:
                keys.add(normalize_name(name))
    return keys


def _hit_creator_is_coauthor(hit: dict, coauthor_keys: set[str]) -> bool:
    """True if the hit's first creator (cIRcle "Surname, Forename") matches a
    known Wellington co-author by normalized name."""
    src = hit.get("_source") or {}
    creators = src.get("creator") or []
    if not creators:
        return False
    first = creators[0] if isinstance(creators[0], str) else ""
    if not first:
        return False
    return normalize_name(from_lastname_first(first)) in coauthor_keys


def _fetch_circle_theses(
    args: argparse.Namespace,
    works: list[dict],
    pi_name: str,
    pi_id: str | None = None,
) -> list[dict]:
    """Look up trainee theses on UBC cIRcle via three complementary legs.

    cIRcle does not expose its structured Supervisor field for querying, so
    no single signal catches every Wellington-supervised thesis. We union:

      1. **Co-authorship** — for each first-author of a paper where the PI is
         the last author, query `creator:"Surname, Forename"`. Catches
         trainees who published.
      2. **PI mention** — phrase-match the PI's full name across the index,
         then require the thesis creator to be a Wellington co-author from
         OpenAlex. Catches middle-author co-authors that leg 1 misses (leg 1
         is restricted to first-author-of-PI-last-author papers). The
         co-author filter is critical: cIRcle's phrase match also fires on
         theses where the PI is named only in the examining-committee
         acknowledgments, which are *not* Wellington-supervised theses.
      3. **Manual seed** — names from `--trainees-file` (one per line). The
         user-curated escape hatch for trainees who never co-authored a paper
         (so they're invisible to legs 1 and 2).

    Hits are deduplicated by `_id` and defensively re-checked for the
    `Thesis/Dissertation` genre (the Lucene filter on each query should
    already enforce this; defense in depth).
    """
    api_key = args.circle_api_key or os.environ.get("CIRCLE_API_KEY") or ""
    if not api_key:
        print(
            "(cIRcle ingestion skipped: no API key. Pass --circle-api-key or "
            "set CIRCLE_API_KEY env var. Register at "
            "https://open.library.ubc.ca/research)",
            file=sys.stderr,
        )
        return []

    client = CircleClient(
        api_key=api_key, cache_dir=args.circle_cache, refresh=args.refresh
    )
    seen_ids: set[str] = set()
    out: list[dict] = []

    # Leg 1 — co-authorship
    auto_candidates = extract_trainee_candidates(works, pi_name, pi_id=pi_id)
    if args.circle_max_trainees:
        auto_candidates = auto_candidates[: args.circle_max_trainees]

    # Leg 3 — manual seed (merged with auto, deduped, prepended so user-supplied
    # names are queried first when --circle-max-trainees is in play)
    manual_names: list[str] = []
    if args.trainees_file:
        manual_names = _load_trainees_file(args.trainees_file)
        print(f"  trainees-file: {len(manual_names)} name(s)", file=sys.stderr)

    seen_names: set[str] = set()
    candidates: list[str] = []
    for n in (*manual_names, *auto_candidates):
        key = n.lower()
        if key in seen_names:
            continue
        seen_names.add(key)
        candidates.append(n)

    print(
        f"cIRcle leg 1+3 (creator search): {len(candidates)} unique trainee "
        f"name(s) ({len(manual_names)} manual + {len(auto_candidates)} from "
        f"co-author graph); querying...",
        file=sys.stderr,
    )
    for cand in candidates:
        last_first = to_lastname_first(cand)
        try:
            hits = client.search_theses_by_creator(
                last_first, size=args.circle_hits_per_trainee
            )
        except CircleError as e:
            print(f"  cIRcle error for '{cand}': {e}", file=sys.stderr)
            continue
        for h in hits:
            _accept_thesis_hit(h, seen_ids, out)

    creator_leg_count = len(out)

    # Leg 2 — PI mention (phrase match), filtered to Wellington co-authors.
    # Without the co-author filter, this leg false-positives on theses where
    # the PI is acknowledged only as an examining-committee member.
    coauthor_keys = _coauthor_name_keys(works)
    print(
        f"cIRcle leg 2 (PI-name phrase match, filtered to known co-authors): "
        f"querying \"{pi_name}\" against {len(coauthor_keys)} co-authors...",
        file=sys.stderr,
    )
    try:
        mention_hits = client.search_theses_mentioning(
            pi_name, size=args.circle_pi_mention_size
        )
    except CircleError as e:
        print(f"  cIRcle PI-mention error: {e}", file=sys.stderr)
        mention_hits = []
    rejected = 0
    for h in mention_hits:
        if not _hit_creator_is_coauthor(h, coauthor_keys):
            rejected += 1
            continue
        _accept_thesis_hit(h, seen_ids, out)
    print(
        f"  PI-mention hits: {len(mention_hits)} fetched, "
        f"{rejected} rejected (creator not a Wellington co-author).",
        file=sys.stderr,
    )

    print(
        f"cIRcle: {len(out)} unique theses retrieved "
        f"({creator_leg_count} from creator search + "
        f"{len(out) - creator_leg_count} new from PI-name match).",
        file=sys.stderr,
    )
    return out


def _format_author(a: dict) -> str:
    insts = ", ".join(
        (inst.get("display_name") or "?")
        for inst in (a.get("last_known_institutions") or [])
    ) or "(no institution)"
    return (
        f"{a.get('display_name')} | id={a.get('id')} | works={a.get('works_count')} | "
        f"cites={a.get('cited_by_count')} | orcid={a.get('orcid') or '-'} | {insts}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
