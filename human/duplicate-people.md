# Duplicate people in the vault — final list

`vault/people/` contains one note per author name that OpenAlex reported. Where OpenAlex assigned the same human more than one author ID, that person ended up with several notes. All 1,667 notes were reviewed; this is the finished result.

**69 people are split across 144 notes. Merging them removes 75 duplicate notes, taking `vault/people/` from 1,667 to 1,592.**

Machine-readable version: [`people-merge-map.tsv`](../people-merge-map.tsv) at the repo root (`canonical`, `variant`, `variant_file`). How each call was reached: [`duplicate-people-audit.md`](duplicate-people-audit.md).

The **Decided by** column is `lab` where a lab member confirmed the call and `evidence` where it follows from the papers themselves — a shared paper, a shared research line, or one name being a plain abbreviation of the other.


## Merge these

| Keep this name | Fold in | Papers | Decided by |
|---|---|---|---|
| **Michael R. Hayden** | `M. R. Hayden` | 52 | evidence |
| **Wai Hang Cheng** | `Wai Cheng` | 43 | evidence |
| **Emily B. Button** | `Emily Button` | 42 | evidence |
| **Jennifer Cooper** | `Jennifer G Cooper`, `Jennifer G. Cooper`, `J. Cooper` | 39 | evidence |
| **Neil R. Cashman** | `Neil Cashman` | 34 | evidence |
| **Jeniffer Chan** | `Jennifer Chan`, `Jennifer Y. Chan` | 20 | lab |
| **Kris M. Martens** | `Kristina M. Martens`, `Kristina Martens` | 19 | lab |
| **Catherine M. Cowan** | `Catherine Cowan` | 16 | evidence |
| **Kevin Kang** | `Kevin H. Kang` | 16 | evidence |
| **Gordon Francis** | `Gordon A. Francis` | 13 | evidence |
| **Sonny Thiara** | `Sharanjit Thiara` | 13 | lab |
| **Noah D. Silverberg** | `Noah Noah Silverberg` | 9 | evidence |
| **Julie A. Schneider** | `Julie Schneider` | 8 | evidence |
| **Denise Foster** | `Denise A. Foster` | 7 | evidence |
| **Michael Carr** | `Mike Carr` | 7 | evidence |
| **Steven Zhou** | `Stephen Zhou` | 7 | evidence |
| **Liam R. Brunham** | `L. R. Brunham` | 6 | evidence |
| **Michael Borrie** | `M Borrie` | 6 | evidence |
| **Donna M. Wilcock** | `Donna Wilcock` | 5 | evidence |
| **Michael Lee** | `Mike Lee` | 5 | evidence |
| **Tom Whyte** | `Thomas Whyte` | 5 | evidence |
| **Alicia Algeciras‐Schimnich** | `Alicia Algeciras-Schimnich` | 4 | evidence |
| **Charlotte E. Teunissen** | `C. Teunissen` | 4 | evidence |
| **Jan Albert Kuivenhoven** | `J.A. Kuivenhoven` | 4 | evidence |
| **Jessica Cusato** | `J Cusato` | 4 | evidence |
| **Jose Martinez‐Yriarte** | `Jose Yriarte` | 4 | evidence |
| **Marie‐Céline Blanc** | `M Blanc` | 4 | evidence |
| **Socrates J. Tzartos** | `Socrates Tzartos` | 4 | evidence |
| **Stephen Pasternak** | `SH Pasternak` | 4 | evidence |
| **Alice Schabas** | `AJ Schabas` | 3 | evidence |
| **Amanda Li** | `Amanda M. Li` | 3 | evidence |
| **Ana‐Luiza Sayao** | `A.L. Sayao` | 3 | evidence |
| **Bruna Seixas Lima** | `Bruna Seixas-Lima` | 3 | evidence |
| **Daniele Imperiale** | `Daniela Imperiale` | 3 | lab |
| **David K.B. Li** | `David Li`, `DKB Li` | 3 | evidence |
| **Elisa Wilson** | `Elizabeth Wilson` | 3 | lab |
| **Elizabeth Finger** | `E Finger` | 3 | evidence |
| **G. R. Wayne Moore** | `GR Wayne Moore`, `George R. Moore` | 3 | evidence |
| **John Tzartos** | `John S. Tzartos` | 3 | evidence |
| **Juan Fortea** | `Juan M. Fortea` | 3 | evidence |
| **Kenneth Rockwood** | `K. Rockwood` | 3 | evidence |
| **M. Natasha Rajah** | `Maria Natasha Rajah` | 3 | evidence |
| **Megan I. Harper** | `Megan I Harper` | 3 | evidence |
| **Michael D. Hill** | `M Hill` | 3 | evidence |
| **Michael M. Tymko** | `Mike Tymko` | 3 | evidence |
| **Natalie A. Phillips** | `Natalie Phillips` | 3 | evidence |
| **Patrick Orban** | `P. C. Orban` | 3 | evidence |
| **Robert Carruthers** | `R.L. Carruthers` | 3 | evidence |
| **Suzanne Vercauteren** | `Susan Vercauteren` | 3 | lab |
| **Yanhong Deng** | `Y. Deng` | 3 | evidence |
| **Angela L. Jefferson** | `Angela Jefferson` | 2 | evidence |
| **Anton P. Porsteinsson** | `Anton Porsteinsson` | 2 | evidence |
| **Christopher H. van Dyck** | `Christopher van Dyck` | 2 | evidence |
| **Claire‐Anne Gutekunst** | `Claire-Anne Gutekunst` | 2 | evidence |
| **Elodie Bouaziz-Amar** | `Elodie Bouaziz Amar` | 2 | evidence |
| **Gregory A. Jicha** | `Gregory Jicha` | 2 | evidence |
| **Jackie T. Yik** | `J.T. Yik` | 2 | evidence |
| **James B. Brewer** | `James Brewer` | 2 | evidence |
| **John J.P. Kastelein** | `J Kastelein` | 2 | evidence |
| **Jonathan Wood** | `Jon D. Wood` | 2 | evidence |
| **Jose Enrique Martínez Rodríguez** | `José Rodríguez` | 2 | evidence |
| **Ken-ichi Hirano** | `Ken‐ichi Hirano` | 2 | evidence |
| **Lon S. Schneider** | `Lon Schneider` | 2 | evidence |
| **Mandar Jog** | `M Jog` | 2 | evidence |
| **Mark Hamer** | `Mark Stephen Hamer` | 2 | evidence |
| **Nicholas Josafatow** | `Nik Josafatow` | 2 | evidence |
| **Priscilla Carrion** | `Prescilla Carrion` | 2 | evidence |
| **Rachel Zhao** | `Rui Qi Zhao` | 2 | lab |
| **Tessa F. Morelli** | `Tessa Morelli` | 2 | evidence |

## Confirmed as different people

Similar names that were checked and are **not** duplicates. Do not merge these.

| | | Why |
|---|---|---|
| `Jennifer A. Chan` | vs the other three `Chan` notes | Confirmed by the lab as a separate researcher, even though she appears on the same GW3965/APP-PS1 abstract line |
| `David D. Howell` | vs `David R. Howell` | Confirmed by the lab — both in concussion/CTE, still two people |
| `Anna Wilkinson` | vs `Amy Wilkinson` | Confirmed by the lab — Amy's paediatric TBI serum-tau papers are a separate collaboration |
| `Yu Deng` | vs `Yanhong Deng` | 2006 *Cell* caspase-6/huntingtin work, unrelated to the ABCA1 line |
| `Sean Kim` | vs `Seung Up Kim` | 2025 proteomics vs 1998 huntingtin — 27 years and two fields apart |
| `J. H. Kim` | vs `Jungsu Kim` | modCHIMERA TBI model vs ABCA1/PDAPP amyloid |
| `C.Y. Chen` | vs `Christopher Chen` | 1994 c-fos mRNA deadenylation vs 2019 vascular dysfunction in AD |
| `Benny K. K. Chan` | vs `Senny Chan` | 2008 ABCG1 atherosclerosis vs 2024 CCNA dementia consortium |
| `Charlotte M. Anderson` | vs `Christine Anderson` | TRANSCENDENT concussion vs Huntington HTT-lowering |
| `Adrian Wong` | vs `Andy Kin On Wong` | Vascular dysfunction in AD vs TBI metabolomics |
| `Jody Peters` | vs `James J. Peters` | Different people — and `James J. Peters` is probably not a person at all, but the VA Medical Center of that name parsed into an author list |

A further 30-odd same-surname pairs were checked and cleared; they are listed in the audit file.

## What this list cannot catch

**Two limits, both worth knowing before treating 1,592 as the true number of people.**

**Names with nothing in common.** `Rachel Zhao` and `Rui Qi Zhao` are one trainee under an English
and a Chinese given name. The two strings share only the surname and, coincidentally, a first
letter — and that coincidence is the only reason the pair was ever noticed. An adopted name
starting with a different letter would leave no trace: the notes themselves would not give it away
either, since the two papers are on unrelated subjects. Closing this gap needs a roster of lab
members, not better string matching.

**Nicknames.** `Mike`/`Michael`, `Tom`/`Thomas`, `Nik`/`Nicholas` all score below any sensible
string-similarity threshold and were caught only by reading papers. Any automated pass needs a
nickname table.

By contrast, one rule held up everywhere: **a conflicting middle initial always meant two different
people** — `Jennifer A. Chan` and `David D./R. Howell` both stayed separate despite sharing their
namesake's exact research line. A shared research area is not a reason to merge across that
conflict.

## Applying it

**This is applied.** `wellington_vault/build.py` reads `people-merge-map.tsv` on every build and
folds the variants in, so duplicates no longer come back after a rebuild. The pass runs after the
existing author-ID grouping — IDs first, then these merges, because by construction author IDs
cannot rejoin one person filed under several of them.

```bash
python -m wellington_vault build                       # merge map applied by default
python -m wellington_vault build --no-merge-map        # previous behaviour, IDs only
python -m wellington_vault build --merge-map other.tsv # use a different map
```

The build prints how many variants it folded, and warns about any map entry that matched nothing
in the fetch — useful for pruning the file as OpenAlex records change.

**The vault checked into this repo predates the change.** It still shows 1,667 person notes; the
merged counts appear the next time the build runs.

### Editing the map

Add a row to `people-merge-map.tsv` — `canonical`, then `variant`, tab-separated. The third column
is informational. Chains are resolved (if A→B and B→C are both listed, A lands on C), so you cannot
create a half-merge by appending carelessly.

One trap: **a person's display name is not their filename.** `slugify` strips diacritics and
rewrites non-ASCII hyphens, so `Alicia Algeciras‐Schimnich` lives at
`Alicia Algeciras Schimnich.md` and `José Rodríguez` at `Jose Rodriguez.md`. The map is keyed on
display names, and lookups also try a normalized form (lowercased, diacritics and periods stripped)
— which is what lets `Jennifer G. Cooper` match a row written as `Jennifer G Cooper`.

`tests/test_merge_map.py` covers the pass, including the consortium case where one paper names the
same person twice under two IDs. Run it with `python -m unittest discover -s tests`.
