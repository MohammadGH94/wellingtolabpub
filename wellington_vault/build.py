"""Orchestrate: resolve author → fetch works → render notes."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from . import notes
from .openalex import OpenAlexClient
from .util import pluck


def resolve_author(
    client: OpenAlexClient, name: str, institution_hint: str | None
) -> dict:
    candidates = client.search_authors(name, institution_hint=institution_hint)
    if not candidates:
        candidates = client.search_authors(name, institution_hint=None)
    if not candidates:
        raise SystemExit(f"No OpenAlex author found for '{name}'.")

    candidates.sort(key=lambda a: a.get("works_count") or 0, reverse=True)

    print(f"Top candidates for '{name}':", file=sys.stderr)
    for i, a in enumerate(candidates[:5]):
        insts = ", ".join(
            (inst.get("display_name") or "?")
            for inst in (a.get("last_known_institutions") or [])
        ) or "(no institution on record)"
        concepts = ", ".join(
            c.get("display_name", "?") for c in (a.get("x_concepts") or [])[:3]
        )
        print(
            f"  [{i}] {a.get('display_name')} | works: {a.get('works_count')} | "
            f"cites: {a.get('cited_by_count')} | {insts} | {concepts}",
            file=sys.stderr,
        )

    return candidates[0]


def build_indexes(works: list[dict]) -> dict[str, Any]:
    by_person: dict[str, list[dict]] = defaultdict(list)
    by_topic: dict[str, dict[str, Any]] = {}
    for w in works:
        for a in pluck(w, "authorships", default=[]) or []:
            name = pluck(a, "author", "display_name", default="")
            if name:
                by_person[name].append(w)
        for c in pluck(w, "concepts", default=[]) or []:
            score = c.get("score") or 0
            level = c.get("level") or 0
            if score < 0.3 or level < 1:
                continue
            display = c.get("display_name")
            if not display:
                continue
            entry = by_topic.setdefault(
                display,
                {"name": display, "wikidata": c.get("wikidata"), "papers": []},
            )
            entry["papers"].append(w)
    return {"by_person": dict(by_person), "by_topic": by_topic}


def write_vault(
    works: list[dict],
    indexes: dict[str, Any],
    pi_name: str,
    out_dir: Path,
    dry_run: bool = False,
) -> dict[str, int]:
    papers_dir = out_dir / "papers"
    people_dir = out_dir / "people"
    topics_dir = out_dir / "topics"
    theses_dir = out_dir / "theses"

    if not dry_run:
        for d in (papers_dir, people_dir, topics_dir, theses_dir):
            d.mkdir(parents=True, exist_ok=True)

    stats = {"papers": 0, "people": 0, "topics": 0, "theses": 0}

    for w in works:
        if notes.is_thesis(w):
            path = theses_dir / f"{notes.thesis_filename(w)}.md"
            content = notes.render_thesis_note(w)
            stats["theses"] += 1
        else:
            path = papers_dir / f"{notes.paper_filename(w)}.md"
            content = notes.render_paper_note(w)
            stats["papers"] += 1
        _write(path, content, dry_run)

    for name, papers in indexes["by_person"].items():
        is_pi = name.lower() == pi_name.lower()
        path = people_dir / f"{notes.person_filename(name)}.md"
        content = notes.render_person_note(name, papers, is_pi=is_pi)
        _write(path, content, dry_run)
        stats["people"] += 1

    for entry in indexes["by_topic"].values():
        path = topics_dir / f"{notes.topic_filename(entry['name'])}.md"
        content = notes.render_topic_note(
            entry["name"], entry["papers"], wikidata_id=entry.get("wikidata")
        )
        _write(path, content, dry_run)
        stats["topics"] += 1

    index_path = out_dir / "index.md"
    _write(index_path, notes.render_index(stats, pi_name), dry_run)

    return stats


def _write(path: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        print(f"DRY-RUN would write: {path} ({len(content)} bytes)", file=sys.stderr)
        return
    path.write_text(content, encoding="utf-8")
