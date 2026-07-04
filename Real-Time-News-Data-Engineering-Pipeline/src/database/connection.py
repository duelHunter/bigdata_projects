import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


def _get_conn_params() -> dict:
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "dbname": os.getenv("DB_NAME", "newsdb"),
        "user": os.getenv("DB_USER", "newsuser"),
        "password": os.getenv("DB_PASSWORD", "newspassword"),
    }


@contextmanager
def get_connection():
    """Yield a psycopg2 connection, auto-committing on success and rolling back on error."""
    conn = psycopg2.connect(**_get_conn_params())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor():
    """Yield a DictCursor, wrapping the connection lifecycle."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur


def test_connection() -> bool:
    try:
        with get_cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
