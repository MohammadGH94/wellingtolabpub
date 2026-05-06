# Claude Operating Manual — Wellington Lab Publications Vault

> Read this file before doing anything in this vault.
> This is the single source of truth for how Claude operates here.

---

## Section 0 — AI-First Vault Rule (read first, applies to every note)

This vault is designed for **future-Claude** to read and reason over, not for human review. The owner rarely reads notes directly — they call Claude to retrieve, synthesize, and connect dots across the Wellington lab's publication record (Alzheimer's disease, apolipoprotein E, traumatic brain injury, cerebrovascular dysfunction).

**Every note Claude writes to this vault must follow these rules:**

1. **Self-contained context** — Each note must explain itself. Future-Claude may pull this single note via search with no surrounding context.
2. **"For future Claude" preamble** — Every note begins with a 2-3 sentence summary so Claude can decide relevance in 10 seconds before parsing the structured data.
3. **Rich, consistent frontmatter** — `type`, `date`, `tags`, type-specific fields, `ai-first: true`.
4. **Recency markers per claim** — When stating external facts, attach the date + source: `cited_by_count: 87 (as of 2026-05-02, openalex.org)`.
5. **Sources preserved verbatim** — Every external claim has its source URL inline (DOI, OpenAlex ID, OA URL).
6. **Cross-links are mandatory** — Every author, topic, paper, or thesis referenced uses `[[wikilinks]]` so the graph is traversable.
7. **Confidence levels** — Mark claims as `stated | high | medium | speculation`.

Full spec: `.claude/skills/obsidian-second-brain/references/ai-first-rules.md` (Section "The 7 Rules").

---

## Vault Identity

- **Subject:** Dr. Cheryl Wellington's lab — University of British Columbia
- **Lab website:** https://wellingtonlabubc.wordpress.com/
- **Primary purpose:** Brain-map of every publication and thesis from the lab, plus the co-author network and topic graph that emerges from them
- **Built by:** `python -m wellington_vault build` (source: `wellington_vault/`)
- **Data provenance:** OpenAlex (https://openalex.org) for publications; UBC cIRcle / Open Collections (https://oc-index.library.ubc.ca) for trainee theses

---

## Folder Map

| Folder | Purpose | Note type |
|---|---|---|
| `papers/` | One note per Wellington-lab publication | `paper` |
| `people/` | One note per author — PI, co-authors, trainees | `person` |
| `topics/` | One note per OpenAlex concept tagged on a paper | `topic` |
| `theses/` | One note per UBC student thesis (planned, may be empty) | `thesis` |

Filenames:
- Papers: `YYYY — Slugified Title.md`
- People: `Full Name.md` (flat — no nested folders)
- Topics: `Topic Name.md`
- Theses: `YYYY — Slugified Title.md`

---

## Note Type Schemas

### `type: paper` (frontmatter)
```yaml
date: YYYY-MM-DD              # vault-build date
type: paper
tags: [paper, wellington-lab, year-YYYY]
title: "..."
year: YYYY
publication_date: YYYY-MM-DD
work_type: article | review | book-chapter | preprint | ...
venue: "Journal of ..."
venue_type: journal | repository | book | ...
doi: "..."
openalex_id: "https://openalex.org/W..."
open_access: true | false
oa_url: "..."
cited_by_count: N             # snapshot — drifts over time
wellington_role: first-author | last-author | co-author | unknown
authors: ["[[Name1]]", "[[Name2]]", ...]
topics: ["[[Topic1]]", ...]
ai-first: true
confidence: stated
```

### `type: person`
```yaml
date: YYYY-MM-DD
type: person
tags: [person, wellington-lab]
name: "..."
role: principal-investigator | co-author | trainee
papers_with_wellington_lab: N
first_co_pub_year: YYYY
last_co_pub_year: YYYY
ai-first: true
confidence: stated
```

### `type: topic`
```yaml
date: YYYY-MM-DD
type: topic
tags: [topic, wellington-lab]
name: "..."
wikidata: "https://www.wikidata.org/wiki/Q..."   # if available
wellington_lab_papers: N
first_year: YYYY
last_year: YYYY
ai-first: true
confidence: stated
```

### `type: thesis` (cIRcle-sourced)
```yaml
date: YYYY-MM-DD
type: thesis
tags: [thesis, wellington-lab, year-YYYY]
title: "..."
year: YYYY
candidate: "Forename Surname"
authors: ["[[Forename Surname]]"]
degree: "Doctor of Philosophy - PhD" | "Master of Science - MSc" | ...
program: "..."                       # e.g. "Pathology and Laboratory Medicine"
affiliations: ["...", "..."]
campus: "UBCV" | "UBCO"
scholarly_level: "Graduate"
institution: "University of British Columbia"
circle_id: "1.0XXXXXX"
circle_url: "https://open.library.ubc.ca/collections/ubctheses/items/1.0XXXXXX"
topics: ["[[Subject1]]", ...]        # cIRcle subject headings (may dangle)
ai-first: true
confidence: stated
source: ubc-circle
```

**Supervisor inference (important).** cIRcle's structured Supervisor field
is not exposed in the public Open Collections index, so theses are surfaced
via three complementary legs and unioned by `_id`:

1. **Co-authorship match** — first-author of a paper where Wellington is last
   author. Catches trainees who published from their thesis work.
2. **PI mention (filtered)** — phrase match `"Cheryl Wellington"` across the
   index, then keep only hits whose creator is a Wellington co-author in
   OpenAlex. Catches middle-author co-authors that leg 1 misses (leg 1 is
   restricted to first-author-of-PI-last-author papers). The co-author
   filter is required: the unfiltered phrase match also surfaces theses
   where Wellington is named only as an examining-committee member, which
   are *not* her supervised theses.
3. **Manual seed** — names from `--trainees-file`, the user-curated escape
   hatch for trainees who never co-authored a paper with Wellington (so
   they're invisible to legs 1 and 2).

This is best-effort coverage, not exhaustive. **Theses are absent from this
vault if the candidate never co-authored a paper with Wellington AND is not
in the trainees file.** When asked who supervised X, hedge: a thesis present
here only means there is a structural link to the lab — verify supervisor
identity by reading the thesis acknowledgments before citing externally.

---

## Key Facts (always-loaded context)

- **PI:** Dr. Cheryl Wellington, Professor, Dept. of Pathology and Laboratory Medicine, UBC (since 2000; Professor since 2011)
- **Research areas:** apolipoprotein E (apoE) metabolism, Alzheimer's disease, traumatic brain injury (TBI), cerebrovascular dysfunction, lipid/lipoprotein metabolism in the brain
- **Affiliations:** UBC Pathology, Djavad Mowafaghian Centre for Brain Health, BC Children's Hospital Research Institute (BCCHR), International Collaboration on Repair Discoveries (ICORD), VCH Research Institute
- **Consortia (leadership roles):** Canadian Traumatic Brain Injury Research Consortium, International TBI Research Consortium, Canadian Consortium for Neurodegeneration in Aging (CCNA), AstraZeneca ApoE Alzheimer Disease Academic Alliance

Sources (as of 2026-05-02):
- https://pathology.ubc.ca/2022/12/01/cheryl-wellington/
- https://www.bcchr.ca/cwellington
- https://icord.org/researchers/dr-cheryl-wellington/

---

## Auto-Save Rules

When the vault is rebuilt via `python -m wellington_vault build`, Claude should:
- Overwrite all notes — they're derived from OpenAlex, source of truth lives upstream
- Preserve any human-added notes in folders OUTSIDE the four schema folders (e.g. `notes/`, `essays/`)
- Update `index.md` and append to `log.md` with the build summary

Claude should **ask before**:
- Hand-editing a derived note (`papers/`, `people/`, `topics/`, `theses/`) — these get clobbered on rebuild; corrections belong upstream (OpenAlex correction request) or in a separate annotations folder
- Deleting any note

---

## Naming Conventions

- Wikilinks to people: `[[Full Name]]` (e.g. `[[Cheryl Wellington]]`)
- Wikilinks to papers: `[[YYYY — Title slug|Display Title]]` (alias supplies the readable title)
- Wikilinks to topics: `[[Topic Name]]`
- Tags: lowercase, hyphenated (`wellington-lab`, `year-2024`)

---

## Rebuild Process

```bash
# Resolve author + see top candidates (no writes)
python -m wellington_vault resolve

# Full build (uses cache from prior runs)
python -m wellington_vault build

# Build including cIRcle thesis ingestion (set CIRCLE_API_KEY first)
python -m wellington_vault build --circle-api-key <key>

# Force re-fetch from both OpenAlex and cIRcle
python -m wellington_vault build --refresh

# Preview without touching disk
python -m wellington_vault build --dry-run
```

After rebuild:
1. Open the vault folder in Obsidian
2. Enable graph view to visualize the co-author and topic networks
3. Use Obsidian's search / dataview to filter (e.g. `wellington_role: last-author` to find PI-led papers)

---

## Do Not Touch

- `index.md` and notes in `papers/`, `people/`, `topics/`, `theses/` — auto-generated. Edits are lost on rebuild.
- `log.md` — append-only build log; do not retroactively edit entries.

---

*This file documents the vault's contract with Claude. It is itself written for future-Claude reference, not for human onboarding.*
