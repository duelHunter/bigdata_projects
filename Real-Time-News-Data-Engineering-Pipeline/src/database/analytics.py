"""
Phase 5 — Analytics queries.

Every function returns a list of dicts so callers can format however they like.
"""

import re
from collections import Counter

from connection import get_cursor


# ── 1. Top news sources ────────────────────────────────────────────────────────

def top_sources(limit: int = 10) -> list[dict]:
    """Publishers ranked by article count with coverage %."""
    sql = """
        WITH total AS (SELECT COUNT(*) AS n FROM articles)
        SELECT
            COALESCE(s.source_name, 'Unknown') AS source,
            COUNT(a.id)                         AS articles,
            ROUND(COUNT(a.id) * 100.0 / total.n, 1) AS pct
        FROM articles a
        LEFT JOIN sources s ON s.id = a.source_id
        CROSS JOIN total
        GROUP BY s.source_name, total.n
        ORDER BY articles DESC
        LIMIT %s;
    """
    with get_cursor() as cur:
        cur.execute(sql, (limit,))
        return [dict(r) for r in cur.fetchall()]


# ── 2. Articles per day ────────────────────────────────────────────────────────

def articles_per_day() -> list[dict]:
    """Daily article volume — useful for spotting collection gaps."""
    sql = """
        SELECT
            published_date,
            COUNT(*) AS articles
        FROM articles
        WHERE published_date IS NOT NULL
        GROUP BY published_date
        ORDER BY published_date;
    """
    with get_cursor() as cur:
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]


# ── 3. Most active publishers (authors) ───────────────────────────────────────

def top_authors(limit: int = 10) -> list[dict]:
    """Authors ranked by byline count, excluding nulls."""
    sql = """
        SELECT
            author,
            COUNT(*) AS articles
        FROM articles
        WHERE author IS NOT NULL
        GROUP BY author
        ORDER BY articles DESC
        LIMIT %s;
    """
    with get_cursor() as cur:
        cur.execute(sql, (limit,))
        return [dict(r) for r in cur.fetchall()]


# ── 4. Publishing hour distribution ───────────────────────────────────────────

def articles_by_hour() -> list[dict]:
    """Article count grouped by hour of day (UTC) — reveals publishing patterns."""
    sql = """
        SELECT
            EXTRACT(HOUR FROM published_at)::INT AS hour_utc,
            COUNT(*) AS articles
        FROM articles
        WHERE published_at IS NOT NULL
        GROUP BY hour_utc
        ORDER BY hour_utc;
    """
    with get_cursor() as cur:
        cur.execute(sql)
        return [dict(r) for r in cur.fetchall()]


# ── 5. Trending keywords ───────────────────────────────────────────────────────

def trending_keywords(limit: int = 20, min_length: int = 4) -> list[dict]:
    """
    Most frequent words in article titles.
    Runs in Python over a SQL result set — no PostgreSQL extensions needed.
    """
    stop_words = {
        "this", "that", "with", "from", "have", "will", "been", "were",
        "they", "their", "what", "when", "where", "which", "after",
        "about", "more", "over", "than", "into", "also", "just", "your",
        "says", "said", "says", "would", "could", "should", "much",
        "how", "why", "who", "the", "and", "for", "are", "but", "not",
        "you", "all", "can", "has", "her", "his", "one", "our", "out",
        "use", "day", "new", "now", "its", "may", "some", "like",
    }

    with get_cursor() as cur:
        cur.execute("SELECT title FROM articles WHERE title IS NOT NULL;")
        titles = [row["title"] for row in cur.fetchall()]

    words = []
    for title in titles:
        tokens = re.findall(r"[a-zA-Z]+", title.lower())
        words.extend(
            w for w in tokens
            if len(w) >= min_length and w not in stop_words
        )

    counts = Counter(words).most_common(limit)
    return [{"keyword": word, "count": cnt} for word, cnt in counts]


# ── 6. Database summary ────────────────────────────────────────────────────────

def db_summary() -> dict:
    """High-level counts across the warehouse."""
    sql = """
        SELECT
            (SELECT COUNT(*)                    FROM articles)     AS total_articles,
            (SELECT COUNT(DISTINCT source_id)   FROM articles)     AS total_sources,
            (SELECT COUNT(DISTINCT author)       FROM articles
             WHERE author IS NOT NULL)                             AS total_authors,
            (SELECT COUNT(DISTINCT published_date) FROM articles
             WHERE published_date IS NOT NULL)                     AS days_covered,
            (SELECT MIN(published_date)          FROM articles
             WHERE published_date IS NOT NULL)                     AS earliest_date,
            (SELECT MAX(published_date)          FROM articles
             WHERE published_date IS NOT NULL)                     AS latest_date;
    """
    with get_cursor() as cur:
        cur.execute(sql)
        return dict(cur.fetchone())


# ── 7. Recent articles ─────────────────────────────────────────────────────────

def recent_articles(limit: int = 10) -> list[dict]:
    """Most recently published articles with source name."""
    sql = """
        SELECT
            a.title,
            COALESCE(s.source_name, 'Unknown') AS source,
            a.published_date,
            a.url
        FROM articles a
        LEFT JOIN sources s ON s.id = a.source_id
        WHERE a.published_at IS NOT NULL
        ORDER BY a.published_at DESC
        LIMIT %s;
    """
    with get_cursor() as cur:
        cur.execute(sql, (limit,))
        return [dict(r) for r in cur.fetchall()]
