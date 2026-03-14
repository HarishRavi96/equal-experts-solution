"""
Ingestion script for vote data.

Usage:
    python -m equalexperts_dataeng_exercise.ingest <path_to_votes.jsonl>

Strategy:
- We create a schema `blog_analysis` and a table `votes` if they don't exist.
- We use INSERT OR IGNORE (via a UNIQUE constraint on the primary key `Id`)
  to ensure duplicate records are never stored, even if ingestion is run multiple times.
- DuckDB's read_json_auto is used to load the JSONL file efficiently in bulk,
  which is the idiomatic OLAP warehouse approach (bulk load, not row-by-row inserts).
"""

import sys
from pathlib import Path

from equalexperts_dataeng_exercise.db import get_connection


def create_schema_and_table(conn) -> None:
    """Create the blog_analysis schema and votes table if they don't already exist."""
    conn.execute("CREATE SCHEMA IF NOT EXISTS blog_analysis")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blog_analysis.votes (
            Id          INTEGER PRIMARY KEY,
            PostId      INTEGER NOT NULL,
            VoteTypeId  INTEGER NOT NULL,
            CreationDate TIMESTAMP NOT NULL
        )
    """)


def ingest_file(conn, path: Path) -> None:
    """
    Load votes from a JSONL file into the votes table.

    We use INSERT OR IGNORE so that re-running ingestion on the same file
    (or a file containing previously seen records) is safe and idempotent.
    The PRIMARY KEY on Id is the deduplication mechanism.
    Empty files are silently skipped.
    """
    if path.stat().st_size == 0:
        return

    conn.execute(f"""
        INSERT OR IGNORE INTO blog_analysis.votes
        SELECT
            CAST(Id AS INTEGER)          AS Id,
            CAST(PostId AS INTEGER)      AS PostId,
            CAST(VoteTypeId AS INTEGER)  AS VoteTypeId,
            CAST(CreationDate AS TIMESTAMP) AS CreationDate
        FROM read_json_auto('{path}')
    """)


def ingest(path: Path) -> None:
    conn = get_connection()
    create_schema_and_table(conn)
    ingest_file(conn, path)
    conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m equalexperts_dataeng_exercise.ingest <path_to_votes.jsonl>")
        sys.exit(1)

    data_path = Path(sys.argv[1])
    if not data_path.exists():
        print(f"Error: File not found: {data_path}")
        sys.exit(1)

    ingest(data_path)
    print(f"Ingestion complete: {data_path}")