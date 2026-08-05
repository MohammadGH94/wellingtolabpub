"""Tests for the curated author-name merge pass.

Run with:  python -m unittest discover -s tests

Stdlib only, matching the rest of the repo — no pytest dependency.
"""

from __future__ import annotations

import collections
import tempfile
import unittest
from pathlib import Path

from wellington_vault.build import (
    build_indexes,
    canonicalize_authorships,
    load_merge_map,
)
from wellington_vault.notes import render_paper_note


def work(wid: str, authors: list[tuple[str, str]], **kw) -> dict:
    """Minimal OpenAlex-shaped work. `authors` is [(author_id, display_name)]."""
    return {
        "id": f"https://openalex.org/{wid}",
        "title": kw.get("title", f"Paper {wid}"),
        "publication_year": kw.get("year", 2020),
        "type": "article",
        "authorships": [
            {"author": {"id": f"https://openalex.org/{aid}", "display_name": name}}
            for aid, name in authors
        ],
        "concepts": [],
    }


def write_map(rows: str) -> Path:
    tmp = Path(tempfile.mkdtemp()) / "merge.tsv"
    tmp.write_text(rows, encoding="utf-8")
    return tmp


class LoadMergeMap(unittest.TestCase):
    def test_parses_and_skips_header_blanks_comments(self):
        path = write_map(
            "canonical\tvariant\tvariant_file\n"
            "\n"
            "# a comment\n"
            "Jennifer Cooper\tJennifer G Cooper\tJennifer G Cooper.md\n"
        )
        m = load_merge_map(path)
        self.assertEqual(m["Jennifer G Cooper"], "Jennifer Cooper")
        self.assertNotIn("variant", m)

    def test_normalized_lookup(self):
        path = write_map("canonical\tvariant\nMichael R. Hayden\tM. R. Hayden\n")
        m = load_merge_map(path)
        self.assertEqual(m["m r hayden"], "Michael R. Hayden")

    def test_resolves_chains(self):
        """A→B and B→C must land on C, so hand-edits cannot create a half-merge."""
        path = write_map("canonical\tvariant\nB\tA\nC\tB\n")
        m = load_merge_map(path)
        self.assertEqual(m["A"], "C")
        self.assertEqual(m["B"], "C")

    def test_missing_file_is_not_an_error(self):
        self.assertEqual(load_merge_map(Path("/nonexistent/merge.tsv")), {})

    def test_self_reference_ignored(self):
        path = write_map("canonical\tvariant\nSame Name\tSame Name\n")
        self.assertEqual(load_merge_map(path), {})


class MergePass(unittest.TestCase):
    def test_merges_across_distinct_author_ids(self):
        """The whole point: same human, two OpenAlex IDs, one person note."""
        works = [
            work("W1", [("A1", "Jennifer Cooper")]),
            work("W2", [("A2", "Jennifer G Cooper")]),
        ]
        merge = {"Jennifer G Cooper": "Jennifer Cooper",
                 "jennifer g cooper": "Jennifer Cooper"}
        canonicalize_authorships(works, merge_map=merge)
        people = build_indexes(works)["by_person"]
        self.assertEqual(sorted(people), ["Jennifer Cooper"])
        self.assertEqual(len(people["Jennifer Cooper"]), 2)

    def test_without_map_ids_stay_separate(self):
        works = [
            work("W1", [("A1", "Jennifer Cooper")]),
            work("W2", [("A2", "Jennifer G Cooper")]),
        ]
        canonicalize_authorships(works)
        self.assertEqual(len(build_indexes(works)["by_person"]), 2)

    def test_id_grouping_still_applies_first(self):
        """Display-name variants under one ID collapse without any map entry."""
        works = [
            work("W1", [("A1", "Cheryl Wellington")]),
            work("W2", [("A1", "Cheryl L. Wellington")]),
            work("W3", [("A1", "Cheryl L. Wellington")]),
        ]
        canonicalize_authorships(works)
        self.assertEqual(sorted(build_indexes(works)["by_person"]), ["Cheryl L. Wellington"])

    def test_same_paper_listing_both_variants_counts_once(self):
        """The consortium case: one paper naming a person individually and again
        as a group member, under two IDs the map unites."""
        works = [work("W1", [("A1", "Jamie Hutchison"), ("A9", "Someone Else"),
                             ("A2", "James S. Hutchison")])]
        merge = {"Jamie Hutchison": "James S. Hutchison",
                 "jamie hutchison": "James S. Hutchison"}
        canonicalize_authorships(works, merge_map=merge)
        people = build_indexes(works)["by_person"]
        self.assertEqual(len(people["James S. Hutchison"]), 1,
                         "paper must not be listed twice on the merged note")
        note = render_paper_note(works[0])
        self.assertEqual(note.count("[[James S. Hutchison]]"), 2,
                         "expected once in frontmatter and once in the citation line")

    def test_name_map_covers_premerge_variants(self):
        """The returned map is what the cIRcle renderer uses to resolve a name
        string with no author ID attached, so every variant must point at the
        final merged name."""
        works = [
            work("W1", [("A1", "Jennifer Cooper")]),
            work("W2", [("A2", "Jennifer G Cooper")]),
            work("W3", [("A2", "Jennifer G. Cooper")]),
        ]
        merge = {"Jennifer G Cooper": "Jennifer Cooper",
                 "jennifer g cooper": "Jennifer Cooper"}
        names = canonicalize_authorships(works, merge_map=merge)
        self.assertEqual(names["Jennifer G Cooper"], "Jennifer Cooper")
        # A2's own canonical is "Jennifer G. Cooper" (longest variant wins the
        # tie), which the map does not list literally. It only merges because
        # the lookup falls back to the normalized form, where the period is
        # stripped — so both spellings must resolve.
        self.assertEqual(names["Jennifer G. Cooper"], "Jennifer Cooper")
        self.assertEqual(names["jennifer g cooper"], "Jennifer Cooper")

    def test_unmapped_people_untouched(self):
        works = [work("W1", [("A1", "Anna Wilkinson")]),
                 work("W2", [("A2", "Amy Wilkinson")])]
        canonicalize_authorships(works, merge_map={"Jennifer G Cooper": "Jennifer Cooper"})
        self.assertEqual(sorted(build_indexes(works)["by_person"]),
                         ["Amy Wilkinson", "Anna Wilkinson"])

    def test_authors_with_no_id_are_left_alone(self):
        works = [{"id": "https://openalex.org/W1", "title": "T",
                  "publication_year": 2020, "type": "article", "concepts": [],
                  "authorships": [{"author": {"display_name": "No Id Person"}}]}]
        canonicalize_authorships(works, merge_map={})
        self.assertIn("No Id Person", build_indexes(works)["by_person"])



class ShippedMergeMap(unittest.TestCase):
    """Validate the curated map that actually ships, not just the loader.

    The Panenka and Hutchison merges were written up as settled but never added
    to the file, so they silently never happened. These checks make that class
    of mistake fail loudly instead.
    """

    REPO = Path(__file__).resolve().parent.parent

    @classmethod
    def setUpClass(cls):
        import csv
        cls.path = cls.REPO / "people-merge-map.tsv"
        with cls.path.open(encoding="utf-8") as fh:
            cls.rows = list(csv.DictReader(fh, delimiter="\t"))

    def test_not_empty(self):
        self.assertGreater(len(self.rows), 50)

    def test_every_name_has_a_note_in_the_vault(self):
        from wellington_vault.notes import person_filename
        people = self.REPO / "vault" / "people"
        if not people.is_dir():
            self.skipTest("no vault checked out")
        missing = [n for r in self.rows for n in (r["canonical"], r["variant"])
                   if not (people / f"{person_filename(n)}.md").exists()]
        self.assertEqual(missing, [], "merge-map names with no person note")

    def test_variant_file_column_matches_slugify(self):
        from wellington_vault.notes import person_filename
        wrong = [r["variant"] for r in self.rows
                 if r["variant_file"] != f"{person_filename(r['variant'])}.md"]
        self.assertEqual(wrong, [], "variant_file out of step with person_filename()")

    def test_no_variant_listed_twice(self):
        seen = collections.Counter(r["variant"] for r in self.rows)
        self.assertEqual([n for n, c in seen.items() if c > 1], [])

    def test_no_chains(self):
        """A canonical name must not itself be someone else's variant."""
        canon = {r["canonical"] for r in self.rows}
        variants = {r["variant"] for r in self.rows}
        self.assertEqual(sorted(canon & variants), [])

    def test_confirmed_merges_are_present(self):
        """Decisions confirmed by the lab must actually be in the file."""
        pairs = {(r["canonical"], r["variant"]) for r in self.rows}
        for pair in [("William J. Panenka", "Will Panenka"),
                     ("James S. Hutchison", "Jamie Hutchison"),
                     ("Sonny Thiara", "Sharanjit Thiara"),
                     ("Rachel Zhao", "Rui Qi Zhao"),
                     ("Kris M. Martens", "Kristina Martens")]:
            self.assertIn(pair, pairs, f"{pair[1]} -> {pair[0]} missing from the merge map")

    def test_people_kept_apart_are_not_merged(self):
        """Pairs the lab confirmed as different people must never appear."""
        variants = {r["variant"] for r in self.rows}
        for name in ["Jennifer A. Chan", "Amy Wilkinson", "David R. Howell",
                     "David D. Howell", "Yu Deng"]:
            self.assertNotIn(name, variants, f"{name} was confirmed as a separate person")

if __name__ == "__main__":
    unittest.main()
