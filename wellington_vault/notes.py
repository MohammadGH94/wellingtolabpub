"""Render OpenAlex records as AI-first Obsidian notes.

Every note follows the 7 rules from
.claude/skills/obsidian-second-brain/references/ai-first-rules.md:

  1. Self-contained context
  2. `## For future Claude` preamble (2-3 sentences)
  3. Rich frontmatter with `ai-first: true`
  4. Recency markers per claim
  5. Source URLs preserved verbatim
  6. [[wikilinks]] for every cross-reference
  7. Confidence levels where applicable
"""

from __future__ import annotations

import re
from typing import Any

from .util import frontmatter, pluck, reconstruct_abstract, slugify, today_iso, wikilink

PI_NAME = "Cheryl Wellington"
PROVENANCE = "openalex.org"

# OpenAlex `type` values that we treat as theses (route to `theses/` instead
# of `papers/`). OpenAlex's canonical type for a doctoral dissertation is
# "dissertation"; "thesis" is accepted defensively in case older records use it.
THESIS_TYPES = frozenset({"dissertation", "thesis"})


# ── Filename helpers ────────────────────────────────────────────────────────


def is_thesis(work: dict) -> bool:
    return (pluck(work, "type", default="") or "").lower() in THESIS_TYPES


def paper_filename(work: dict) -> str:
    year = pluck(work, "publication_year", default="n.d.")
    title = pluck(work, "title", default="Untitled") or "Untitled"
    return f"{year} — {slugify(title, max_len=90)}"


def thesis_filename(work: dict) -> str:
    year = pluck(work, "publication_year", default="n.d.")
    title = pluck(work, "title", default="Untitled") or "Untitled"
    return f"{year} — {slugify(title, max_len=90)}"


def circle_thesis_filename(hit: dict) -> str:
    src = hit.get("_source") or {}
    title = (src.get("title") or ["Untitled"])[0] or "Untitled"
    year = circle_year(src) or "n.d."
    return f"{year} — {slugify(title, max_len=90)}"


def circle_year(src: dict) -> int | None:
    """Best-effort year extraction from a cIRcle _source.

    Prefers `ubc_date_sort` (e.g. '1993-12-31 AD') over `dateAvailable`
    (the date the record entered Open Collections, often years later).
    """
    for raw in (src.get("ubc_date_sort"), src.get("dateAvailable")):
        if not raw:
            continue
        m = re.match(r"(\d{4})", str(raw))
        if m:
            return int(m.group(1))
    return None


def person_filename(author_display_name: str) -> str:
    return slugify(author_display_name, max_len=80)


def topic_filename(concept_display_name: str) -> str:
    return slugify(concept_display_name, max_len=80)


# ── Renderers ───────────────────────────────────────────────────────────────


def render_paper_note(work: dict) -> str:
    title = pluck(work, "title", default="Untitled") or "Untitled"
    year = pluck(work, "publication_year", default=None)
    pub_date = pluck(work, "publication_date", default="")
    work_type = pluck(work, "type", default="article")
    doi = pluck(work, "doi", default="")
    openalex_id = pluck(work, "id", default="")
    cited_by = pluck(work, "cited_by_count", default=0)
    is_oa = bool(pluck(work, "open_access", "is_oa", default=False))
    oa_url = pluck(work, "open_access", "oa_url", default="") or ""
    venue = (
        pluck(work, "primary_location", "source", "display_name", default="")
        or pluck(work, "host_venue", "display_name", default="")
        or ""
    )
    venue_type = pluck(work, "primary_location", "source", "type", default="") or ""
    abstract = reconstruct_abstract(pluck(work, "abstract_inverted_index", default=None))

    authorships = pluck(work, "authorships", default=[]) or []
    author_names = [
        pluck(a, "author", "display_name", default="") for a in authorships
    ]
    author_names = [n for n in author_names if n]
    author_links = [wikilink(person_filename(n), n) for n in author_names]

    concepts_raw = pluck(work, "concepts", default=[]) or []
    top_concepts = [
        c for c in concepts_raw
        if (c.get("score") or 0) >= 0.3 and (c.get("level") or 0) >= 1
    ][:8]
    concept_links = [
        wikilink(topic_filename(c.get("display_name") or ""), c.get("display_name"))
        for c in top_concepts
        if c.get("display_name")
    ]

    pi_present = any(
        PI_NAME.lower() in (n or "").lower() for n in author_names
    )
    role = (
        "first-author" if author_names and PI_NAME.lower() in author_names[0].lower()
        else "last-author" if author_names and PI_NAME.lower() in author_names[-1].lower()
        else "co-author" if pi_present
        else "unknown"
    )

    fm: dict[str, Any] = {
        "date": today_iso(),
        "type": "paper",
        "tags": ["paper", "wellington-lab", f"year-{year}" if year else "year-unknown"],
        "title": title,
        "year": year,
        "publication_date": pub_date,
        "work_type": work_type,
        "venue": venue,
        "venue_type": venue_type,
        "doi": doi or "",
        "openalex_id": openalex_id,
        "open_access": is_oa,
        "oa_url": oa_url,
        "cited_by_count": cited_by,
        "wellington_role": role,
        "authors": author_links,
        "topics": concept_links,
        "ai-first": True,
        "confidence": "stated",
    }

    body_lines: list[str] = []
    body_lines.append("")
    body_lines.append("## For future Claude")
    role_phrase = {
        "first-author": f"{PI_NAME} is first author",
        "last-author": f"{PI_NAME} is last/senior author (typical PI position)",
        "co-author": f"{PI_NAME} is a co-author",
        "unknown": f"role of {PI_NAME} on this paper is unclear from metadata",
    }[role]
    preamble = (
        f"This is a paper note for \"{title}\" ({year}), published in "
        f"{venue or 'an unspecified venue'}. {role_phrase}. Metadata sourced from "
        f"{PROVENANCE} (as of {today_iso()}); abstract reconstructed from OpenAlex's "
        f"inverted index. Verify via DOI before citing externally."
    )
    body_lines.append(preamble)
    body_lines.append("")

    body_lines.append("## Citation")
    if author_names:
        body_lines.append(f"- Authors: {', '.join(author_links)}")
    if year:
        body_lines.append(f"- Year: {year}{' (' + pub_date + ')' if pub_date else ''}")
    if venue:
        body_lines.append(f"- Venue: {venue}{' — ' + venue_type if venue_type else ''}")
    if doi:
        doi_url = doi if doi.startswith("http") else f"https://doi.org/{doi.lstrip('/')}"
        body_lines.append(f"- DOI: {doi_url}")
    if openalex_id:
        body_lines.append(f"- OpenAlex: {openalex_id}")
    if is_oa and oa_url:
        body_lines.append(f"- Open access: {oa_url}")
    body_lines.append(f"- Cited by: {cited_by} (as of {today_iso()}, {PROVENANCE})")
    body_lines.append("")

    if abstract:
        body_lines.append("## Abstract")
        body_lines.append(
            f"> Reconstructed from OpenAlex inverted index — word order is correct, "
            f"punctuation may be approximate."
        )
        body_lines.append("")
        body_lines.append(abstract)
        body_lines.append("")

    if concept_links:
        body_lines.append("## Topics")
        for c, link in zip(top_concepts, concept_links):
            score = c.get("score")
            score_str = f" (score: {score:.2f})" if isinstance(score, (int, float)) else ""
            body_lines.append(f"- {link}{score_str}")
        body_lines.append("")

    return frontmatter(fm) + "\n".join(body_lines).rstrip() + "\n"


def render_thesis_note(work: dict) -> str:
    title = pluck(work, "title", default="Untitled") or "Untitled"
    year = pluck(work, "publication_year", default=None)
    pub_date = pluck(work, "publication_date", default="")
    work_type = pluck(work, "type", default="dissertation") or "dissertation"
    doi = pluck(work, "doi", default="")
    openalex_id = pluck(work, "id", default="")
    is_oa = bool(pluck(work, "open_access", "is_oa", default=False))
    oa_url = pluck(work, "open_access", "oa_url", default="") or ""
    institution = (
        pluck(work, "primary_location", "source", "display_name", default="")
        or pluck(work, "host_venue", "display_name", default="")
        or ""
    )
    abstract = reconstruct_abstract(pluck(work, "abstract_inverted_index", default=None))

    authorships = pluck(work, "authorships", default=[]) or []
    author_names = [
        pluck(a, "author", "display_name", default="") for a in authorships
    ]
    author_names = [n for n in author_names if n]
    author_links = [wikilink(person_filename(n), n) for n in author_names]

    concepts_raw = pluck(work, "concepts", default=[]) or []
    top_concepts = [
        c for c in concepts_raw
        if (c.get("score") or 0) >= 0.3 and (c.get("level") or 0) >= 1
    ][:8]
    concept_links = [
        wikilink(topic_filename(c.get("display_name") or ""), c.get("display_name"))
        for c in top_concepts
        if c.get("display_name")
    ]

    candidate = author_names[0] if author_names else ""
    pi_present = any(
        PI_NAME.lower() in (n or "").lower() for n in author_names
    )

    fm: dict[str, Any] = {
        "date": today_iso(),
        "type": "thesis",
        "tags": ["thesis", "wellington-lab", f"year-{year}" if year else "year-unknown"],
        "title": title,
        "year": year,
        "publication_date": pub_date,
        "work_type": work_type,
        "institution": institution,
        "doi": doi or "",
        "openalex_id": openalex_id,
        "open_access": is_oa,
        "oa_url": oa_url,
        "candidate": candidate,
        "authors": author_links,
        "wellington_listed": pi_present,
        "topics": concept_links,
        "ai-first": True,
        "confidence": "stated",
    }

    role_phrase = (
        f"{PI_NAME} appears in the OpenAlex authorship list (typically supervisor "
        f"or committee member for a {work_type})."
        if pi_present else
        f"{PI_NAME} is not listed in OpenAlex authorship — this {work_type} surfaces "
        f"via the lab's co-authorship graph."
    )
    preamble = (
        f"This is a thesis note for \"{title}\" ({year or 'n.d.'}), a {work_type} "
        f"from {institution or 'an unspecified institution'}. {role_phrase} Metadata "
        f"sourced from {PROVENANCE} (as of {today_iso()}); abstract reconstructed from "
        f"OpenAlex's inverted index when present. UBC cIRcle ingestion is a planned "
        f"follow-up that will enrich this with the official thesis record."
    )

    body_lines: list[str] = [
        "",
        "## For future Claude",
        preamble,
        "",
        "## Citation",
    ]
    if candidate:
        body_lines.append(
            f"- Candidate: {wikilink(person_filename(candidate), candidate)}"
        )
    if author_names:
        body_lines.append(f"- Listed authors: {', '.join(author_links)}")
    if year:
        body_lines.append(f"- Year: {year}{' (' + pub_date + ')' if pub_date else ''}")
    if institution:
        body_lines.append(f"- Institution: {institution}")
    if doi:
        doi_url = doi if doi.startswith("http") else f"https://doi.org/{doi.lstrip('/')}"
        body_lines.append(f"- DOI: {doi_url}")
    if openalex_id:
        body_lines.append(f"- OpenAlex: {openalex_id}")
    if is_oa and oa_url:
        body_lines.append(f"- Open access: {oa_url}")
    body_lines.append("")

    if abstract:
        body_lines.append("## Abstract")
        body_lines.append(
            f"> Reconstructed from OpenAlex inverted index — word order is correct, "
            f"punctuation may be approximate."
        )
        body_lines.append("")
        body_lines.append(abstract)
        body_lines.append("")

    if concept_links:
        body_lines.append("## Topics")
        for c, link in zip(top_concepts, concept_links):
            score = c.get("score")
            score_str = f" (score: {score:.2f})" if isinstance(score, (int, float)) else ""
            body_lines.append(f"- {link}{score_str}")
        body_lines.append("")

    return frontmatter(fm) + "\n".join(body_lines).rstrip() + "\n"


def render_circle_thesis_note(hit: dict) -> str:
    """Render a thesis note from a UBC Open Collections (cIRcle) ES hit.

    `hit` is the full ES envelope: `{"_id": ..., "_index": ..., "_source": {...}}`.
    The OC index uses lowercased Solr-style field names (`creator`, `title`,
    `description`, `genre`, `degree`, `program`, `affiliation`, `subject`,
    `campus`, `scholarlyLevel`, `ubc_date_sort`).
    """
    from .circle import from_lastname_first

    src = hit.get("_source") or {}
    oc_id = hit.get("_id") or ""

    title = (src.get("title") or ["Untitled"])[0] or "Untitled"
    creators = [c for c in (src.get("creator") or []) if c]
    candidate_lf = creators[0] if creators else ""
    candidate = from_lastname_first(candidate_lf)
    abstract = (src.get("description") or [""])[0] or ""
    degrees = [d for d in (src.get("degree") or []) if d]
    programs = [p for p in (src.get("program") or []) if p]
    affiliations = [a for a in (src.get("affiliation") or []) if a]
    subjects = [s for s in (src.get("subject") or []) if s]
    campus = (src.get("campus") or [""])[0] or ""
    scholarly = (src.get("scholarlyLevel") or [""])[0] or ""
    year = circle_year(src)

    handle_url = (
        f"https://open.library.ubc.ca/collections/ubctheses/items/{oc_id}"
        if oc_id else ""
    )

    # Wikilinks to person notes use OpenAlex display-name format ("Forename
    # Surname") so they resolve to notes generated from the OpenAlex co-author
    # graph; cIRcle's "Surname, Forename" is converted first.
    creator_links = [
        wikilink(person_filename(from_lastname_first(c)), from_lastname_first(c))
        for c in creators
    ]
    subject_links = [
        wikilink(topic_filename(s), s) for s in subjects
    ]

    fm: dict[str, Any] = {
        "date": today_iso(),
        "type": "thesis",
        "tags": ["thesis", "wellington-lab", f"year-{year}" if year else "year-unknown"],
        "title": title,
        "year": year,
        "candidate": candidate,
        "authors": creator_links,
        "degree": degrees[0] if degrees else "",
        "program": programs[0] if programs else "",
        "affiliations": affiliations,
        "campus": campus,
        "scholarly_level": scholarly,
        "institution": "University of British Columbia",
        "circle_id": oc_id,
        "circle_url": handle_url,
        "topics": subject_links,
        "ai-first": True,
        "confidence": "stated",
        "source": "ubc-circle",
    }

    program_str = programs[0] if programs else "an unspecified program"
    degree_str = degrees[0] if degrees else "graduate"
    candidate_link = (
        wikilink(person_filename(candidate), candidate) if candidate else "an unknown candidate"
    )

    body_lines = [
        "",
        "## For future Claude",
        (
            f"This is a thesis note for \"{title}\" ({year or 'n.d.'}), a UBC "
            f"{degree_str} thesis by {candidate_link} in {program_str}. Surfaced by "
            f"matching the candidate against the Wellington-lab co-authorship graph "
            f"(OpenAlex), then retrieved from UBC cIRcle (open.library.ubc.ca). "
            f"cIRcle's structured Supervisor field is not exposed in the public "
            f"index, so for any thesis Wellington's role as supervisor is INFERRED "
            f"from the co-author relationship — verify by reading the thesis's "
            f"acknowledgments before citing externally. Metadata as of {today_iso()}."
        ),
        "",
        "## Citation",
    ]
    if candidate:
        body_lines.append(f"- Candidate: {candidate_link}")
    if year:
        body_lines.append(f"- Year: {year}")
    if degrees:
        body_lines.append(f"- Degree: {degrees[0]}")
    if programs:
        body_lines.append(f"- Program: {programs[0]}")
    if affiliations:
        body_lines.append(f"- Affiliation(s): {'; '.join(affiliations)}")
    if campus:
        body_lines.append(f"- Campus: {campus}")
    body_lines.append("- Institution: University of British Columbia")
    if oc_id:
        body_lines.append(f"- cIRcle ID: {oc_id}")
    if handle_url:
        body_lines.append(f"- URL: {handle_url}")
    body_lines.append(f"- Source: open.library.ubc.ca (as of {today_iso()})")
    body_lines.append("")

    if abstract:
        body_lines.append("## Abstract")
        body_lines.append(abstract)
        body_lines.append("")

    if subject_links:
        body_lines.append("## Subjects (cIRcle)")
        for link in subject_links:
            body_lines.append(f"- {link}")
        body_lines.append("")

    return frontmatter(fm) + "\n".join(body_lines).rstrip() + "\n"


def render_person_note(name: str, papers: list[dict], is_pi: bool = False) -> str:
    paper_links = [wikilink(paper_filename(w), pluck(w, "title", default="Untitled"))
                   for w in papers]
    years = sorted(
        {pluck(w, "publication_year") for w in papers if pluck(w, "publication_year")}
    )
    first_year = years[0] if years else None
    last_year = years[-1] if years else None
    paper_count = len(papers)

    role = "principal-investigator" if is_pi else "co-author"
    fm: dict[str, Any] = {
        "date": today_iso(),
        "type": "person",
        "tags": ["person", "wellington-lab"],
        "name": name,
        "role": role,
        "papers_with_wellington_lab": paper_count,
        "first_co_pub_year": first_year,
        "last_co_pub_year": last_year,
        "ai-first": True,
        "confidence": "stated",
    }

    role_summary = (
        f"PI of the Wellington lab at the University of British Columbia"
        if is_pi else
        f"co-author with {wikilink(person_filename(PI_NAME), PI_NAME)} on {paper_count} "
        f"OpenAlex-indexed paper{'s' if paper_count != 1 else ''}"
    )
    span = (
        f" Co-publication span: {first_year}–{last_year}."
        if first_year and last_year and first_year != last_year
        else f" Co-publication year: {first_year}." if first_year else ""
    )

    body = [
        "",
        "## For future Claude",
        f"Person note for {name}, {role_summary}.{span} Built from {PROVENANCE} "
        f"co-authorship metadata (as of {today_iso()}). Affiliations and current role "
        f"NOT captured here — re-derive from OpenAlex `/authors` if needed.",
        "",
        "## Co-authored papers",
    ]
    sorted_papers = sorted(
        papers,
        key=lambda w: (pluck(w, "publication_year") or 0, pluck(w, "title") or ""),
        reverse=True,
    )
    for w in sorted_papers:
        title = pluck(w, "title", default="Untitled")
        y = pluck(w, "publication_year") or "n.d."
        venue = pluck(w, "primary_location", "source", "display_name", default="") or ""
        body.append(f"- {wikilink(paper_filename(w), title)} — {y}{' · ' + venue if venue else ''}")
    body.append("")

    return frontmatter(fm) + "\n".join(body).rstrip() + "\n"


def render_topic_note(name: str, papers: list[dict], wikidata_id: str | None = None) -> str:
    paper_count = len(papers)
    years = sorted(
        {pluck(w, "publication_year") for w in papers if pluck(w, "publication_year")}
    )
    first_year = years[0] if years else None
    last_year = years[-1] if years else None

    fm: dict[str, Any] = {
        "date": today_iso(),
        "type": "topic",
        "tags": ["topic", "wellington-lab"],
        "name": name,
        "wikidata": wikidata_id or "",
        "wellington_lab_papers": paper_count,
        "first_year": first_year,
        "last_year": last_year,
        "ai-first": True,
        "confidence": "stated",
    }

    body = [
        "",
        "## For future Claude",
        f"Topic note for \"{name}\" — an OpenAlex concept tagged on {paper_count} "
        f"Wellington-lab paper{'s' if paper_count != 1 else ''} "
        f"({first_year or '?'}–{last_year or '?'}). Topic taxonomy is OpenAlex's, "
        f"derived from MAG concepts (as of {today_iso()}). Two papers tagged with the same "
        f"topic do not necessarily address it as their primary subject — check per-paper score.",
        "",
        "## Wellington-lab papers tagged with this topic",
    ]
    sorted_papers = sorted(
        papers,
        key=lambda w: (pluck(w, "publication_year") or 0, pluck(w, "title") or ""),
        reverse=True,
    )
    for w in sorted_papers:
        title = pluck(w, "title", default="Untitled")
        y = pluck(w, "publication_year") or "n.d."
        body.append(f"- {wikilink(paper_filename(w), title)} — {y}")
    body.append("")

    return frontmatter(fm) + "\n".join(body).rstrip() + "\n"


def render_index(stats: dict[str, int], pi_name: str = PI_NAME) -> str:
    fm: dict[str, Any] = {
        "date": today_iso(),
        "type": "index",
        "tags": ["index", "wellington-lab"],
        "ai-first": True,
    }
    body = [
        "",
        "## For future Claude",
        f"This is the front door to the Wellington-lab vault. Read it first. "
        f"It catalogs every folder and gives current counts as of {today_iso()}. "
        f"All publication and authorship data sourced from {PROVENANCE}; theses "
        f"sourced separately if/when ingested.",
        "",
        "## Vault layout",
        "",
        "| Folder | Contents | Count |",
        "|---|---|---|",
        f"| `papers/` | One note per Wellington-lab publication | {stats.get('papers', 0)} |",
        f"| `people/` | One note per author (PI + co-authors + trainees) | {stats.get('people', 0)} |",
        f"| `topics/` | One note per OpenAlex concept tagged on the lab's papers | {stats.get('topics', 0)} |",
        f"| `theses/` | One note per UBC student thesis (best-effort, may be empty) | {stats.get('theses', 0)} |",
        "",
        "## PI",
        f"- {wikilink(person_filename(pi_name), pi_name)} — Principal Investigator",
        "",
        "## How to navigate",
        "- Open the graph view in Obsidian to see clusters by topic and co-author network.",
        "- Each paper note's frontmatter has `wellington_role: first-author | last-author | co-author` "
        "to filter PI-led work vs. collaborations.",
        "- `cited_by_count` is a snapshot at vault-build time and will drift — "
        "re-run the ingest periodically.",
        "",
        "## Data provenance",
        f"- Built from {PROVENANCE} (as of {today_iso()}, {PROVENANCE})",
        "- Source repo: https://github.com/MohammadGH94/wellingtolabpub",
        "- Rebuild command: `python -m wellington_vault build --refresh`",
        "",
    ]
    return frontmatter(fm) + "\n".join(body).rstrip() + "\n"
