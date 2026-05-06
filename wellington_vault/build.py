"""Orchestrate: resolve author → fetch works → render notes."""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from . import notes
from .openalex import OpenAlexClient
from .util import normalize_name, pluck


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


def _aid(authorship: dict) -> str:
    """Extract bare OpenAlex author ID ("A12345") from an authorship dict."""
    raw = pluck(authorship, "author", "id", default="") or ""
    return raw.rstrip("/").rsplit("/", 1)[-1]


def canonicalize_authorships(works: list[dict]) -> dict[str, str]:
    """Collapse author display-name variants by keying on OpenAlex author IDs.

    OpenAlex returns the same author with different display-name spellings on
    different papers ("Cheryl Wellington" vs "Cheryl L. Wellington"; "Jennifer
    Cooper" vs "Jennifer G. Cooper" vs "Jennifer G Cooper"). Each variant is
    backed by the same stable `author.id` (e.g. A5065510480), so we group on
    ID and pick one canonical display name per person.

    Mutates each authorship in-place to carry the canonical name. Authors
    with no `author.id` (rare; malformed records) are left as-is.

    Returns a name-resolution map covering both observed display-name
    variants AND their case/punctuation-normalized forms, all pointing at
    the canonical display name. Used downstream by the cIRcle renderer
    (which has a name string from cIRcle but no OpenAlex ID).
    """
    name_counts_by_aid: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for w in works:
        for a in pluck(w, "authorships", default=[]) or []:
            aid = _aid(a)
            name = pluck(a, "author", "display_name", default="") or ""
            if not name or not aid:
                continue
            name_counts_by_aid[aid][name] += 1

    # Pick canonical name per author ID: most-frequent variant, ties broken
    # by length (prefers "Cheryl L. Wellington" over "Cheryl Wellington").
    canonical_by_aid: dict[str, str] = {}
    for aid, counts in name_counts_by_aid.items():
        canonical_by_aid[aid] = sorted(
            counts.items(), key=lambda kv: (-kv[1], -len(kv[0]))
        )[0][0]

    # Mutate authorships in place.
    for w in works:
        for a in pluck(w, "authorships", default=[]) or []:
            aid = _aid(a)
            if not aid:
                continue
            canon = canonical_by_aid.get(aid)
            if canon and isinstance(a.get("author"), dict):
                a["author"]["display_name"] = canon

    # Build the name-resolution map (display variant + normalized form → canon).
    name_map: dict[str, str] = {}
    for aid, counts in name_counts_by_aid.items():
        canon = canonical_by_aid[aid]
        for variant in counts:
            name_map[variant] = canon
            name_map[normalize_name(variant)] = canon
    return name_map


def extract_trainee_candidates(
    works: list[dict], pi_name: str, pi_id: str | None = None
) -> list[str]:
    """Return display names that look like Wellington-lab trainees.

    Heuristic: the first author of any paper where the PI is the last author.
    In life-sciences convention the last author is the PI and the first
    author is the lead trainee (postdoc/PhD/MSc) for that work.

    PI matching uses `pi_id` (OpenAlex author ID, e.g. "A5065510480") when
    available — this is exact and survives display-name variants. Falls back
    to substring match on `pi_name` only if `pi_id` is missing.

    Returned in descending frequency order so trainees on multiple lab papers
    are searched first when downstream callers cap the cIRcle query count.
    """
    pi_lower = (pi_name or "").lower()
    counts: dict[str, int] = {}
    for w in works:
        authorships = pluck(w, "authorships", default=[]) or []
        if len(authorships) < 2:
            continue
        last = authorships[-1]
        first = authorships[0]
        last_name = pluck(last, "author", "display_name", default="") or ""
        first_name = pluck(first, "author", "display_name", default="") or ""
        if not first_name:
            continue
        if pi_id:
            if _aid(last) != pi_id:
                continue
            if _aid(first) == pi_id:
                continue
        else:
            if pi_lower not in last_name.lower():
                continue
            if pi_lower in first_name.lower():
                continue
        counts[first_name] = counts.get(first_name, 0) + 1
    return sorted(counts.keys(), key=lambda n: counts[n], reverse=True)


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
    circle_theses: list[dict] | None = None,
    pi_id: str | None = None,
    canonical_names: dict[str, str] | None = None,
) -> dict[str, int]:
    papers_dir = out_dir / "papers"
    people_dir = out_dir / "people"
    topics_dir = out_dir / "topics"
    theses_dir = out_dir / "theses"

    if not dry_run:
        for d in (papers_dir, people_dir, topics_dir, theses_dir):
            d.mkdir(parents=True, exist_ok=True)

    stats = {"papers": 0, "people": 0, "topics": 0, "theses": 0}

    # Canonicalize the PI's own display name (the by_person index keys are
    # canonical post-canonicalize_authorships, so the simple name comparison
    # below requires the same form on both sides).
    pi_name_canonical = (
        (canonical_names or {}).get(pi_name)
        or (canonical_names or {}).get(normalize_name(pi_name))
        or pi_name
    )

    for w in works:
        if notes.is_thesis(w):
            path = theses_dir / f"{notes.thesis_filename(w)}.md"
            content = notes.render_thesis_note(w, pi_id=pi_id)
            stats["theses"] += 1
        else:
            path = papers_dir / f"{notes.paper_filename(w)}.md"
            content = notes.render_paper_note(w, pi_id=pi_id)
            stats["papers"] += 1
        _write(path, content, dry_run)

    # cIRcle theses are written after OpenAlex dissertations so the cIRcle
    # record (the authoritative thesis source) wins on filename collision.
    for hit in circle_theses or []:
        path = theses_dir / f"{notes.circle_thesis_filename(hit)}.md"
        content = notes.render_circle_thesis_note(hit, canonical_names=canonical_names)
        _write(path, content, dry_run)
        stats["theses"] += 1

    for name, papers in indexes["by_person"].items():
        is_pi = name == pi_name_canonical or name.lower() == pi_name.lower()
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
