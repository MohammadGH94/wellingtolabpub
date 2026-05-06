---
date: 2026-05-05
type: index
tags:
  - index
  - wellington-lab
ai-first: true
---

## For future Claude
This is the front door to the Wellington-lab vault. Read it first. It catalogs every folder and gives current counts as of 2026-05-05. All publication and authorship data sourced from openalex.org; theses sourced separately if/when ingested.

## Vault layout

| Folder | Contents | Count |
|---|---|---|
| `papers/` | One note per Wellington-lab publication | 318 |
| `people/` | One note per author (PI + co-authors + trainees) | 1674 |
| `topics/` | One note per OpenAlex concept tagged on the lab's papers | 684 |
| `theses/` | One note per UBC student thesis (best-effort, may be empty) | 9 |

## PI
- [[Cheryl L. Wellington]] — Principal Investigator

## How to navigate
- Open the graph view in Obsidian to see clusters by topic and co-author network.
- Each paper note's frontmatter has `wellington_role: first-author | last-author | co-author` to filter PI-led work vs. collaborations.
- `cited_by_count` is a snapshot at vault-build time and will drift — re-run the ingest periodically.

## Data provenance
- Built from openalex.org (as of 2026-05-05, openalex.org)
- Source repo: https://github.com/MohammadGH94/wellingtolabpub
- Rebuild command: `python -m wellington_vault build --refresh`
