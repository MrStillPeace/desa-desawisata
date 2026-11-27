"""Manajemen koneksi PostgreSQL menggunakan psycopg2 dan RealDictCursor."""

from contextlib import contextmanager
import os
from typing import Iterator

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DATABASE_URL = "postgresql://app:app@localhost:5432/desawisata"


def get_database_url() -> str:
    """Mengambil DATABASE_URL dari environment variable atau file .env."""
    load_dotenv()
    return os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL


@contextmanager
def get_db_cursor(commit: bool = False) -> Iterator[RealDictCursor]:
    """
    Context manager untuk membuka koneksi dan cursor PostgreSQL (RealDictCursor).

    Args:
        commit: Jika True, lakukan commit saat blok selesai tanpa error.
                Jika False, lakukan rollback agar tidak meninggalkan transaksi terbuka.
    """
    conn = psycopg2.connect(get_database_url(), cursor_factory=RealDictCursor)
    try:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()
        else:
            conn.rollback()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def check_db_health() -> bool:
    """Memeriksa kesehatan koneksi PostgreSQL dengan query sederhana SELECT 1."""
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 AS ok;")
            row = cur.fetchone()
            return bool(row and row.get("ok") == 1)
    except Exception:
        return False
