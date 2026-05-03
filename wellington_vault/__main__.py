"""CLI entry point: `python -m wellington_vault build [...]`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .build import build_indexes, resolve_author, write_vault
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
        stats = write_vault(works, indexes, pi_name, args.out, dry_run=args.dry_run)
        action = "Would write" if args.dry_run else "Wrote"
        print(
            f"{action}: {stats['papers']} papers, {stats['people']} people, "
            f"{stats['topics']} topics → {args.out}/",
            file=sys.stderr,
        )
        return 0

    return 1


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
