"""Minimal OpenAlex client — stdlib only, with on-disk JSON cache.

OpenAlex API docs: https://docs.openalex.org/
- Polite pool (faster + more reliable): pass `mailto=<your-email>` query param.
- Pagination: cursor-based via `cursor=*` then meta.next_cursor.
- Authors: /authors?search=...&filter=last_known_institutions.ror:...
- Works:   /works?filter=author.id:A...&per-page=200&cursor=...
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Iterator

API_BASE = "https://api.openalex.org"
USER_AGENT = "wellington-vault/0.1 (https://github.com/MohammadGH94/wellingtolabpub)"


class OpenAlexError(RuntimeError):
    pass


class OpenAlexClient:
    def __init__(self, mailto: str | None, cache_dir: Path, refresh: bool = False):
        self.mailto = mailto
        self.cache_dir = cache_dir
        self.refresh = refresh
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ── HTTP layer ──────────────────────────────────────────────────────────

    def _cache_path(self, url: str) -> Path:
        h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
        return self.cache_dir / f"{h}.json"

    def _get(self, path: str, params: dict | None = None) -> dict:
        params = dict(params or {})
        if self.mailto:
            params.setdefault("mailto", self.mailto)
        query = urllib.parse.urlencode(params, doseq=True, safe=":/")
        url = f"{API_BASE}{path}" + (f"?{query}" if query else "")
        cache = self._cache_path(url)
        if cache.exists() and not self.refresh:
            return json.loads(cache.read_text("utf-8"))

        last_err: Exception | None = None
        for attempt in range(5):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                cache.write_text(json.dumps(data), "utf-8")
                return data
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504):
                    time.sleep(2**attempt)
                    last_err = e
                    continue
                raise OpenAlexError(f"HTTP {e.code} on {url}: {e.reason}") from e
            except urllib.error.URLError as e:
                time.sleep(2**attempt)
                last_err = e
        raise OpenAlexError(f"Repeated failure on {url}: {last_err}")

    # ── Public methods ──────────────────────────────────────────────────────

    def search_authors(self, name: str, institution_hint: str | None = None) -> list[dict]:
        """Search authors by name. `institution_hint` is a substring matched
        case-insensitively against last_known_institutions[].display_name."""
        data = self._get("/authors", {"search": name, "per-page": 25})
        results = data.get("results", [])
        if institution_hint:
            hint = institution_hint.lower()
            results = [
                a
                for a in results
                if any(
                    hint in (inst.get("display_name") or "").lower()
                    for inst in (a.get("last_known_institutions") or [])
                )
            ]
        return results

    def get_author(self, author_id: str) -> dict:
        author_id = _strip_openalex_prefix(author_id)
        return self._get(f"/authors/{author_id}")

    def iter_works(self, author_id: str, per_page: int = 200) -> Iterator[dict]:
        """Yield every work for the given author, following cursor pagination."""
        author_id = _strip_openalex_prefix(author_id)
        cursor = "*"
        seen = 0
        while cursor:
            data = self._get(
                "/works",
                {
                    "filter": f"author.id:{author_id}",
                    "per-page": per_page,
                    "cursor": cursor,
                    "sort": "publication_date:desc",
                },
            )
            for work in data.get("results", []):
                seen += 1
                yield work
            cursor = (data.get("meta") or {}).get("next_cursor")
            if not cursor:
                break


def _strip_openalex_prefix(author_id: str) -> str:
    """Accept `https://openalex.org/A123` or `openalex.org/A123` or `A123`."""
    if "/" in author_id:
        author_id = author_id.rstrip("/").rsplit("/", 1)[-1]
    return author_id
