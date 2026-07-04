"""
Phase 5 — Analytics report runner.

Prints a formatted CLI report for every analytics query.

Usage:
    python src/database/analytics_report.py
    python src/database/analytics_report.py --section sources
    python src/database/analytics_report.py --section keywords
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analytics import (
    db_summary,
    top_sources,
    articles_per_day,
    top_authors,
    articles_by_hour,
    trending_keywords,
    recent_articles,
)


# ── Formatting helpers ─────────────────────────────────────────────────────────

def _header(title: str):
    width = 55
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def _table(rows: list[dict], cols: list[tuple[str, int, str]]):
    """
    Print a simple fixed-width table.
    cols: list of (key, width, label)
    """
    if not rows:
        print("  (no data)")
        return

    header = "  " + "  ".join(f"{label:<{w}}" for _, w, label in cols)
    separator = "  " + "  ".join("-" * w for _, w, _ in cols)
    print(header)
    print(separator)
    for row in rows:
        line = "  " + "  ".join(
            f"{str(row.get(key, '')):<{w}}"[:w] for key, w, _ in cols
        )
        print(line)


def _bar_chart(rows: list[dict], key_col: str, val_col: str, bar_width: int = 30):
    """ASCII horizontal bar chart."""
    if not rows:
        print("  (no data)")
        return
    max_val = max(r[val_col] for r in rows) or 1
    for row in rows:
        label = str(row[key_col])[:20]
        val = row[val_col]
        bars = int(val / max_val * bar_width)
        print(f"  {label:<22} {'█' * bars} {val}")


# ── Report sections ────────────────────────────────────────────────────────────

def section_summary():
    _header("Database Summary")
    s = db_summary()
    print(f"  Total articles  : {s['total_articles']}")
    print(f"  Total sources   : {s['total_sources']}")
    print(f"  Total authors   : {s['total_authors']}")
    print(f"  Days covered    : {s['days_covered']}")
    print(f"  Date range      : {s['earliest_date']}  →  {s['latest_date']}")


def section_top_sources():
    _header("Top News Sources")
    rows = top_sources(limit=10)
    _table(rows, [
        ("source",   28, "Source"),
        ("articles",  8, "Articles"),
        ("pct",       6, "  %"),
    ])


def section_articles_per_day():
    _header("Articles per Day")
    rows = articles_per_day()
    _bar_chart(rows, "published_date", "articles")


def section_top_authors():
    _header("Most Active Authors")
    rows = top_authors(limit=10)
    _table(rows, [
        ("author",   35, "Author"),
        ("articles",  8, "Articles"),
    ])


def section_hours():
    _header("Publishing Hour Distribution (UTC)")
    rows = articles_by_hour()
    hour_map = {r["hour_utc"]: r["articles"] for r in rows}
    max_val = max(hour_map.values()) if hour_map else 1
    for h in range(24):
        count = hour_map.get(h, 0)
        bars = int(count / max_val * 30)
        print(f"  {h:02d}:00  {'█' * bars} {count}")


def section_trending_keywords():
    _header("Trending Keywords (Title Analysis)")
    rows = trending_keywords(limit=20)
    _bar_chart(rows, "keyword", "count", bar_width=25)


def section_recent():
    _header("10 Most Recent Articles")
    rows = recent_articles(limit=10)
    for i, r in enumerate(rows, 1):
        title = r["title"][:60] + ("…" if len(r["title"]) > 60 else "")
        print(f"  {i:2}. [{r['published_date']}] {r['source']}")
        print(f"      {title}")


# ── Entry point ────────────────────────────────────────────────────────────────

SECTIONS = {
    "summary":  section_summary,
    "sources":  section_top_sources,
    "daily":    section_articles_per_day,
    "authors":  section_top_authors,
    "hours":    section_hours,
    "keywords": section_trending_keywords,
    "recent":   section_recent,
}


def main():
    args = sys.argv[1:]

    if "--section" in args:
        idx = args.index("--section")
        name = args[idx + 1] if idx + 1 < len(args) else ""
        fn = SECTIONS.get(name)
        if not fn:
            print(f"Unknown section '{name}'. Choose from: {', '.join(SECTIONS)}")
            sys.exit(1)
        fn()
        print()
        return

    # Run all sections
    print("\n" + "=" * 55)
    print("  NEWS PIPELINE — ANALYTICS REPORT   (Phase 5)")
    print("=" * 55)

    for fn in SECTIONS.values():
        fn()

    print("\n" + "=" * 55 + "\n")


if __name__ == "__main__":
    main()
