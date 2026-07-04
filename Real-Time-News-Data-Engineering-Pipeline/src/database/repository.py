"""
CRUD operations for sources and articles.
"""

from connection import get_connection, get_cursor


# ── Sources ────────────────────────────────────────────────────────────────────

def upsert_source(source_id: str | None, source_name: str | None) -> int | None:
    """
    Insert a source if it doesn't exist, then return its primary key.
    Returns None if source_name is empty (can't store anonymous sources).
    """
    if not source_name:
        return None

    sql = """
        INSERT INTO sources (source_id, source_name)
        VALUES (%s, %s)
        ON CONFLICT (source_id, source_name) DO UPDATE
            SET source_name = EXCLUDED.source_name
        RETURNING id;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (source_id, source_name))
            row = cur.fetchone()
            return row[0] if row else None


# ── Articles ───────────────────────────────────────────────────────────────────

def insert_article(article: dict, source_pk: int | None) -> bool:
    """
    Insert one article. Skips silently if the URL already exists.
    Returns True if inserted, False if skipped (duplicate).
    """
    sql = """
        INSERT INTO articles
            (url, source_id, title, author, description, content,
             url_to_image, published_at, published_date)
        VALUES
            (%(url)s, %(source_id)s, %(title)s, %(author)s, %(description)s,
             %(content)s, %(url_to_image)s, %(published_at)s, %(published_date)s)
        ON CONFLICT (url) DO NOTHING;
    """
    params = {
        "url": article["url"],
        "source_id": source_pk,
        "title": article["title"],
        "author": article.get("author"),
        "description": article.get("description"),
        "content": article.get("content"),
        "url_to_image": article.get("url_to_image"),
        "published_at": article.get("published_at"),
        "published_date": article.get("published_date"),
    }
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount == 1


def bulk_insert_articles(articles: list[dict]) -> dict:
    """
    Insert a batch of clean articles, upserting sources as needed.
    Returns a report: {inserted, skipped, errors}.
    """
    report = {"inserted": 0, "skipped": 0, "errors": 0}

    for article in articles:
        try:
            source_pk = upsert_source(
                article.get("source_id"),
                article.get("source_name"),
            )
            inserted = insert_article(article, source_pk)
            if inserted:
                report["inserted"] += 1
            else:
                report["skipped"] += 1
        except Exception as e:
            report["errors"] += 1
            print(f"  Error inserting {article.get('url')}: {e}")

    return report


# ── Queries ────────────────────────────────────────────────────────────────────

def get_article_count() -> int:
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM articles;")
        return cur.fetchone()["count"]


def get_articles_by_date(published_date: str) -> list[dict]:
    """Return all articles published on a given date (YYYY-MM-DD)."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM articles WHERE published_date = %s ORDER BY published_at;",
            (published_date,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_top_sources(limit: int = 10) -> list[dict]:
    """Return sources ranked by article count."""
    sql = """
        SELECT s.source_name, COUNT(a.id) AS article_count
        FROM articles a
        JOIN sources s ON s.id = a.source_id
        GROUP BY s.source_name
        ORDER BY article_count DESC
        LIMIT %s;
    """
    with get_cursor() as cur:
        cur.execute(sql, (limit,))
        return [dict(row) for row in cur.fetchall()]


def get_articles_per_day() -> list[dict]:
    """Return article counts grouped by published_date."""
    sql = """
        SELECT published_date, COUNT(*) AS article_count
        FROM articles
        WHERE published_date IS NOT NULL
        GROUP BY published_date
        ORDER BY published_date;
    """
    with get_cursor() as cur:
        cur.execute(sql)
        return [dict(row) for row in cur.fetchall()]


def search_articles(keyword: str, limit: int = 20) -> list[dict]:
    """Full-text search across title and description."""
    sql = """
        SELECT id, title, source_id, published_date, url
        FROM articles
        WHERE title ILIKE %s OR description ILIKE %s
        ORDER BY published_at DESC
        LIMIT %s;
    """
    pattern = f"%{keyword}%"
    with get_cursor() as cur:
        cur.execute(sql, (pattern, pattern, limit))
        return [dict(row) for row in cur.fetchall()]
