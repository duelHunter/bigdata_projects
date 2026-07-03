"""
ETL Pipeline orchestrator — Phase 3.

Usage:
    python src/etl/pipeline.py              # process today's raw data
    python src/etl/pipeline.py 2026-06-30  # process a specific date
    python src/etl/pipeline.py --all       # process entire data lake
"""

import sys
from datetime import date

from extractor import extract_for_date, extract_all
from transformer import transform
from loader import save_processed, load_processed_for_date


def run_for_date(target_date: date):
    print(f"\n{'='*55}")
    print(f"  ETL Pipeline — {target_date}")
    print(f"{'='*55}\n")

    # ── Extract ────────────────────────────────────────────────
    print("[1/3] Extract")
    raw_articles = extract_for_date(target_date)
    print(f"  Total extracted : {len(raw_articles)} articles\n")

    if not raw_articles:
        print("  Nothing to process. Run the collector first.")
        return

    # ── Transform ──────────────────────────────────────────────
    print("[2/3] Transform")
    clean_articles, report = transform(raw_articles)

    print(f"  Input           : {report['input_count']}")
    print(f"  Removed ([Removed] sentinel) : {report['removed_sentinel']}")
    print(f"  Missing required fields      : {report['missing_required']}")
    print(f"  Duplicates removed           : {report['duplicates_removed']}")
    print(f"  Output (clean)  : {report['output_count']}\n")

    # ── Load ───────────────────────────────────────────────────
    print("[3/3] Load")
    filepath = save_processed(clean_articles, label="etl", run_date=target_date)
    print(f"  Saved {len(clean_articles)} clean articles -> {filepath}\n")

    print("ETL complete.")


def run_all():
    print("\nRunning ETL over entire data lake...\n")
    raw_articles = extract_all()
    if not raw_articles:
        print("No raw data found.")
        return

    print(f"\nTotal extracted : {len(raw_articles)} articles")
    clean_articles, report = transform(raw_articles)

    print(f"Removed sentinels    : {report['removed_sentinel']}")
    print(f"Missing required     : {report['missing_required']}")
    print(f"Duplicates removed   : {report['duplicates_removed']}")
    print(f"Clean output         : {report['output_count']}")

    filepath = save_processed(clean_articles, label="etl_full")
    print(f"\nSaved -> {filepath}")


def main():
    args = sys.argv[1:]

    if "--all" in args:
        run_all()
        return

    if args:
        try:
            target_date = date.fromisoformat(args[0])
        except ValueError:
            print(f"Invalid date '{args[0]}'. Use YYYY-MM-DD format.")
            sys.exit(1)
    else:
        target_date = date.today()

    run_for_date(target_date)


if __name__ == "__main__":
    main()
