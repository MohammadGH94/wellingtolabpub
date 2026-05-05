"""CLI entry point: `python -m wellington_vault build [...]`."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .build import build_indexes, extract_trainee_candidates, resolve_author, write_vault
from .circle import CircleClient, CircleError, to_lastname_first
from .openalex import OpenAlexClient
from .util import pluck


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

        indexes = build_indexes(works)
        print(
            f"Indexed: {len(indexes['by_person'])} unique authors, "
            f"{len(indexes['by_topic'])} unique topics.",
            file=sys.stderr,
        )

        pi_name = author.get("display_name") or args.author_name
        circle_theses = _fetch_circle_theses(args, works, pi_name)

        stats = write_vault(
            works, indexes, pi_name, args.out,
            dry_run=args.dry_run, circle_theses=circle_theses,
        )
        action = "Would write" if args.dry_run else "Wrote"
        print(
            f"{action}: {stats['papers']} papers, {stats['theses']} theses, "
            f"{stats['people']} people, {stats['topics']} topics → {args.out}/",
            file=sys.stderr,
        )
        return 0

    return 1


def _fetch_circle_theses(
    args: argparse.Namespace, works: list[dict], pi_name: str
) -> list[dict]:
    """Look up trainee theses on UBC cIRcle. Returns list of ES hits.

    A trainee candidate is the first author of any paper where the PI is the
    last author (canonical life-sciences authorship: PI last, lead trainee
    first). We dedupe by `_id` across all queries and skip non-thesis hits
    defensively (the Lucene `genre` filter should already exclude them).
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

    candidates = extract_trainee_candidates(works, pi_name)
    if args.circle_max_trainees:
        candidates = candidates[: args.circle_max_trainees]
    print(
        f"cIRcle: {len(candidates)} trainee candidate(s) from co-author graph; "
        f"querying...",
        file=sys.stderr,
    )

    client = CircleClient(
        api_key=api_key, cache_dir=args.circle_cache, refresh=args.refresh
    )
    seen_ids: set[str] = set()
    out: list[dict] = []
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
            src = h.get("_source") or {}
            genres = [(g or "").lower() for g in (src.get("genre") or [])]
            if not any("thesis" in g or "dissertation" in g for g in genres):
                continue
            cid = h.get("_id") or ""
            if cid and cid in seen_ids:
                continue
            if cid:
                seen_ids.add(cid)
            out.append(h)
    print(f"cIRcle: {len(out)} unique theses retrieved.", file=sys.stderr)
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
