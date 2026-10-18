
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).parent / "leadbot.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                budget TEXT NOT NULL,
                district TEXT NOT NULL,
                preferences TEXT NOT NULL,
                rental_term TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_application(
    user_id,
    budget,
    district,
    preferences,
    rental_term,
):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO applications (
                user_id,
                budget,
                district,
                preferences,
                rental_term
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                budget,
                district,
                preferences,
                rental_term,
            ),
        )

def get_applications(limit=10):
    """Возвращает последние заявки из базы."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT id, user_id, budget, district, preferences,
                   rental_term, created_at
            FROM applications
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return rows