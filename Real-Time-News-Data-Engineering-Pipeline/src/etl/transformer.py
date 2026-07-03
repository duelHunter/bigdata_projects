import re
from datetime import datetime, timezone


# Articles NewsAPI marks as removed/unavailable
_REMOVED_SENTINEL = "[Removed]"


def transform(articles: list[dict]) -> tuple[list[dict], dict]:
    """
    Clean and standardize a list of raw NewsAPI articles.

    Returns:
        (clean_articles, report)  where report contains counts for each
        transformation step so the caller can log what happened.
    """
    report = {
        "input_count": len(articles),
        "removed_sentinel": 0,
        "missing_required": 0,
        "duplicates_removed": 0,
        "output_count": 0,
    }

    step1 = _drop_removed_sentinels(articles, report)
    step2 = _drop_missing_required(step1, report)
    step3 = _deduplicate(step2, report)
    cleaned = [_clean_record(a) for a in step3]

    report["output_count"] = len(cleaned)
    return cleaned, report


# ── Transform steps ────────────────────────────────────────────────────────────

def _drop_removed_sentinels(articles: list[dict], report: dict) -> list[dict]:
    """Drop articles NewsAPI marks as [Removed]."""
    result = []
    for a in articles:
        title = a.get("title") or ""
        content = a.get("content") or ""
        if _REMOVED_SENTINEL in title or _REMOVED_SENTINEL in content:
            report["removed_sentinel"] += 1
        else:
            result.append(a)
    return result


def _drop_missing_required(articles: list[dict], report: dict) -> list[dict]:
    """Drop articles that have no title or no URL — they are useless records."""
    result = []
    for a in articles:
        if not a.get("title") or not a.get("url"):
            report["missing_required"] += 1
        else:
            result.append(a)
    return result


def _deduplicate(articles: list[dict], report: dict) -> list[dict]:
    """Remove duplicate articles, keeping the first occurrence by URL."""
    seen_urls = set()
    result = []
    for a in articles:
        url = a.get("url", "").strip()
        if url in seen_urls:
            report["duplicates_removed"] += 1
        else:
            seen_urls.add(url)
            result.append(a)
    return result


def _clean_record(article: dict) -> dict:
    """Standardize a single article into a clean, flat dict."""
    source = article.get("source") or {}

    return {
        # Identifiers
        "url": _clean_text(article.get("url")),
        "source_id": _clean_text(source.get("id")),
        "source_name": _clean_text(source.get("name")),

        # Content
        "title": _clean_text(article.get("title")),
        "author": _clean_text(article.get("author")),
        "description": _clean_text(article.get("description")),
        "content": _truncate_content(article.get("content")),
        "url_to_image": _clean_text(article.get("urlToImage")),

        # Timestamps
        "published_at": _parse_timestamp(article.get("publishedAt")),
        "published_date": _parse_date(article.get("publishedAt")),

        # Provenance
        "_source_file": article.get("_source_file"),
        "_endpoint": article.get("_endpoint"),
    }


# ── Field-level helpers ────────────────────────────────────────────────────────

def _clean_text(value) -> str | None:
    if not value:
        return None
    cleaned = str(value).strip()
    # Collapse internal whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned if cleaned else None


def _parse_timestamp(value) -> str | None:
    """Return a UTC ISO-8601 string, or None if the value is unparseable."""
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.strptime(value.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            continue
    return value  # return as-is if nothing matched


def _parse_date(value) -> str | None:
    """Return 'YYYY-MM-DD' extracted from a publishedAt string."""
    ts = _parse_timestamp(value)
    if ts and len(ts) >= 10:
        return ts[:10]
    return None


def _truncate_content(value) -> str | None:
    """
    NewsAPI truncates content at 200 chars and appends ' [+N chars]'.
    Strip that suffix and return clean text.
    """
    cleaned = _clean_text(value)
    if not cleaned:
        return None
    return re.sub(r"\s*\[\+\d+ chars\]$", "", cleaned).strip() or None
