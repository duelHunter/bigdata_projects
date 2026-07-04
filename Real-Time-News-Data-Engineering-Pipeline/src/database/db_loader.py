"""
Loads cleaned articles from data/processed/ into PostgreSQL.

Usage:
    python src/database/db_loader.py              # load today's processed data
    python src/database/db_loader.py 2026-06-30   # load a specific date
    python src/database/db_loader.py --all        # load all processed data
"""

import sys
from datetime import date
from pathlib import Path

# Make sibling packages importable when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.connection import test_connection
from database.schema import init_schema
from database.repository import bulk_insert_articles, get_article_count
from etl.loader import load_processed_for_date

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


def load_all_processed() -> list[dict]:
    """Read every processed file from the data lake."""
    articles = []
    if not PROCESSED_DIR.exists():
        return articles
    import json
    for filepath in sorted(PROCESSED_DIR.rglob("*.json")):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        articles.extend(data.get("articles", []))
    return articles


def run(target_date: date | None = None, all_data: bool = False):
    print("\n" + "=" * 55)
    print("  DB Loader — Phase 4")
    print("=" * 55 + "\n")

    print("[1/4] Testing database connection...")
    if not test_connection():
        print("  Cannot reach PostgreSQL. Is Docker running?")
        print("  Run: docker-compose up -d")
        sys.exit(1)
    print("  Connected.\n")

    print("[2/4] Initialising schema...")
    init_schema()
    print()

    print("[3/4] Reading processed articles...")
    if all_data:
        articles = load_all_processed()
        print(f"  Loaded {len(articles)} articles from entire processed lake")
    else:
        target = target_date or date.today()
        articles = load_processed_for_date(target)
        print(f"  Loaded {len(articles)} articles for {target}")

    if not articles:
        print("  Nothing to load. Run the ETL pipeline first.")
        return
    print()

    print("[4/4] Inserting into PostgreSQL...")
    report = bulk_insert_articles(articles)
    print(f"  Inserted : {report['inserted']}")
    print(f"  Skipped  : {report['skipped']} (already in DB)")
    print(f"  Errors   : {report['errors']}")

    total = get_article_count()
    print(f"\n  Total articles in DB : {total}")
    print("\nLoad complete.")


def main():
    args = sys.argv[1:]

    if "--all" in args:
        run(all_data=True)
        return

    if args:
        try:
            target_date = date.fromisoformat(args[0])
        except ValueError:
            print(f"Invalid date '{args[0]}'. Use YYYY-MM-DD.")
            sys.exit(1)
        run(target_date=target_date)
    else:
        run()


if __name__ == "__main__":
    main()
