"""
Phase 7 — Kafka Consumer.

Subscribes to the 'news-articles' topic, runs the Phase 3 transformer
on each message, and inserts clean articles into PostgreSQL.

Runs continuously until Ctrl+C.

Usage:
    python src/consumer/news_consumer.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from etl.transformer import transform
from database.connection import test_connection
from database.schema import init_schema
from database.repository import bulk_insert_articles

load_dotenv()

TOPIC = "news-articles"
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
GROUP_ID = "news-consumer-group"


def build_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=GROUP_ID,
        value_deserializer=lambda b: json.loads(b.decode("utf-8")),
        auto_offset_reset="earliest",   # start from oldest unread message
        enable_auto_commit=True,
        auto_commit_interval_ms=5000,
        consumer_timeout_ms=-1,          # block forever until messages arrive
    )


def process_message(message_value: dict) -> dict | None:
    """
    Extract the raw article from a Kafka message, run it through
    the ETL transformer, and return the single clean record (or None).
    """
    raw_article = message_value.get("article", {})
    meta = message_value.get("meta", {})

    # Attach endpoint so transformer provenance fields are populated
    raw_article["_source_file"] = "kafka"
    raw_article["_endpoint"] = meta.get("endpoint", "unknown")

    clean_articles, _ = transform([raw_article])
    return clean_articles[0] if clean_articles else None


def main():
    print("=" * 55)
    print("  News Consumer — Phase 7")
    print("=" * 55 + "\n")

    print("[1/3] Checking database connection...")
    if not test_connection():
        print("  Cannot reach PostgreSQL. Is Docker running?")
        sys.exit(1)
    print("  Connected.\n")

    print("[2/3] Initialising schema...")
    init_schema()
    print()

    print(f"[3/3] Connecting to Kafka at {KAFKA_BROKER}...")
    try:
        consumer = build_consumer()
    except NoBrokersAvailable:
        print("  No Kafka broker found. Is Docker running?")
        print("  Run: docker-compose up -d")
        sys.exit(1)

    print(f"  Subscribed to topic: '{TOPIC}'")
    print("  Waiting for messages... (Ctrl+C to stop)\n")

    stats = {"received": 0, "inserted": 0, "skipped": 0, "errors": 0}

    try:
        for message in consumer:
            stats["received"] += 1

            try:
                clean = process_message(message.value)
                if clean is None:
                    stats["skipped"] += 1
                    continue

                report = bulk_insert_articles([clean])
                stats["inserted"] += report["inserted"]
                stats["skipped"] += report["skipped"]
                stats["errors"] += report["errors"]

                now = datetime.now(timezone.utc).strftime("%H:%M:%S")
                title = (clean.get("title") or "")[:55]
                status = "INSERT" if report["inserted"] else "SKIP  "
                print(f"  [{now}] {status}  {title}")

            except Exception as e:
                stats["errors"] += 1
                print(f"  Error processing message: {e}")

    except KeyboardInterrupt:
        print("\nConsumer stopped.")

    finally:
        consumer.close()
        print("\n── Session Stats ──────────────────────")
        print(f"  Messages received : {stats['received']}")
        print(f"  Inserted          : {stats['inserted']}")
        print(f"  Skipped (dup/inv) : {stats['skipped']}")
        print(f"  Errors            : {stats['errors']}")


if __name__ == "__main__":
    main()
