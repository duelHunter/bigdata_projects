import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def list_collection_dates():
    dates = []
    if not RAW_DATA_DIR.exists():
        return dates
    for year_dir in sorted(RAW_DATA_DIR.iterdir()):
        if not year_dir.is_dir():
            continue
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for day_dir in sorted(month_dir.iterdir()):
                if not day_dir.is_dir():
                    continue
                files = list(day_dir.glob("*.json"))
                dates.append({
                    "date": f"{year_dir.name}-{month_dir.name}-{day_dir.name}",
                    "file_count": len(files),
                    "path": str(day_dir),
                })
    return dates


def list_files_for_date(year, month, day):
    date_path = RAW_DATA_DIR / str(year) / f"{month:02d}" / f"{day:02d}"
    if not date_path.exists():
        return []
    results = []
    for filepath in sorted(date_path.glob("*.json")):
        size_kb = filepath.stat().st_size / 1024
        metadata = _read_metadata(filepath)
        results.append({
            "filename": filepath.name,
            "size_kb": round(size_kb, 1),
            "endpoint": metadata.get("endpoint", "unknown"),
            "article_count": metadata.get("article_count", 0),
            "collected_at": metadata.get("collected_at", "unknown"),
        })
    return results


def get_storage_summary():
    total_files = 0
    total_size_bytes = 0
    total_articles = 0
    dates = list_collection_dates()

    for date_info in dates:
        path = Path(date_info["path"])
        for filepath in path.glob("*.json"):
            total_files += 1
            total_size_bytes += filepath.stat().st_size
            metadata = _read_metadata(filepath)
            total_articles += metadata.get("article_count", 0)

    return {
        "total_collection_days": len(dates),
        "total_files": total_files,
        "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
        "total_articles": total_articles,
    }


def _read_metadata(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("metadata", {})
    except (json.JSONDecodeError, KeyError):
        return {}


def main():
    print("=== Data Lake Summary ===\n")

    summary = get_storage_summary()
    print(f"  Collection days : {summary['total_collection_days']}")
    print(f"  Total files     : {summary['total_files']}")
    print(f"  Total size      : {summary['total_size_mb']} MB")
    print(f"  Total articles  : {summary['total_articles']}")

    dates = list_collection_dates()
    if not dates:
        print("\n  No data collected yet. Run news_collector.py first.")
        return

    print("\n=== Collections by Date ===\n")
    for d in dates:
        print(f"  {d['date']}  ({d['file_count']} files)")
        files = list_files_for_date(
            int(d["date"][:4]),
            int(d["date"][5:7]),
            int(d["date"][8:10]),
        )
        for f in files:
            print(f"    - {f['filename']}  |  {f['article_count']} articles  |  {f['size_kb']} KB  |  {f['collected_at']}")


if __name__ == "__main__":
    main()
