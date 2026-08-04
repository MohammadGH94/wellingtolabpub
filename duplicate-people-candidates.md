# Potential duplicate people in `vault/people/`

Every one of the 1,667 person notes was walked and clustered by surname + given-name form (diacritics, hyphens and periods normalised away). These duplicates survive the build's ID-based canonicalization in `wellington_vault/build.py:51` because **OpenAlex itself assigned the same human more than one `author.id`** — collapsing display-name variants per ID cannot catch them, so a name-level pass is required.

Counts shown are `papers_with_wellington_lab` from each note's frontmatter, followed by the note's co-publication year span.

**Summary:** 49 near-certain merge clusters (99 notes → 49 people, removing 50 spurious entries),
2 clusters resolved by manually reading the papers (`Chan`, `Martens` — worth 4 more merges),
26 probable pairs needing a human call, and 43 same-surname pairs that are probably genuinely
different people, listed so the sweep is auditable.


---

## Tier 1 — near-certain duplicates

One name is a strict extension or abbreviation of the other: a middle name/initial present in one form and absent in the other, an initial-only given name where no other person in the vault shares that surname, or a pure diacritic/hyphen difference. Nothing in the names conflicts.

| # | Keep (most papers) | Merge in | Papers | Years |
|---|---|---|---|---|
| 1 | **Wai Hang Cheng** (39p, 2013–2025) | `Wai Cheng` | 4 | 2017–2017 |
| 2 | **Emily B. Button** (40p, 2015–2021) | `Emily Button` | 2 | 2017–2017 |
| 3 | **Jennifer Cooper** (26p, 2020–2025) | `Jennifer G Cooper`<br>`Jennifer G. Cooper` | 11<br>1 | 2022–2025<br>2026–2026 |
| 4 | **Neil R. Cashman** (32p, 1999–2024) | `Neil Cashman` | 2 | 2017–2017 |
| 5 | **Kevin Kang** (12p, 2017–2017) | `Kevin H. Kang` | 4 | 2017–2017 |
| 6 | **Catherine M. Cowan** (12p, 2015–2018) | `Catherine Cowan` | 4 | 2017–2017 |
| 7 | **Gordon Francis** (10p, 2017–2017) | `Gordon A. Francis` | 3 | 2017–2017 |
| 8 | **Julie A. Schneider** (7p, 2014–2020) | `Julie Schneider` | 1 | 2026–2026 |
| 9 | **Denise Foster** (6p, 2020–2022) | `Denise A. Foster` | 1 | 2025–2025 |
| 10 | **Liam R. Brunham** (5p, 2001–2012) | `L. R. Brunham` | 1 | 2004–2004 |
| 11 | **Michael Borrie** (5p, 2024–2025) | `M Borrie` | 1 | 2024–2024 |
| 12 | **Donna M. Wilcock** (4p, 2014–2020) | `Donna Wilcock` | 1 | 2026–2026 |
| 13 | **Alicia Algeciras‐Schimnich** (3p, 2024–2025) | `Alicia Algeciras-Schimnich` | 1 | 2025–2025 |
| 14 | **Charlotte E. Teunissen** (3p, 2024–2025) | `C. Teunissen` | 1 | 2025–2025 |
| 15 | **Jessica Cusato** (3p, 2024–2025) | `J Cusato` | 1 | 2025–2025 |
| 16 | **Jan Albert Kuivenhoven** (3p, 2008–2012) | `J.A. Kuivenhoven` | 1 | 2004–2004 |
| 17 | **Socrates J. Tzartos** (3p, 2024–2025) | `Socrates Tzartos` | 1 | 2025–2025 |
| 18 | **Jose Martinez‐Yriarte** (2p, 2025–2025) | `Jose Yriarte` | 2 | 2024–2025 |
| 19 | **M Blanc** (3p, 2024–2025) | `Marie‐Céline Blanc` | 1 | 2025–2025 |
| 20 | **Ana‐Luiza Sayao** (2p, 2021–2023) | `A.L. Sayao` | 1 | 2021–2021 |
| 21 | **Amanda Li** (2p, 2024–2024) | `Amanda M. Li` | 1 | 2023–2023 |
| 22 | **Bruna Seixas Lima** (2p, 2025–2025) | `Bruna Seixas-Lima` | 1 | 2026–2026 |
| 23 | **Elizabeth Finger** (2p, 2024–2025) | `E Finger` | 1 | 2024–2024 |
| 24 | **Megan I. Harper** (2p, 2022–2024) | `Megan I Harper` | 1 | 2025–2025 |
| 25 | **John Tzartos** (2p, 2025–2025) | `John S. Tzartos` | 1 | 2025–2025 |
| 26 | **Juan Fortea** (2p, 2025–2025) | `Juan M. Fortea` | 1 | 2025–2025 |
| 27 | **K. Rockwood** (2p, 2024–2025) | `Kenneth Rockwood` | 1 | 2024–2024 |
| 28 | **Kristina Martens** (2p, 2015–2017) | `Kristina M. Martens` | 1 | 2016–2016 |
| 29 | **Michael D. Hill** (2p, 2024–2025) | `M Hill` | 1 | 2025–2025 |
| 30 | **M. Natasha Rajah** (2p, 2024–2025) | `Maria Natasha Rajah` | 1 | 2024–2024 |
| 31 | **Natalie A. Phillips** (2p, 2024–2025) | `Natalie Phillips` | 1 | 2024–2024 |
| 32 | **Patrick Orban** (2p, 2001–2004) | `P. C. Orban` | 1 | 2004–2004 |
| 33 | **Robert Carruthers** (2p, 2021–2023) | `R.L. Carruthers` | 1 | 2021–2021 |
| 34 | **David K.B. Li** (1p, 2021–2021) | `David Li` | 1 | 2023–2023 |
| 35 | **Lon S. Schneider** (1p, 2019–2019) | `Lon Schneider` | 1 | 2025–2025 |
| 36 | **Angela Jefferson** (1p, 2025–2025) | `Angela L. Jefferson` | 1 | 2019–2019 |
| 37 | **Anton P. Porsteinsson** (1p, 2023–2023) | `Anton Porsteinsson` | 1 | 2025–2025 |
| 38 | **Christopher H. van Dyck** (1p, 2023–2023) | `Christopher van Dyck` | 1 | 2025–2025 |
| 39 | **Claire‐Anne Gutekunst** (1p, 2002–2002) | `Claire-Anne Gutekunst` | 1 | 2000–2000 |
| 40 | **Elodie Bouaziz Amar** (1p, 2025–2025) | `Elodie Bouaziz-Amar` | 1 | 2025–2025 |
| 41 | **Gregory A. Jicha** (1p, 2023–2023) | `Gregory Jicha` | 1 | 2025–2025 |
| 42 | **J Kastelein** (1p, 2004–2004) | `John J.P. Kastelein` | 1 | 2002–2002 |
| 43 | **J.T. Yik** (1p, 2021–2021) | `Jackie T. Yik` | 1 | 2021–2021 |
| 44 | **James B. Brewer** (1p, 2023–2023) | `James Brewer` | 1 | 2025–2025 |
| 45 | **Jose Enrique Martínez Rodríguez** (1p, 2025–2025) | `José Rodríguez` | 1 | 2025–2025 |
| 46 | **Ken‐ichi Hirano** (1p, 2002–2002) | `Ken-ichi Hirano` | 1 | 2003–2003 |
| 47 | **M Jog** (1p, 2024–2024) | `Mandar Jog` | 1 | 2025–2025 |
| 48 | **Mark Hamer** (1p, 2022–2022) | `Mark Stephen Hamer` | 1 | 2022–2022 |
| 49 | **Tessa F. Morelli** (1p, 2025–2025) | `Tessa Morelli` | 1 | 2025–2025 |

---

## Manually verified — the two messiest clusters

The name rules alone could not settle these two, so the underlying paper lists were read. Both
turn out to be resolvable, and the answers do **not** match what the name rules predicted.

### `Chan` — 4 notes, 21 papers, all one person

| Note | Papers | Years | Research line |
|---|---|---|---|
| `Jeniffer Chan` | 15 | 2004–2014 | LCAT / ABCA1 / apoE / APP-PS1, mostly *J. Lipid Research* |
| `Jennifer Chan` | 3 | 2008–2011 | ABCA1-independent apoE recycling, LCAT in astrocytes, GW3965 |
| `Jennifer Y. Chan` | 2 | 2005–2007 | transgenic ABCA1 and amyloid burden |
| `Jennifer A. Chan` | 1 | 2008 | GW3965 in APP/PS1 with and without ABCA1 |

Every note sits on the same ABCA1/apoE/GW3965/APP-PS1 research line in the same venues over an
overlapping decade. `Jeniffer` is a straight misspelling of `Jennifer`, and the conflicting `Y.`
and `A.` middle initials are metadata noise on conference abstracts, not two different people.
**Merge all four into `Jeniffer Chan`'s successor note** — this is the single largest fix in the
list, folding 6 spurious paper-links back onto one trainee. Note that this contradicts the general
rule that conflicting middle initials imply distinct people; it is the one confirmed exception.

### `Martens` — 3 notes, probably 2 people

| Note | Papers | Years | Research line |
|---|---|---|---|
| `Kris M. Martens` | 16 | 2014–2020 | CHIMERA TBI model, APP/PS1 cerebrovascular work |
| `Kristina M. Martens` | 1 | 2016 | the original CHIMERA rodent TBI paper |
| `Kristina Martens` | 2 | 2015–2017 | Aβ-oligomer vaccination / epitope-specific immunotherapy |

`Kris M. Martens` and `Kristina M. Martens` are the same CHIMERA researcher — **merge**.
`Kristina Martens` sits on a different research line (amyloid-oligomer vaccination) with no
CHIMERA overlap, so despite the compatible name it is likelier a different person — **leave
separate** unless you can confirm otherwise.

---

## Tier 2 — probable duplicates, need a human call

Given names differ but one is a short form, an ambiguous initial, or a near-identical spelling.
The `Chan` and `Martens` rows below are already settled in the verified section above.

| Name A | Name B | Why flagged |
|---|---|---|
| **Michael R. Hayden** (51p, 1997–2025) | `M. R. Hayden` (1p, 2004–2004) | initial-only given name; surname shared by 3 notes, so the expansion is ambiguous |
| **Jennifer Cooper** (26p, 2020–2025) | `J. Cooper` (1p, 2025–2025) | initial-only given name; surname shared by 4 notes, so the expansion is ambiguous |
| **Jeniffer Chan** (15p, 2004–2014) | `Jennifer Chan` (3p, 2008–2011) | given names near-identical (ratio 0.88) — spelling variant or typo |
| **Kris M. Martens** (16p, 2014–2020) | `Kristina Martens` (2p, 2015–2017) | one given name is a short form/prefix of the other |
| **Jeniffer Chan** (15p, 2004–2014) | `Jennifer Y. Chan` (2p, 2005–2007) | given names near-identical (ratio 0.88) — spelling variant or typo |
| **Kris M. Martens** (16p, 2014–2020) | `Kristina M. Martens` (1p, 2016–2016) | one given name is a short form/prefix of the other |
| **Jeniffer Chan** (15p, 2004–2014) | `Jennifer A. Chan` (1p, 2008–2008) | given names near-identical (ratio 0.88) — spelling variant or typo |
| **William J. Panenka** (12p, 2013–2025) | `Will Panenka` (1p, 2023–2023) | one given name is a short form/prefix of the other |
| **Jennifer G Cooper** (11p, 2022–2025) | `J. Cooper` (1p, 2025–2025) | initial-only given name; surname shared by 4 notes, so the expansion is ambiguous |
| **Jamie Hutchison** (8p, 2018–2023) | `James S. Hutchison` (4p, 2018–2025) | given names near-identical (ratio 0.80) — spelling variant or typo |
| **Anne‐Marie Guerguerian** (4p, 2018–2025) | `Ann-Marie Guerguerian` (1p, 2019–2019) | one given name is a short form/prefix of the other |
| **Jacques Lacroix** (3p, 2020–2023) | `Jacque Lacroix` (1p, 2025–2025) | one given name is a short form/prefix of the other |
| **Pamela F. Parkinson** (3p, 2005–2009) | `Pam Parkinson` (1p, 2008–2008) | one given name is a short form/prefix of the other |
| **Daniele Imperiale** (2p, 2025–2025) | `Daniela Imperiale` (1p, 2025–2025) | given names near-identical (ratio 0.86) — spelling variant or typo |
| **Juanjo Hernandez Sanchez** (2p, 2025–2025) | `Juan José Hernández Sánchez` (1p, 2025–2025) | one given name is a short form/prefix of the other |
| **Shannon Kolind** (2p, 2021–2023) | `SH Kolind` (1p, 2021–2021) | one given name is a short form/prefix of the other |
| **Y. Deng** (2p, 2001–2004) | `Yanhong Deng` (1p, 2004–2004) | initial-only given name; surname shared by 3 notes, so the expansion is ambiguous |
| **Y. Deng** (2p, 2001–2004) | `Yu Deng` (1p, 2006–2006) | initial-only given name; surname shared by 3 notes, so the expansion is ambiguous |
| **Benny K. K. Chan** (1p, 2008–2008) | `Senny Chan` (1p, 2024–2024) | given names near-identical (ratio 0.80) — spelling variant or typo |
| **C.Y. Chen** (1p, 1994–1994) | `Christopher Chen` (1p, 2019–2019) | initial-only given name; surname shared by 11 notes, so the expansion is ambiguous |
| **G. R. Wayne Moore** (1p, 2021–2021) | `GR Wayne Moore` (1p, 2023–2023) | initial-only given name; surname shared by 4 notes, so the expansion is ambiguous |
| **G. R. Wayne Moore** (1p, 2021–2021) | `George R. Moore` (1p, 2021–2021) | initial-only given name; surname shared by 4 notes, so the expansion is ambiguous |
| **J. Cooper** (1p, 2025–2025) | `Jennifer G. Cooper` (1p, 2026–2026) | initial-only given name; surname shared by 4 notes, so the expansion is ambiguous |
| **J. H. Kim** (1p, 2018–2018) | `Jungsu Kim` (1p, 2008–2008) | initial-only given name; surname shared by 4 notes, so the expansion is ambiguous |
| **Jon D. Wood** (1p, 2003–2003) | `Jonathan Wood` (1p, 1999–1999) | one given name is a short form/prefix of the other |
| **Prescilla Carrion** (1p, 2025–2025) | `Priscilla Carrion` (1p, 2023–2023) | given names near-identical (ratio 0.89) — spelling variant or typo |

---

## Tier 3 — same surname, flagged but probably DIFFERENT people

Listed for completeness so the sweep is auditable. Conflicting middle initials are the strongest in-name signal of two distinct humans; the rest merely share a first initial.

| Name A | Name B | Why flagged |
|---|---|---|
| Anna Wilkinson (35p) | Amy Wilkinson (2p) | given names genuinely differ — probably two different people |
| Sonny Thiara (12p) | Sharanjit Thiara (1p) | given names genuinely differ — probably two different people |
| Noah D. Silverberg (8p) | Noah Noah Silverberg (1p) | same given+surname but CONFLICTING middle initials — likely two people |
| Michael Carr (6p) | Mike Carr (1p) | given names genuinely differ — probably two different people |
| Steven Zhou (6p) | Stephen Zhou (1p) | given names genuinely differ — probably two different people |
| Michael Lee (4p) | Chel Hee Lee (2p) | given names genuinely differ — probably two different people |
| Christopher A. Ross (5p) | Colin J.D. Ross (1p) | given names genuinely differ — probably two different people |
| Agnes Lee (4p) | Allen Lee (1p) | given names genuinely differ — probably two different people |
| Agnes Lee (4p) | Athene Lee (1p) | given names genuinely differ — probably two different people |
| Michael Lee (4p) | Mike Lee (1p) | given names genuinely differ — probably two different people |
| Tom Whyte (4p) | Thomas Whyte (1p) | given names genuinely differ — probably two different people |
| Adi Zoref‐Lorenz (3p) | Bradi R Lorenz (1p) | given names genuinely differ — probably two different people |
| Adrienne L. Davis (2p) | Albert A. Davis (2p) | given names genuinely differ — probably two different people |
| Johnson Chen (3p) | Jue Chen (1p) | given names genuinely differ — probably two different people |
| Jon L. Collins (3p) | Jennifer A. Collins (1p) | given names genuinely differ — probably two different people |
| Stephen Pasternak (3p) | SH Pasternak (1p) | given names genuinely differ — probably two different people |
| Alice Schabas (2p) | AJ Schabas (1p) | given names genuinely differ — probably two different people |
| Amanda Li (2p) | Aimin Li (1p) | given names genuinely differ — probably two different people |
| Yicong Li (2p) | Yan Li (1p) | given names genuinely differ — probably two different people |
| Elisa Wilson (2p) | Elizabeth Wilson (1p) | given names genuinely differ — probably two different people |
| Jefferson R. Wilson (2p) | Janet E. Wilson (1p) | given names genuinely differ — probably two different people |
| Jennifer Y. Chan (2p) | Jennifer A. Chan (1p) | same given+surname but CONFLICTING middle initials — likely two people |
| Jie Liu (2p) | Jiangui Liu (1p) | given names genuinely differ — probably two different people |
| Jody Peters (2p) | James J. Peters (1p) | given names genuinely differ — probably two different people |
| Mike Tymko (2p) | Michael M. Tymko (1p) | given names genuinely differ — probably two different people |
| Suzanne Vercauteren (2p) | Susan Vercauteren (1p) | given names genuinely differ — probably two different people |
| Achelle Cortel‐LeBlanc (1p) | Allana LeBlanc (1p) | given names genuinely differ — probably two different people |
| Adrian Wong (1p) | Andy Kin On Wong (1p) | given names genuinely differ — probably two different people |
| Allen Lee (1p) | Athene Lee (1p) | given names genuinely differ — probably two different people |
| Aimin Li (1p) | Amanda M. Li (1p) | given names genuinely differ — probably two different people |
| DKB Li (1p) | David K.B. Li (1p) | given names genuinely differ — probably two different people |
| DKB Li (1p) | David Li (1p) | given names genuinely differ — probably two different people |
| Rachel Zhao (1p) | Rui Qi Zhao (1p) | given names genuinely differ — probably two different people |
| Charlotte M. Anderson (1p) | Christine Anderson (1p) | given names genuinely differ — probably two different people |
| Zefang Wang (1p) | Zhengnan Wang (1p) | given names genuinely differ — probably two different people |
| David D. Howell (1p) | David R. Howell (1p) | same given+surname but CONFLICTING middle initials — likely two people |
| Kathleen A. Martin (1p) | Kelly Martin (1p) | given names genuinely differ — probably two different people |
| GR Wayne Moore (1p) | George R. Moore (1p) | given names genuinely differ — probably two different people |
| Li Gan (1p) | Lu Gan (1p) | given names genuinely differ — probably two different people |
| Gene L. Bowman (1p) | Gregory R. Bowman (1p) | given names genuinely differ — probably two different people |
| Sean Kim (1p) | Seung Up Kim (1p) | given names genuinely differ — probably two different people |
| Nicholas Josafatow (1p) | Nik Josafatow (1p) | given names genuinely differ — probably two different people |
| Yanhong Deng (1p) | Yu Deng (1p) | given names genuinely differ — probably two different people |

---

## Not people at all

Consortium / working-group strings that OpenAlex records in author lists and the build therefore renders as person notes.

- `Alzheimer’s Disease Cooperative Study T2 Protect AD Study Group` and `and the InTBIR Biospecimens/Biomarkers Working Group`
- `The Alzheimer’s Disease Cooperative Study T2 Protect AD Study Group` and `the InTBIR Fundamental & Translational Working Group`

---

## Caveats on the evidence used

- **Two names appearing on the same paper does NOT prove they are different people.** Three pairs
  here link to a shared paper note, and all three are still the same person:
  - `Mark Hamer` / `Mark Stephen Hamer` — an artifact of a *filename collision*, not a real shared
    paper: the medRxiv preprint and the Frontiers in Immunology version of "Prognostic peripheral
    blood biomarkers at ICU admission predict COVID-19 clinical outcomes" both slugify to the same
    filename, so the two notes point at one file.
  - `Jamie Hutchison` / `James S. Hutchison` and `William J. Panenka` / `Will Panenka` — the 2023
    metabolomics paper genuinely lists both variants in one OpenAlex authorship array, because
    consortium members are recorded a second time alongside the named authors.
- **Disjoint year spans are weak evidence of distinctness.** A split usually just marks the point
  where OpenAlex started emitting a different display name for the same person.
- **Conflicting middle initials are the strongest in-name signal of two real people** and are the
  basis for Tier 3 and for quarantining the ambiguous cluster.

## Fixing this upstream

The durable fix belongs in `canonicalize_authorships()` (`wellington_vault/build.py:51`): after
grouping by `author.id`, run a second pass that merges *ID groups* whose canonical names are
name-compatible under the Tier 1 rule, keeping the ID group with the most works as canonical. That
would fold the merges above into every rebuild instead of requiring a manual sweep.

