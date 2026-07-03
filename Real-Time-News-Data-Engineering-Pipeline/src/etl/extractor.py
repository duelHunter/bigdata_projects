import json
from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def extract_from_file(filepath: Path) -> list[dict]:
    """Read one raw JSON file and return its list of articles."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Support both the Phase-2 envelope format and plain NewsAPI responses
    if "raw_response" in data:
        articles = data["raw_response"].get("articles", [])
        source_meta = data.get("metadata", {})
    else:
        articles = data.get("articles", [])
        source_meta = {}

    # Attach the source filename so transformations can trace each record
    for article in articles:
        article["_source_file"] = filepath.name
        article["_endpoint"] = source_meta.get("endpoint", "unknown")

    return articles


def extract_for_date(target_date: date) -> list[dict]:
    """Extract all articles from every raw file on a given date."""
    date_path = (
        RAW_DATA_DIR
        / str(target_date.year)
        / f"{target_date.month:02d}"
        / f"{target_date.day:02d}"
    )

    if not date_path.exists():
        print(f"  No raw data found for {target_date}")
        return []

    all_articles = []
    for filepath in sorted(date_path.glob("*.json")):
        articles = extract_from_file(filepath)
        print(f"  Extracted {len(articles)} articles from {filepath.name}")
        all_articles.extend(articles)

    return all_articles


def extract_all() -> list[dict]:
    """Extract every article from the entire raw data lake."""
    all_articles = []
    if not RAW_DATA_DIR.exists():
        return all_articles

    for year_dir in sorted(RAW_DATA_DIR.iterdir()):
        if not year_dir.is_dir():
            continue
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for day_dir in sorted(month_dir.iterdir()):
                if not day_dir.is_dir():
                    continue
                for filepath in sorted(day_dir.glob("*.json")):
                    articles = extract_from_file(filepath)
                    all_articles.extend(articles)

    return all_articles
