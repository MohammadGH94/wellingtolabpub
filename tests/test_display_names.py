"""Tests for how the browser decides what one person is called.

The vault keys a person on the wikilink *target* — the person note's filename.
The browser used to key them on the *alias*, which is only how one paper spelled
them, so a person OpenAlex spelled two ways became two people sharing their own
papers. `resolve_labels()` is the fix; these tests hold it in place.

Run with:  python -m unittest discover -s tests
"""

from __future__ import annotations

import re
import sys
import unicodedata
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "human"))

from build_human import link_parts, resolve_labels, unlink  # noqa: E402


class LinkParts(unittest.TestCase):
    def test_splits_target_from_alias(self):
        self.assertEqual(link_parts("[[Jose Rodriguez|José Rodríguez]]"),
                         ("Jose Rodriguez", "José Rodríguez"))

    def test_unaliased_link_is_its_own_alias(self):
        self.assertEqual(link_parts("[[Cheryl L. Wellington]]"),
                         ("Cheryl L. Wellington", "Cheryl L. Wellington"))

    def test_first_pipe_separates(self):
        """wikilink() rewrites any `|` inside a target, so the first one is it."""
        self.assertEqual(link_parts("[[A|B|C]]"), ("A", "B|C"))

    def test_empty_alias_falls_back_to_target(self):
        self.assertEqual(link_parts("[[Some Person|]]"), ("Some Person", "Some Person"))


class ResolveLabels(unittest.TestCase):
    def test_most_papers_wins(self):
        """The real case: six papers say Diaz‐Arrastia, a seventh says Diaz Arrastia."""
        papers = [[("Ramon Diaz Arrastia", "Ramon Diaz‐Arrastia")]] * 6 \
               + [[("Ramon Diaz Arrastia", "Ramon Diaz Arrastia")]]
        self.assertEqual(resolve_labels(papers),
                         {"Ramon Diaz Arrastia": "Ramon Diaz‐Arrastia"})

    def test_tie_goes_to_the_accented_spelling(self):
        """A stripped spelling is the lossy one, so it loses an otherwise even tie."""
        papers = [[("Elodie Bouaziz-Amar", "Élodie Bouaziz-Amar")],
                  [("Elodie Bouaziz-Amar", "Elodie Bouaziz-Amar")]]
        self.assertEqual(resolve_labels(papers)["Elodie Bouaziz-Amar"],
                         "Élodie Bouaziz-Amar")

    def test_ties_are_broken_deterministically(self):
        """Same notes in, same page out — otherwise rebuilds churn the diff."""
        pairs = [[("T", "Ann Lee")], [("T", "Ann Loe")]]
        self.assertEqual(resolve_labels(pairs)["T"], resolve_labels(reversed(pairs))["T"])

    def test_distinct_targets_stay_distinct(self):
        """Different notes are different people, however alike they are spelled."""
        papers = [[("Alicia Algeciras Schimnich", "Alicia Algeciras‐Schimnich")],
                  [("Alicia Algeciras-Schimnich", "Alicia Algeciras-Schimnich")]]
        self.assertEqual(len(resolve_labels(papers)), 2)


class Unlink(unittest.TestCase):
    def test_labels_collapse_variant_spellings_to_one_person(self):
        labels = resolve_labels([[("Jens Kuhle", "Jens Kühle")]] * 3
                                + [[("Jens Kuhle", "Jens Kuhle")]])
        got = {unlink(["[[Jens Kuhle|Jens Kühle]]"], labels)[0],
               unlink(["[[Jens Kuhle]]"], labels)[0]}
        self.assertEqual(got, {"Jens Kühle"}, "both links must name the same person")

    def test_without_labels_the_split_comes_back(self):
        """Guards the regression itself: no labels means alias-keying means two people."""
        got = {unlink(["[[Jens Kuhle|Jens Kühle]]"])[0], unlink(["[[Jens Kuhle]]"])[0]}
        self.assertEqual(len(got), 2)

    def test_non_list_is_empty(self):
        self.assertEqual(unlink(""), [])
        self.assertEqual(unlink(None), [])


class ShippedPage(unittest.TestCase):
    """Run the real collector over the real vault: no person may appear twice."""

    @classmethod
    def setUpClass(cls):
        if not (REPO / "vault" / "papers").is_dir():
            raise unittest.SkipTest("no vault checked out")
        from build_human import DEFAULT_MERGE_MAP, collect
        from wellington_vault.build import load_merge_map
        cls.data = collect(str(REPO / "vault"),
                           merge_map=load_merge_map(Path(DEFAULT_MERGE_MAP)))

    @staticmethod
    def key(name: str) -> str:
        """Ignore case, diacritics and every flavour of punctuation."""
        s = unicodedata.normalize("NFKD", name)
        s = "".join(c for c in s if not unicodedata.combining(c))
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", s.lower())).strip()

    def test_no_person_appears_under_two_spellings(self):
        import collections
        seen = collections.defaultdict(list)
        for person in self.data["people"]:
            seen[self.key(person["n"])].append(person["n"])
        dupes = {k: v for k, v in seen.items() if len(v) > 1}
        self.assertEqual(dupes, {}, "same person listed under several spellings")

    def test_no_person_listed_twice_on_one_paper(self):
        for paper in self.data["papers"]:
            self.assertEqual(len(paper["a"]), len(set(paper["a"])), paper["t"])

    def test_paper_counts_match_an_independent_count_over_the_notes(self):
        """Re-derive every person's total straight from the paper notes, by target.

        Deliberately not compared against `papers_with_wellington_lab` in the
        person notes: those were written from the build's in-memory index, and
        several papers never reached disk because their filenames collided
        (318 works, 306 files), so the notes overcount. Counting the targets in
        `papers/` is the same question asked of what is actually there.
        """
        import collections
        from wellington_vault.notes import person_filename
        expected: collections.Counter = collections.Counter()
        for path in sorted((REPO / "vault" / "papers").glob("*.md")):
            fm = path.read_text(encoding="utf-8").split("---")[1]
            targets, in_authors = set(), False
            for line in fm.splitlines():
                if re.match(r"^authors:\s*$", line):
                    in_authors = True
                    continue
                if in_authors:
                    item = re.match(r"^\s+-\s+(.*)$", line)
                    if not item:
                        break
                    targets.add(link_parts(item.group(1).strip('"'))[0])
            expected.update(targets)

        # People in a merge cluster draw papers from several targets by design,
        # so a per-target count does not apply to them; test_merge_map covers those.
        import csv
        merged = set()
        with (REPO / "people-merge-map.tsv").open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                merged.update({person_filename(row["canonical"]),
                               person_filename(row["variant"])})

        mismatched = [(p["n"], p["p"], expected[person_filename(p["n"])])
                      for p in self.data["people"]
                      if person_filename(p["n"]) in expected
                      and person_filename(p["n"]) not in merged
                      and p["p"] != expected[person_filename(p["n"])]]
        self.assertEqual(mismatched, [], "(name, browser count, count over papers/)")


if __name__ == "__main__":
    unittest.main()
