import sqlite3
from contextlib import contextmanager
from typing import Generator


# For FastAPI
# FastAPI needs a generator. This way we can use their dependency
# injection for a quick database transaction.
def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    connection = sqlite3.connect("db.db")
    cursor = connection.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
        connection.close()


# Now, anything else can be quickly managed by a quick
# Context manager, which FastAPI doesn't jive with - because
# they themselves wrap everything in one implicitly.
get_db_cursor_context = contextmanager(get_db_cursor)


def initialize_database():
    with get_db_cursor_context() as cursor:
        create_database_tables(cursor)


def create_database_tables(cursor: sqlite3.Cursor) -> None:
    # Cats
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS cat (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        breed TEXT,
        age INTEGER
    );
    """
    )
    # Owners
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS owner (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        address TEXT,
        cat_id INTEGER,
        FOREIGN KEY (cat_id) REFERENCES cat(id)
    );
    """
    )
