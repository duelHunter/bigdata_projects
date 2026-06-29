import os
import json
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://newsapi.org/v2"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def get_api_key():
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        print("ERROR: NEWS_API_KEY not found in environment variables.")
        print("Create a .env file with: NEWS_API_KEY=your_key_here")
        sys.exit(1)
    return api_key


def fetch_top_headlines(api_key, country="us", page_size=100):
    url = f"{BASE_URL}/top-headlines"
    params = {
        "apiKey": api_key,
        "country": country,
        "pageSize": page_size,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_everything(api_key, query="technology", page_size=100, sort_by="publishedAt"):
    url = f"{BASE_URL}/everything"
    params = {
        "apiKey": api_key,
        "q": query,
        "pageSize": page_size,
        "sortBy": sort_by,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def save_raw_json(data, endpoint_name):
    now = datetime.now()
    date_path = RAW_DATA_DIR / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
    date_path.mkdir(parents=True, exist_ok=True)

    filename = f"{endpoint_name}_{now.strftime('%H%M%S')}.json"
    filepath = date_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def main():
    api_key = get_api_key()

    print("Fetching top headlines...")
    headlines = fetch_top_headlines(api_key)
    path = save_raw_json(headlines, "headlines")
    print(f"  Saved {headlines.get('totalResults', 0)} results -> {path}")

    print("Fetching everything (technology)...")
    everything = fetch_everything(api_key, query="technology")
    path = save_raw_json(everything, "everything")
    print(f"  Saved {everything.get('totalResults', 0)} results -> {path}")

    print("Done.")


if __name__ == "__main__":
    main()
