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
    # Quantitative / statistical boilerplate
    "study", "studies", "result", "results", "method", "methods",
    "data", "may", "also", "show", "shown", "showed", "found",
    "using", "use", "used", "well", "one", "two", "three", "four", "five",
    "high", "low", "increase", "decrease", "increased", "decreased",
    "significantly", "significant", "compared", "group", "groups",
    "level", "levels", "n", "vs", "versus", "p", "ci", "respectively",
    "associated", "association", "total", "similar",
    # Structural / rhetorical words
    "background", "objective", "conclusion", "conclusions",
    "abstract", "introduction", "discussion", "however",
    "although", "within", "across", "several", "many", "area",
    "following", "including", "difference", "present",
    # Generic academic filler
    "role", "effect", "effects", "time", "future", "case", "cases",
    "report", "reports", "dose", "lead", "improve", "without",
    "known", "individual", "individuals", "sample", "samples",
    "assay", "assays", "influence", "measure", "measured",
    "demonstrate", "demonstrates", "demonstrated", "demonstrating",
    "suggest", "suggests", "suggested", "suggesting",
    "different", "major", "important", "primary", "novel",
    "observed", "based", "development", "understanding",
    "contribute", "contributes", "evidence", "affect", "affects",
    "support", "supports", "activity", "potential", "response",
    "responses", "health", "work", "provide", "provides",
    "test", "tests", "change", "changes", "identify", "identified",
    "indicate", "indicates", "indicated", "include", "includes",
    "included", "first", "second", "third", "number", "numbers",
    "large", "small", "multiple", "specific", "overall", "current",
    "recent", "likely", "whether", "thus", "therefore", "furthermore",
    "additionally", "moreover", "especially", "particularly",
    "patient", "patients",
    # Single-char and numeric-looking tokens (catch-all; min_word_length
    # in WordCloud handles single chars, but belt-and-suspenders)
    "h", "h2", "h3", "h4", "p", "b", "i", "s", "d", "m",
    "li", "ul", "ol", "br", "hr", "div", "span", "em", "strong",
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
