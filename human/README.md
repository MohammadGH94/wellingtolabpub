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

It has two views, switched at the top: **Dashboard** and **Map**.

### Dashboard

What you can do with it:

- **Search everything at once** — titles, abstracts, venues, author names and topics. Press `/` to
  jump to the search box, `Esc` to clear it.
- **Filter publications** by year (click a bar on the chart), by Wellington's role on the paper
  (first, last or co-author), and by open-access status.
- **Sort** by newest, oldest, or most cited.
- **Click any paper** to expand its abstract, full author list, topics and DOI link.
- **Click any author or topic** to pivot the paper list onto them — this is how you walk the
  co-author network without opening Obsidian.
- **Switch tabs** to browse the ~1,600 co-authors, 684 research topics, or the trainee theses (which
  link out to UBC cIRcle).
- **Toggle light/dark** with the button in the corner; it follows your system theme by default.
- **Choose what counts** — articles, preprints, conference abstracts, supplementary files and other
  records toggle independently with the chips beside the view switcher.

On a phone the stat tiles go three-up, the controls pair off, and the chart resizes so the whole
1989–2026 span fits without scrolling sideways.

### Map

The network view — the same thing Obsidian's graph view shows for `vault/`, but without needing
Obsidian. Two modes:

- **People** — who publishes with whom. Node size is papers with the lab; a link means two people
  appear on that many papers together.
- **Topics** — what gets studied together. Node size is how many lab papers carry that topic; a
  link means two topics are tagged on the same papers.

Drag to pan, scroll to zoom, drag a node to pull it out of the tangle, hover for counts, and click
any node to jump back to the Dashboard with its papers already filtered. The search box finds and
centres a node. "Re-layout" reshuffles the starting positions, which sometimes untangles a knot.

**On a touch device** the same gestures work: drag to pan, **pinch to zoom**, drag a node to move
it. Since there is no hover, tapping a node inspects it — pinning it and showing its counts — and
tapping the same node again opens its papers. Choosing Map also scrolls the canvas into view, which
would otherwise sit below the header and controls.

**Two thresholds control what you see**, and both exist because the raw graph is unreadable:

- *Minimum papers* — how many papers a person or topic needs before they appear at all.
- *Minimum shared papers* — how strong a link has to be before it is drawn. At a threshold of 1 the
  co-author network is about 12,000 links of solid hairball; requiring repeat collaboration is what
  makes structure visible.

**One judgment call worth knowing about.** Papers with more than 30 authors are excluded from the
co-authorship links (16 papers). Being named on a consortium paper says very little about who
actually works together, and each such paper contributes up to *n*(*n*−1)/2 links on its own — the
79-author paper alone would add 3,081. Those papers are untouched everywhere else in the browser;
only the map's links ignore them. The methodology note under the map states this on the page too,
along with how many nodes were dropped for having no qualifying link.

The map is a filtered view by design. The Dashboard's People and Topics tabs remain the complete,
unfiltered list.

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

## Publishing it

`index.html` is one static file with no external requests, so any static host will serve it. There
is nothing to build and no server-side anything.

### Vercel (free Hobby tier)

The one setting that matters is **Root Directory** — point it at `human` and Vercel serves
`index.html` at `/` with no config file.

1. Go to [vercel.com/new](https://vercel.com/new) and import this GitHub repository.
2. **Framework Preset:** Other.
3. **Root Directory:** `human` ← the important one.
4. Leave Build Command and Output Directory empty. There is no build step.
5. Deploy.

You get a `*.vercel.app` URL immediately, and every later push that changes `human/index.html`
redeploys automatically. `.vercelignore` in this folder keeps the deployment to the built page.

Or from the command line:

```bash
npm i -g vercel
cd human
vercel          # preview URL
vercel --prod   # production URL
```

The Hobby tier is free and this page sits far inside its limits — a single ~500 KB file, no
functions, no bandwidth to speak of. Note that Hobby is licensed for non-commercial use; an
academic lab page qualifies.

### Alternatives

**Cloudflare Pages** and **Netlify** work identically — import the repo, set the root/publish
directory to `human`, no build command.

**GitHub Pages** is the awkward one here: it can only serve from a branch root or `/docs`, not from
an arbitrary folder, so publishing `human/` needs either a small Actions workflow or moving the
file. Vercel is genuinely less work for this layout.

### Two things to keep in mind

**It is a snapshot, and it will go stale.** The deployed page only changes when a rebuilt
`index.html` is committed. Make it part of the refresh:

```bash
python -m wellington_vault build && python human/build_human.py
git commit -am "Refresh vault and browser" && git push
```

**It is public.** Everything on the page is already-published scholarly metadata from OpenAlex and
UBC cIRcle, but a deployment does put ~1,600 named co-authors and a citation snapshot on an
open URL. Citation counts in particular are frozen at build time, so date the page or refresh it on
a schedule if people are going to cite what they see.

---

## What counts as a publication

**A third of the records are not journal articles.** The 306 records resolve to:

| Kind | Count | Citations | What it is |
|---|---|---|---|
| Articles | **209** | 17,912 | peer-reviewed journal articles and reviews |
| Preprints | 17 | 9 | bioRxiv, medRxiv, Research Square, SSRN |
| Conference abstracts | 63 | 11 | meeting submissions |
| Supplementary files | 11 | 0 | Figshare deposits belonging to a paper already in the list |
| Other records | 6 | 2 | a preface, a news column, an eLife author response |

The 97 non-article records hold **22 citations between them**, against 17,912 for the articles — they
move the publication count and essentially nothing else.

### Choosing what to count

A row of chips beside the view switcher turns each kind on or off independently, so any combination
works: **articles only** (the default), **articles and abstracts**, **abstracts only**, **preprints
only**, everything, or nothing. Each chip shows how many records it holds.

Independent toggles rather than a fixed set of presets, because presets cannot express "preprints
only" and "articles and abstracts" at the same time, and the counts are what make the choice
informed. Selecting a kind moves **totals, chart, people, topics and both graphs together**, so no
two views can disagree about what is being counted. When a non-article kind is shown, each of its
rows is labelled with what it is.

Note that preprints and articles overlap: several preprints are earlier versions of a journal
article also in the list, so "articles and preprints" double-counts that work.

### How the kinds are worked out

OpenAlex types nearly all of these as ordinary articles, so there is no field to read. The evidence
is in the DOI, the venue and the title:

| Signal | Example |
|---|---|
| Supplement DOI | `10.1002/alz.047179` — an Alzheimer's & Dementia supplement; a real article there is `alz.12157` |
| | `alz70856_102379` (its 2025 form), `bjsports-2023-concussion.207`, `blood-2023-178867`, `10.58530/…` (ISMRM), `…05201s416` |
| Session code in title | `P4-218:`, `O1-03-07`, `S3-02-03:`, `IC-P1`, `Abstract 245:`, `2.16 `, `73 (13B) ` |
| All-capitals title | how several proceedings render them |
| Figshare DOI / "Additional file" | `10.6084/m9.figshare.…` |
| Work type | `preprint`, `posted-content`, `peer-review` |

**The rules are deliberately conservative**, because misfiling a real paper is worse than leaving an
abstract among the articles. Nothing demoted has more than **two** citations, while the articles
kept have a median of 30 — that is the check worth re-running if the rules change. It still
under-catches: an abstract published in a supplement with no session code and an ordinary DOI is
indistinguishable here from a short article.

See `record_kind()` in `build_human.py`.

---

## Three things to know about the data

**Citation counts are a snapshot.** They were true at vault-build time and drift upward
continuously. Re-run the build for current numbers.

**Duplicate people are merged here.** OpenAlex files some researchers under several author IDs,
which would show one person several times. `build_human.py` applies `people-merge-map.tsv` — the
same file the vault build uses — so the browser shows 1,589 people rather than the vault's 1,667
notes. Pass `--no-merge-map` to see it unmerged.

It also settles on **one spelling per person**. OpenAlex spells the same name differently across
papers — `Ramon Diaz‐Arrastia` on six and `Ramon Diaz Arrastia` on a seventh — and a person is
identified here by the note those links point at, not by how any one paper spelled them. The
spelling shown is the one the most papers use. See `resolve_labels()` in `build_human.py`.

Because of that, **paper counts here are counted from the papers, not read from the person notes**.
Summing a merged cluster's note counts would double-count any paper naming two variants of the same
person, and it also means the number shown always matches what clicking that person lists. A
handful of people can therefore differ by one or two from their `vault/people/` note.

Coverage is not complete: duplicates whose names share nothing — an English and a transliterated
given name, say — cannot be found from names alone. See `duplicate-people.md`.

---

## `notes/`

`vault/papers/`, `vault/people/`, `vault/topics/` and `vault/theses/` are deleted and rewritten on
every build. Anything you hand-write in them is lost.

`notes/` is outside that blast radius. Put reading notes, corrections, drafts and anything else you
want to keep there — plain markdown, no schema, no rules. If you open `vault/` in Obsidian and want
these alongside it, symlink the folder in rather than moving it.
