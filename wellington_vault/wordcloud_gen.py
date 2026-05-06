"""Render a word-cloud PNG from paper + thesis abstracts.

Optional feature. Activates when the third-party `wordcloud` package is
importable; otherwise the build pipeline calls `render_wordcloud()` and
gets `False`, prints an install hint, and continues without failing.
"""

from __future__ import annotations

from pathlib import Path

from .util import pluck, reconstruct_abstract

# Research-paper boilerplate that adds noise to a Wellington-lab summary.
# Layered on top of the wordcloud package's English STOPWORDS list at
# render time (see `render_wordcloud`).
DOMAIN_STOPWORDS = frozenset({
    "study", "studies", "result", "results", "method", "methods",
    "data", "patient", "patients", "may", "however", "also", "show",
    "shown", "showed", "found", "using", "use", "used", "well",
    "one", "two", "three", "four", "five", "high", "low", "increase",
    "decrease", "increased", "decreased", "significantly", "compared",
    "group", "groups", "level", "levels", "n", "vs", "versus",
    "p", "ci", "respectively", "associated", "association",
    "background", "objective", "conclusion", "conclusions",
    "abstract", "introduction", "discussion",
})


def collect_abstracts(
    works: list[dict],
    circle_theses: list[dict] | None = None,
) -> str:
    """Concatenate every paper abstract + cIRcle thesis description into one string.

    OpenAlex abstracts live as inverted indexes (`{token: [positions]}`) for
    Elsevier compliance — `reconstruct_abstract` turns them back into linear
    text. cIRcle exposes thesis abstracts directly under `_source.description`.
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
                parts.append(desc)
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
        max_words=200,
        relative_scaling=0.5,
    ).generate(text)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wc.to_file(str(out_path))
    return True
