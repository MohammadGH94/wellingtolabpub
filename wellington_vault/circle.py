"""Minimal client for UBC Library Open Collections (cIRcle) search API.

Endpoint: https://oc-index.library.ubc.ca/search/8.5
Auth:     X-API-Key header (register at https://open.library.ubc.ca/research)
Docs:     https://open.library.ubc.ca/docs

Response shape (verified against probe responses):
    {
      "http_code": 200,
      "data": {
        "hits": {
          "total": <int>,
          "hits": [
            {"_id": "1.0052902", "_index": "dsp.831-...", "_score": <f>,
             "_source": {
                "title": ["..."], "creator": ["Surname, Forename"], "genre": [...],
                "description": ["abstract..."], "degree": ["..."],
                "program": ["..."], "affiliation": ["..."], "subject": ["..."],
                "campus": ["UBCV"], "scholarlyLevel": ["Graduate"],
                "ubc_date_sort": "1993-12-31 AD",
                "dateAvailable": "2008-08-05T00:00:00Z",
                "ubc_internal_repo": "dsp", "ubc_internal_handle": "..."
             }},
            ...
          ]}}}

The structured `Supervisor` field is NOT exposed in this index, so we can't
filter by supervisor. Instead the build pipeline cross-references trainees
(first-authors of Wellington-last-author papers from OpenAlex) against
`creator` here.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_BASE = "https://oc-index.library.ubc.ca/search/8.5"
USER_AGENT = "wellington-vault/0.1 (https://github.com/MohammadGH94/wellingtolabpub)"


class CircleError(RuntimeError):
    pass


class CircleClient:
    def __init__(self, api_key: str, cache_dir: Path, refresh: bool = False):
        if not api_key:
            raise ValueError("CircleClient requires a non-empty api_key.")
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.refresh = refresh
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ── HTTP layer ──────────────────────────────────────────────────────────

    def _cache_path(self, url: str) -> Path:
        # API key lives in headers, not the URL, so the URL is safe to hash.
        h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        return self.cache_dir / f"{h}.json"

    def _get(self, params: dict) -> dict:
        query = urllib.parse.urlencode(params, doseq=True, safe=':/"')
        url = f"{API_BASE}?{query}"
        cache = self._cache_path(url)
        if cache.exists() and not self.refresh:
            return json.loads(cache.read_text("utf-8"))

        last_err: Exception | None = None
        for attempt in range(5):
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "X-API-Key": self.api_key,
                    },
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                cache.write_text(json.dumps(data), "utf-8")
                return data
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(2**attempt)
                    last_err = e
                    continue
                raise CircleError(f"HTTP {e.code} on {url}: {e.reason}") from e
            except urllib.error.URLError as e:
                time.sleep(2**attempt)
                last_err = e
        raise CircleError(f"Repeated failure on {url}: {last_err}")

    # ── Public methods ──────────────────────────────────────────────────────

    def search_theses_by_creator(
        self, creator_lastname_first: str, size: int = 5
    ) -> list[dict]:
        """Return ES hits (full envelope incl. _id) for theses by the named creator.

        `creator_lastname_first` must be in cIRcle's "Surname, Forename" format.
        Genre filter narrows the index to thesis records.
        """
        if not creator_lastname_first:
            return []
        q = f'creator:"{creator_lastname_first}" AND genre:"Thesis/Dissertation"'
        data = self._get({"q": q, "size": size})
        hits_block = ((data.get("data") or {}).get("hits") or {}).get("hits") or []
        return [h for h in hits_block if isinstance(h, dict)]


# ── Name format helpers ────────────────────────────────────────────────────


def to_lastname_first(display_name: str) -> str:
    """Convert OpenAlex "Forename Middle Surname" → cIRcle "Surname, Forename Middle".

    Naive: assumes the last whitespace-separated token is the surname. This is
    correct for the majority of OpenAlex display names; unusual cases (compound
    surnames like "van der Berg") will still produce a usable, if imperfect,
    query — cIRcle's analyzer is forgiving.
    """
    parts = (display_name or "").strip().split()
    if len(parts) < 2:
        return display_name or ""
    return f"{parts[-1]}, {' '.join(parts[:-1])}"


def from_lastname_first(name: str) -> str:
    """Convert cIRcle "Surname, Forename" → "Forename Surname" for display/slug.

    If `name` lacks a comma it is returned unchanged.
    """
    if not name or "," not in name:
        return name or ""
    surname, _, forename = name.partition(",")
    return f"{forename.strip()} {surname.strip()}".strip()
