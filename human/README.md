# `human/` — the parts of this repo meant for people

The rest of this repository is written for Claude. `vault/` is an **AI-first** vault: every note
carries dense frontmatter, a `## For future Claude` preamble, recency markers on each claim and
wikilinks on every cross-reference. That is deliberate — it makes the vault good to *retrieve and
reason over*, and correspondingly tiring to *read*. `vault/_CLAUDE.md` says so outright: "The owner
rarely reads notes directly."

This folder is the other half. Same data, arranged for a person.

| | What it is |
|---|---|
| **`index.html`** | Interactive browser for the whole publication record. Open it in any browser — no server, no install, no network. |
| **`duplicate-people.md`** | The finished list of people who appear more than once in `vault/people/`, and which notes to merge. |
| **`duplicate-people-audit.md`** | How each of those calls was reached — including the pairs that were checked and rejected. |
| **`notes/`** | Somewhere to write things by hand. Nothing here is ever overwritten. |

---

## The browser

```
open human/index.html          # macOS
start human\index.html         # Windows
xdg-open human/index.html      # Linux
```

A single self-contained file — the vault's data is embedded in it, so it works offline and can be
emailed or dropped on a shared drive as-is.

What you can do with it:

- **Search everything at once** — titles, abstracts, venues, author names and topics. Press `/` to
  jump to the search box, `Esc` to clear it.
- **Filter publications** by year (click a bar on the chart), by Wellington's role on the paper
  (first, last or co-author), and by open-access status.
- **Sort** by newest, oldest, or most cited.
- **Click any paper** to expand its abstract, full author list, topics and DOI link.
- **Click any author or topic** to pivot the paper list onto them — this is how you walk the
  co-author network without opening Obsidian.
- **Switch tabs** to browse the 1,667 co-authors, 684 research topics, or the trainee theses (which
  link out to UBC cIRcle).
- **Toggle light/dark** with the button in the corner; it follows your system theme by default.

### Regenerating it

The browser is derived from `vault/`, exactly like the vault is derived from OpenAlex. After any
rebuild:

```bash
python -m wellington_vault build      # refresh the vault from OpenAlex
python human/build_human.py           # refresh this browser from the vault
```

`build_human.py` reads the vault notes and writes `index.html` from `_template.html`. Both are
stdlib-only and make no network calls. Edit `_template.html` to change the page; `index.html` is
generated output and your edits to it will be overwritten.

---

## Two things to know about the data

**Citation counts are a snapshot.** They were true at vault-build time and drift upward
continuously. Re-run the build for current numbers.

**Some people appear more than once.** OpenAlex sometimes files one researcher under several author
IDs, so the co-author count is inflated — 1,667 notes describe roughly 1,592 people. See
`duplicate-people.md`. This affects the People tab and the author lists, not the publication count.

---

## `notes/`

`vault/papers/`, `vault/people/`, `vault/topics/` and `vault/theses/` are deleted and rewritten on
every build. Anything you hand-write in them is lost.

`notes/` is outside that blast radius. Put reading notes, corrections, drafts and anything else you
want to keep there — plain markdown, no schema, no rules. If you open `vault/` in Obsidian and want
these alongside it, symlink the folder in rather than moving it.
