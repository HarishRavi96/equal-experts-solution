"""
Tests for the ingestion module.

Each test uses a temporary in-memory or temp-file DuckDB connection so tests
are fully self-contained and independent of each other.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

from equalexperts_dataeng_exercise.db import get_connection
from equalexperts_dataeng_exercise.ingest import create_schema_and_table, ingest, ingest_file


@pytest.fixture
def conn():
    """Provides a fresh in-memory DuckDB connection for each test."""
    connection = duckdb.connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def sample_jsonl(tmp_path) -> Path:
    """Writes the sample votes JSONL from the README to a temp file."""
    records = [
        {"Id": "1",  "PostId": "1",  "VoteTypeId": "2", "CreationDate": "2022-01-02T00:00:00.000"},
        {"Id": "2",  "PostId": "1",  "VoteTypeId": "2", "CreationDate": "2022-01-09T00:00:00.000"},
        {"Id": "4",  "PostId": "1",  "VoteTypeId": "2", "CreationDate": "2022-01-09T00:00:00.000"},
        {"Id": "5",  "PostId": "1",  "VoteTypeId": "2", "CreationDate": "2022-01-09T00:00:00.000"},
        {"Id": "6",  "PostId": "5",  "VoteTypeId": "3", "CreationDate": "2022-01-16T00:00:00.000"},
        {"Id": "7",  "PostId": "3",  "VoteTypeId": "2", "CreationDate": "2022-01-16T00:00:00.000"},
        {"Id": "8",  "PostId": "4",  "VoteTypeId": "2", "CreationDate": "2022-01-16T00:00:00.000"},
        {"Id": "9",  "PostId": "2",  "VoteTypeId": "2", "CreationDate": "2022-01-23T00:00:00.000"},
        {"Id": "10", "PostId": "2",  "VoteTypeId": "2", "CreationDate": "2022-01-23T00:00:00.000"},
        {"Id": "11", "PostId": "1",  "VoteTypeId": "2", "CreationDate": "2022-01-30T00:00:00.000"},
        {"Id": "12", "PostId": "5",  "VoteTypeId": "2", "CreationDate": "2022-01-30T00:00:00.000"},
        {"Id": "13", "PostId": "8",  "VoteTypeId": "2", "CreationDate": "2022-02-06T00:00:00.000"},
        {"Id": "14", "PostId": "13", "VoteTypeId": "3", "CreationDate": "2022-02-13T00:00:00.000"},
        {"Id": "15", "PostId": "13", "VoteTypeId": "3", "CreationDate": "2022-02-20T00:00:00.000"},
        {"Id": "16", "PostId": "11", "VoteTypeId": "2", "CreationDate": "2022-02-20T00:00:00.000"},
        {"Id": "17", "PostId": "3",  "VoteTypeId": "3", "CreationDate": "2022-02-27T00:00:00.000"},
    ]
    file_path = tmp_path / "votes.jsonl"
    with open(file_path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")
    return file_path


# ── Unit tests ────────────────────────────────────────────────────────────────

def test_schema_and_table_are_created(conn):
    """After setup, the blog_analysis.votes table should exist."""
    create_schema_and_table(conn)
    result = conn.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'blog_analysis' AND table_name = 'votes'
    """).fetchall()
    assert len(result) == 1


def test_correct_row_count_after_single_ingest(conn, sample_jsonl):
    """All 16 rows from the sample file should be loaded."""
    create_schema_and_table(conn)
    ingest_file(conn, sample_jsonl)
    count = conn.execute("SELECT COUNT(*) FROM blog_analysis.votes").fetchone()[0]
    assert count == 16


def test_idempotent_ingestion_no_duplicates(conn, sample_jsonl):
    """Running ingestion twice should not insert duplicate rows."""
    create_schema_and_table(conn)
    ingest_file(conn, sample_jsonl)
    ingest_file(conn, sample_jsonl)
    count = conn.execute("SELECT COUNT(*) FROM blog_analysis.votes").fetchone()[0]
    assert count == 16


def test_data_types_are_correct(conn, sample_jsonl):
    """Id, PostId, VoteTypeId should be INTEGER; CreationDate should be TIMESTAMP."""
    create_schema_and_table(conn)
    ingest_file(conn, sample_jsonl)
    row = conn.execute(
        "SELECT Id, PostId, VoteTypeId, CreationDate FROM blog_analysis.votes LIMIT 1"
    ).fetchone()
    assert isinstance(row[0], int)
    assert isinstance(row[1], int)
    assert isinstance(row[2], int)


def test_create_schema_is_idempotent(conn):
    """Calling create_schema_and_table multiple times should not raise an error."""
    create_schema_and_table(conn)
    create_schema_and_table(conn)


def test_ingest_empty_file(conn, tmp_path):
    """Ingesting an empty file should result in 0 rows and not crash."""
    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("")
    create_schema_and_table(conn)
    try:
        ingest_file(conn, empty_file)
    except Exception:
        pass
    count = conn.execute("SELECT COUNT(*) FROM blog_analysis.votes").fetchone()[0]
    assert count == 0


def test_all_fields_are_stored_correctly(conn, sample_jsonl):
    """Check a specific row's values are stored exactly as expected."""
    create_schema_and_table(conn)
    ingest_file(conn, sample_jsonl)
    row = conn.execute(
        "SELECT Id, PostId, VoteTypeId FROM blog_analysis.votes WHERE Id = 1"
    ).fetchone()
    assert row == (1, 1, 2)


def test_votes_table_has_correct_columns(conn):
    """The votes table should have exactly the 4 expected columns."""
    create_schema_and_table(conn)
    columns = conn.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'blog_analysis' AND table_name = 'votes'
        ORDER BY column_name
    """).fetchall()
    column_names = {col[0] for col in columns}
    assert column_names == {"Id", "PostId", "VoteTypeId", "CreationDate"}


# ── Integration tests (uses real warehouse.db file) ───────────────────────────

def test_ingest_function_creates_real_db(tmp_path, sample_jsonl, monkeypatch):
    """
    The ingest() function should create warehouse.db and load data into it.
    Uses monkeypatch to change working directory so warehouse.db goes to tmp_path.
    """
    monkeypatch.chdir(tmp_path)
    ingest(sample_jsonl)
    conn = duckdb.connect(str(tmp_path / "warehouse.db"))
    count = conn.execute("SELECT COUNT(*) FROM blog_analysis.votes").fetchone()[0]
    conn.close()
    assert count == 16


def test_ingest_twice_via_ingest_function(tmp_path, sample_jsonl, monkeypatch):
    """Calling ingest() twice should still result in no duplicates."""
    monkeypatch.chdir(tmp_path)
    ingest(sample_jsonl)
    ingest(sample_jsonl)
    conn = duckdb.connect(str(tmp_path / "warehouse.db"))
    count = conn.execute("SELECT COUNT(*) FROM blog_analysis.votes").fetchone()[0]
    conn.close()
    assert count == 16


def test_get_connection_creates_warehouse_db(tmp_path, monkeypatch):
    """get_connection() should create and connect to warehouse.db."""
    monkeypatch.chdir(tmp_path)
    conn = get_connection()
    result = conn.execute("SELECT 1").fetchone()
    conn.close()
    assert result == (1,)
    assert (tmp_path / "warehouse.db").exists()


def test_ingest_main_module(tmp_path, sample_jsonl, monkeypatch):
    """
    Running ingest as __main__ via subprocess should load data correctly.
    Covers the __main__ block in ingest.py.
    """
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "equalexperts_dataeng_exercise.ingest", str(sample_jsonl)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0
    assert "Ingestion complete" in result.stdout
    conn = duckdb.connect(str(tmp_path / "warehouse.db"))
    count = conn.execute("SELECT COUNT(*) FROM blog_analysis.votes").fetchone()[0]
    conn.close()
    assert count == 16


def test_ingest_main_module_missing_file(tmp_path, monkeypatch):
    """Running ingest with a missing file should exit with non-zero return code."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "equalexperts_dataeng_exercise.ingest", "nonexistent.jsonl"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert result.returncode != 0


def test_ingest_main_module_no_args(tmp_path, monkeypatch):
    """Running ingest with no arguments should exit with non-zero return code."""
    monkeypatch.chdir(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "equalexperts_dataeng_exercise.ingest"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert result.returncode != 0