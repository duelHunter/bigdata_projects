"""
Database schema for the news data warehouse.

Tables:
    sources  — unique news publishers
    articles — individual news articles (one row per URL)
"""

from connection import get_connection

CREATE_SOURCES = """
CREATE TABLE IF NOT EXISTS sources (
    id          SERIAL PRIMARY KEY,
    source_id   TEXT,
    source_name TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source_id, source_name)
);
"""

CREATE_ARTICLES = """
CREATE TABLE IF NOT EXISTS articles (
    id             SERIAL PRIMARY KEY,
    url            TEXT NOT NULL UNIQUE,
    source_id      INTEGER REFERENCES sources(id),
    title          TEXT NOT NULL,
    author         TEXT,
    description    TEXT,
    content        TEXT,
    url_to_image   TEXT,
    published_at   TIMESTAMPTZ,
    published_date DATE,
    ingested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

CREATE_INDEX_PUBLISHED_DATE = """
CREATE INDEX IF NOT EXISTS idx_articles_published_date
    ON articles (published_date);
"""

CREATE_INDEX_SOURCE = """
CREATE INDEX IF NOT EXISTS idx_articles_source_id
    ON articles (source_id);
"""


def init_schema():
    """Create all tables and indexes. Safe to run multiple times (IF NOT EXISTS)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_SOURCES)
            cur.execute(CREATE_ARTICLES)
            cur.execute(CREATE_INDEX_PUBLISHED_DATE)
            cur.execute(CREATE_INDEX_SOURCE)
    print("Schema initialised.")


def drop_schema():
    """Drop all tables — useful for a clean reset during development."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS articles CASCADE;")
            cur.execute("DROP TABLE IF EXISTS sources CASCADE;")
    print("Schema dropped.")


if __name__ == "__main__":
    init_schema()
