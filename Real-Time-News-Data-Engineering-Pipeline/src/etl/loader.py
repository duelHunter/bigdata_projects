import json
from datetime import datetime, date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def save_processed(articles: list[dict], label: str = "etl", run_date: date | None = None) -> Path:
    """
    Save cleaned articles to data/processed/YYYY/MM/DD/<label>_HHMMSS.json
    Returns the path of the saved file.
    """
    now = datetime.now()
    target_date = run_date or now.date()

    date_path = (
        PROCESSED_DIR
        / str(target_date.year)
        / f"{target_date.month:02d}"
        / f"{target_date.day:02d}"
    )
    date_path.mkdir(parents=True, exist_ok=True)

    filename = f"{label}_{now.strftime('%H%M%S')}.json"
    filepath = date_path / filename

    output = {
        "metadata": {
            "label": label,
            "processed_at": now.isoformat(),
            "article_count": len(articles),
        },
        "articles": articles,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return filepath


def load_processed_for_date(target_date: date) -> list[dict]:
    """Load all cleaned articles that were saved on a given date."""
    date_path = (
        PROCESSED_DIR
        / str(target_date.year)
        / f"{target_date.month:02d}"
        / f"{target_date.day:02d}"
    )

    if not date_path.exists():
        return []

    all_articles = []
    for filepath in sorted(date_path.glob("*.json")):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        all_articles.extend(data.get("articles", []))

    return all_articles
