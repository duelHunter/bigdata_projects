"""
Phase 7 — Kafka Producer.

Polls NewsAPI on a configurable interval and publishes each article
as an individual JSON message to the 'news-articles' Kafka topic.

Usage:
    python src/producer/news_producer.py              # poll every 15 min
    python src/producer/news_producer.py --interval 5 # poll every 5 min
    python src/producer/news_producer.py --once        # single run then exit
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# Make sibling packages importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collector.news_collector import fetch_top_headlines, fetch_everything, get_api_key

load_dotenv()

TOPIC = "news-articles"
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
DEFAULT_INTERVAL_MINUTES = 15


def build_producer() -> KafkaProducer:
    """Create a KafkaProducer with JSON serialisation."""
    return KafkaProducer(
        bootstrap_servers=[KAFKA_BROKER],
        value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",           # wait for broker acknowledgement
        retries=3,
    )


def publish_articles(producer: KafkaProducer, articles: list[dict], endpoint: str) -> int:
    """
    Send each article as a separate Kafka message.
    The message key is the article URL so Kafka can partition by source.
    Returns the number of messages published.
    """
    published = 0
    for article in articles:
        url = article.get("url")
        if not url:
            continue

        message = {
            "article": article,
            "meta": {
                "endpoint": endpoint,
                "produced_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        producer.send(TOPIC, key=url, value=message)
        published += 1

    producer.flush()  # block until all messages are delivered
    return published


def run_once(producer: KafkaProducer, api_key: str):
    """Fetch from both endpoints and publish to Kafka."""
    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{now}] Fetching from NewsAPI...")

    total = 0

    headlines = fetch_top_headlines(api_key)
    articles = headlines.get("articles", [])
    count = publish_articles(producer, articles, endpoint="top-headlines")
    print(f"  top-headlines  → {count} messages published")
    total += count

    everything = fetch_everything(api_key, query="technology")
    articles = everything.get("articles", [])
    count = publish_articles(producer, articles, endpoint="everything")
    print(f"  everything     → {count} messages published")
    total += count

    print(f"  Total published: {total}")


def main():
    args = sys.argv[1:]
    run_once_flag = "--once" in args

    interval_minutes = DEFAULT_INTERVAL_MINUTES
    if "--interval" in args:
        idx = args.index("--interval")
        interval_minutes = int(args[idx + 1])

    api_key = get_api_key()

    print(f"Connecting to Kafka at {KAFKA_BROKER}...")
    try:
        producer = build_producer()
    except NoBrokersAvailable:
        print("  No Kafka broker found. Is Docker running?")
        print("  Run: docker-compose up -d")
        sys.exit(1)

    print(f"Connected. Publishing to topic: '{TOPIC}'")

    if run_once_flag:
        run_once(producer, api_key)
        producer.close()
        return

    print(f"Polling every {interval_minutes} minute(s). Press Ctrl+C to stop.\n")
    try:
        while True:
            run_once(producer, api_key)
            print(f"  Sleeping {interval_minutes} min...")
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("\nProducer stopped.")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
