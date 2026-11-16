import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import UUID


class FeedbackStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    answer_id TEXT PRIMARY KEY,
                    useful INTEGER NOT NULL CHECK (useful IN (0, 1)),
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save(self, answer_id: UUID, useful: bool) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                """
                INSERT INTO feedback (answer_id, useful) VALUES (?, ?)
                ON CONFLICT (answer_id) DO UPDATE SET
                    useful = excluded.useful,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (str(answer_id), int(useful)),
            )
