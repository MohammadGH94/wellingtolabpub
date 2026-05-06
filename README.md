# wellingtolabpub

An Obsidian second-brain vault of every publication (and eventually thesis) from
**Dr. Cheryl Wellington's lab** at the University of British Columbia, plus the
ingest tooling that builds it from OpenAlex.

The vault is **AI-first**: notes are written for future-Claude to retrieve and
reason over, not for human reading. Every note has rich frontmatter, a `## For
future Claude` preamble, recency-marked claims, source URLs, and `[[wikilinks]]`
to every cross-reference — see `.claude/skills/obsidian-second-brain/references/ai-first-rules.md`.

---

## Repo layout

```
wellingtolabpub/
├── vault/                     ← the Obsidian vault (open this in Obsidian)
│   ├── _CLAUDE.md             ← Claude's operating manual for the vault
│   ├── index.md               ← front door (auto-generated on build)
│   ├── log.md                 ← append-only build log
│   ├── papers/                ← one note per publication (auto-generated)
│   ├── people/                ← one note per author (auto-generated)
│   ├── topics/                ← one note per OpenAlex concept (auto-generated)
│   └── theses/                ← one note per UBC cIRcle thesis by a lab trainee (auto-generated)
│
├── wellington_vault/          ← Python ingest package (stdlib-only)
│   ├── openalex.py            ← OpenAlex client with on-disk cache
│   ├── circle.py              ← UBC cIRcle (Open Collections) client
│   ├── notes.py               ← AI-first markdown emitters
│   ├── build.py               ← orchestration
│   └── __main__.py            ← CLI entry point
│
└── .claude/skills/obsidian-second-brain/
                               ← installed Claude Code skill that operates on the vault
```

---

## Quick start

Requires **Python 3.10+** (no third-party packages — pure stdlib).

```bash
# Resolve the OpenAlex author and print top candidates (no writes)
python -m wellington_vault resolve

# Full build — fetches every Wellington-lab paper, renders the vault
python -m wellington_vault build --mailto you@example.com

# Same, but also retrieve trainee theses from UBC cIRcle (recommended)
$env:CIRCLE_API_KEY = "your-key"  # PowerShell — register at https://open.library.ubc.ca/research
python -m wellington_vault build --mailto you@example.com

# Preview without touching disk
python -m wellington_vault build --dry-run

# Force re-fetch (ignore cache)
python -m wellington_vault build --refresh

# If author name resolution misfires, pin the OpenAlex author ID directly
python -m wellington_vault build --author-id A1234567890
```

The cIRcle key is optional. Without it the build proceeds with OpenAlex only
and the `theses/` folder will likely be empty (OpenAlex rarely indexes UBC
graduate theses). With it, the build cross-references Wellington-paper
co-authors against cIRcle's thesis collection by creator name and writes
one note per match.

The first build populates the cache at `.cache/openalex/`; subsequent runs are
near-instant unless you pass `--refresh`.

---

## Usage

1. Run the build (above).
2. Open `vault/` as a vault in Obsidian.
3. Enable **Graph view** to see clusters by topic and the co-author network.
4. Use Obsidian search or dataview to filter — e.g. find every PI-led paper:

   ```dataview
   TABLE year, venue, cited_by_count
   FROM "papers"
   WHERE wellington_role = "last-author" OR wellington_role = "first-author"
   SORT year DESC
   ```

5. Ask Claude things like:
   - *"What are the most-cited Wellington-lab papers on apoE?"*
   - *"Who has co-authored more than 5 papers with the lab?"*
   - *"Summarize the lab's TBI work between 2018 and 2024."*

   Claude will read the vault directly via the `obsidian-second-brain` skill.

---

## What's in the data

- **Source:** [OpenAlex](https://openalex.org) — open metadata of ~250M+ scholarly works.
- **Per paper:** title, year, venue, DOI, OpenAlex ID, OA status, cited-by count, full author list, top topics (≥0.3 score), abstract reconstructed from OpenAlex's inverted index.
- **Per person:** every Wellington-lab paper they're on, their first/last co-publication year.
- **Per topic:** every Wellington-lab paper tagged with that OpenAlex concept.

Coverage caveat: OpenAlex covers ~95% of what shows on Google Scholar. Preprints and very recent items may lag. UBC graduate theses are sourced from **cIRcle** (Open Collections, `oc-index.library.ubc.ca`) via three legs unioned by record ID: (1) creator-name match for first-authors of Wellington-last-author papers, (2) phrase match of the PI's full name across the index, filtered to creators who are Wellington co-authors in OpenAlex (the unfiltered phrase match also surfaces examining-committee acknowledgments, which are not Wellington-supervised theses), and (3) manual seeding via `--trainees-file`. cIRcle does not expose its Supervisor field for queries, so a thesis here only means there is a structural link to the lab — Wellington's role as supervisor is inferred and should be verified against the thesis acknowledgments before external citation. Trainees who never co-authored a paper with Wellington and aren't in the trainees file will not be captured.

---

## Rebuilding

The vault is **fully derived** from OpenAlex. Re-run the build any time:

- New papers come out
- You want refreshed citation counts
- The lab roster changes

Each run overwrites `papers/`, `people/`, `topics/`, `theses/`, `index.md` and appends a line to `log.md`. Hand-edits to those files are lost — keep human notes in a separate folder.

### Optional: word cloud

`build` also writes `vault/wordcloud.png` (a word cloud of every paper + thesis abstract) when the third-party `wordcloud` package is installed:

```
pip install wordcloud
```

Without it, the build prints an install hint and continues. Pass `--no-wordcloud` to skip the render even when the package is available.

---

## Source

- Dr. Wellington's Google Scholar: https://scholar.google.com/citations?user=aMfyjdEAAAAJ
- Lab website: https://wellingtonlabubc.wordpress.com/
- UBC profile: https://pathology.ubc.ca/2022/12/01/cheryl-wellington/
