"""Render a word-cloud PNG from paper + thesis abstracts.

Optional feature. Activates when the third-party `wordcloud` package is
importable; otherwise the build pipeline calls `render_wordcloud()` and
gets `False`, prints an install hint, and continues without failing.
"""

from __future__ import annotations

import re
from pathlib import Path

from .util import pluck, reconstruct_abstract

# Research-paper boilerplate and generic academic filler that adds noise to
# a Wellington-lab subject summary.  Layered on top of the wordcloud
# package's English STOPWORDS list at render time (see `render_wordcloud`).
DOMAIN_STOPWORDS = frozenset({
    # ── Time units ──────────────────────────────────────────────────────────
    "week", "weeks", "month", "months", "day", "days", "year", "years",
    "early", "late", "baseline", "prior", "post",
    # ── Participants / subjects ──────────────────────────────────────────────
    "patient", "patients", "participant", "participants",
    "subject", "subjects", "individual", "individuals",
    "cohort", "cohorts", "male", "female", "sex",
    # ── Generic experimental design ─────────────────────────────────────────
    "control", "controls", "model", "models",
    "animal", "animals", "vivo", "vitro",
    "group", "groups", "arm", "arms",
    "design", "study", "studies",
    # ── Quantitative / statistical boilerplate ───────────────────────────────
    "result", "results", "method", "methods", "data",
    "analysis", "analyses", "sample", "samples",
    "level", "levels", "score", "scores",
    "number", "numbers", "percent", "percentage",
    "n", "vs", "versus", "p", "ci", "pg", "ml",
    "respectively", "significantly", "significant",
    "associated", "association", "correlation",
    "total", "overall", "mean", "average", "median",
    "increase", "decrease", "increased", "decreased",
    "greater", "higher", "lower", "reduced", "elevated",
    "similar", "difference", "differences",
    # ── Generic verbs / research filler ─────────────────────────────────────
    "show", "shown", "showed", "find", "found", "finding", "findings",
    "suggest", "suggests", "suggested", "suggesting",
    "demonstrate", "demonstrates", "demonstrated", "demonstrating",
    "indicate", "indicates", "indicated",
    "report", "reports", "reported", "reporting",
    "assess", "assessed", "assessment",
    "determine", "determined",
    "investigate", "investigated",
    "induce", "induced", "induction",
    "conduct", "conducted",
    "derive", "derived",
    "collect", "collected", "collection",
    "establish", "established",
    "develop", "developed", "development",
    "play", "plays",
    "may", "also", "using", "use", "used",
    "well", "due", "will", "can", "also",
    # ── Generic adjectives / nouns ───────────────────────────────────────────
    "role", "effect", "effects", "impact", "impacts",
    "factor", "factors", "context", "condition", "conditions",
    "human", "humans", "research", "review", "reviews",
    "clinical", "preclinical", "treatment", "treatments",
    "outcome", "outcomes", "response", "responses",
    "function", "functions", "form", "forms",
    "target", "targets", "marker", "markers",
    "key", "novel", "new", "normal", "common",
    "primary", "secondary", "major", "minor",
    "important", "specific", "large", "small",
    "current", "recent", "future", "time", "case", "cases",
    "provide", "provides", "support", "supports",
    "contribute", "contributes", "evidence",
    "influence", "measure", "measured",
    "improve", "reduction", "activity",
    "health", "work", "known", "without", "following",
    "including", "across", "several", "many", "area",
    "although", "however", "potential", "understanding",
    "one", "two", "three", "four", "five",
    # ── Structural / document words ───────────────────────────────────────────
    "background", "objective", "conclusion", "conclusions",
    "abstract", "introduction", "discussion",
    # ── HTML tag remnants (belt-and-suspenders; _strip_html handles these) ───
    "h2", "h3", "h4", "li", "ul", "ol", "br", "div", "span",
})

_HTML_TAG = re.compile(r"<[^>]+>")
_MULTI_SPACE = re.compile(r"\s+")


def _strip_html(text: str) -> str:
    """Remove HTML markup. cIRcle thesis descriptions often contain raw HTML."""
    text = _HTML_TAG.sub(" ", text)
    return _MULTI_SPACE.sub(" ", text).strip()


def collect_abstracts(
    works: list[dict],
    circle_theses: list[dict] | None = None,
) -> str:
    """Concatenate every paper abstract + cIRcle thesis description into one string.

    OpenAlex abstracts live as inverted indexes (`{token: [positions]}`) for
    Elsevier compliance — `reconstruct_abstract` turns them back into linear
    text. cIRcle exposes thesis abstracts directly under `_source.description`;
    those may contain raw HTML which is stripped before inclusion.
    """
    parts: list[str] = []
    for w in works:
        inv = pluck(w, "abstract_inverted_index")
        text = reconstruct_abstract(inv) if inv else ""
        if text:
            parts.append(text)
    for hit in circle_theses or []:
        src = hit.get("_source") or {}
        for desc in src.get("description") or []:
            if isinstance(desc, str) and desc.strip():
                parts.append(_strip_html(desc))
    return " ".join(parts)


def render_wordcloud(
    text: str,
    out_path: Path,
    width: int = 1600,
    height: int = 900,
) -> bool:
    """Write a word-cloud PNG to `out_path`. Returns False if wordcloud isn't installed."""
    try:
        from wordcloud import STOPWORDS, WordCloud
    except ImportError:
        return False
    if not text.strip():
        return False
    stopwords = set(STOPWORDS) | DOMAIN_STOPWORDS
    wc = WordCloud(
        width=width,
        height=height,
        background_color="white",
        stopwords=stopwords,
        collocations=True,
        min_word_length=3,
        max_words=200,
        relative_scaling=0.5,
    ).generate(text)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wc.to_file(str(out_path))
    return True
