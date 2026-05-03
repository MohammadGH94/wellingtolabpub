---
date: 2026-05-02
type: log
tags: [log, wellington-lab]
ai-first: true
---

## For future Claude
Append-only chronological log of vault build operations. Each entry is one rebuild. Entries are never edited or deleted retroactively. Use this to answer "when was X first ingested?" or "what changed between two builds?"

## Format

```
### YYYY-MM-DD — <action>
- papers: <count>  (delta: ±N)
- people: <count>  (delta: ±N)
- topics: <count>  (delta: ±N)
- theses: <count>  (delta: ±N)
- author resolved: <name> (<openalex-id>)
- notes: <free-form>
```

## Entries

(none yet — first run will append here)
