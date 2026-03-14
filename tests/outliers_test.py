"""
Tests for the outliers module.

Uses the sample dataset from the README to verify that the correct weeks
are identified as outliers.

Expected outlier weeks from the README sample:
    Year  WeekNumber  VoteCount
    2022  0           1
    2022  1           3
    2022  2           3
    2022  5           1
    2022  6           1
    2022  8           1
"""

import json
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

from equalexperts_dataeng_exercise.ingest import create_schema_and_table, ingest_file
from equalexperts_dataeng_exercise.outliers import (
    CREATE_VIEW_SQL,
    create_outlier_view,
    detect_outliers,
    print_outlier_weeks,
)


@pytest.fixture
def conn_with_sample_data(tmp_path):
    """
    Returns a fresh in-memory DuckDB connection pre-loaded with the
    sample dataset from the README.
    """
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

    connection = duckdb.connect(":memory:")
    create_schema_and_table(connection)
    ingest_file(connection, file_path)
    connection.execute(CREATE_VIEW_SQL)
    yield connection
    connection.close()


# ── Unit tests ────────────────────────────────────────────────────────────────

def test_outlier_view_exists(conn_with_sample_data):
    """The outlier_weeks view should exist in blog_analysis schema."""
    result = conn_with_sample_data.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'blog_analysis' AND table_name = 'outlier_weeks'
    """).fetchall()
    assert len(result) == 1


def test_outlier_weeks_match_expected(conn_with_sample_data):
    """The outlier weeks should exactly match the sample output in the README."""
    rows = conn_with_sample_data.execute(
        "SELECT Year, WeekNumber, VoteCount FROM blog_analysis.outlier_weeks ORDER BY Year, WeekNumber"
    ).fetchall()
    expected = [
        (2022, 0, 1),
        (2022, 1, 3),
        (2022, 2, 3),
        (2022, 5, 1),
        (2022, 6, 1),
        (2022, 8, 1),
    ]
    assert rows == expected


def test_outlier_weeks_sorted_by_year_and_week(conn_with_sample_data):
    """Results must be ordered by Year then WeekNumber ascending."""
    rows = conn_with_sample_data.execute(
        "SELECT Year, WeekNumber FROM blog_analysis.outlier_weeks"
    ).fetchall()
    assert rows == sorted(rows)


def test_non_outlier_weeks_excluded(conn_with_sample_data):
    """Weeks with 2 votes (the mean) should NOT be outliers."""
    rows = conn_with_sample_data.execute(
        "SELECT WeekNumber FROM blog_analysis.outlier_weeks WHERE Year = 2022"
    ).fetchall()
    week_numbers = [r[0] for r in rows]
    assert 3 not in week_numbers
    assert 4 not in week_numbers


def test_outlier_count(conn_with_sample_data):
    """There should be exactly 6 outlier weeks for the sample data."""
    count = conn_with_sample_data.execute(
        "SELECT COUNT(*) FROM blog_analysis.outlier_weeks"
    ).fetchone()[0]
    assert count == 6


def test_create_outlier_view_function(conn_with_sample_data):
    """create_outlier_view() should recreate the view without error."""
    create_outlier_view(conn_with_sample_data)
    count = conn_with_sample_data.execute(
        "SELECT COUNT(*) FROM blog_analysis.outlier_weeks"
    ).fetchone()[0]
    assert count == 6


def test_print_outlier_weeks(conn_with_sample_data, capsys):
    """print_outlier_weeks() should print a table with correct content."""
    print_outlier_weeks(conn_with_sample_data)
    captured = capsys.readouterr()
    assert "2022" in captured.out
    assert "Year" in captured.out
    assert "WeekNumber" in captured.out
    assert "VoteCount" in captured.out


def test_view_is_replaced_on_rerun(conn_with_sample_data):
    """Running create_outlier_view twice should not raise an error (CREATE OR REPLACE)."""
    create_outlier_view(conn_with_sample_data)
    create_outlier_view(conn_with_sample_data)
    count = conn_with_sample_data.execute(
        "SELECT COUNT(*) FROM blog_analysis.outlier_weeks"
    ).fetchone()[0]
    assert count == 6


# ── Integration tests ─────────────────────────────────────────────────────────

def test_detect_outliers_function(tmp_path, monkeypatch):
    """
    detect_outliers() should create the view and print results.
    Covers the detect_outliers() function in outliers.py.
    """
    # First ingest sample data into a real warehouse.db in tmp_path
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

    monkeypatch.chdir(tmp_path)
    conn = duckdb.connect(str(tmp_path / "warehouse.db"))
    create_schema_and_table(conn)
    ingest_file(conn, file_path)
    conn.close()

    # Now run detect_outliers() — it opens warehouse.db itself
    detect_outliers()

    conn = duckdb.connect(str(tmp_path / "warehouse.db"))
    count = conn.execute("SELECT COUNT(*) FROM blog_analysis.outlier_weeks").fetchone()[0]
    conn.close()
    assert count == 6


def test_outliers_main_module(tmp_path, monkeypatch):
    """
    Running outliers as __main__ via subprocess should work correctly.
    Covers the __main__ block in outliers.py.
    """
    records = [
        {"Id": "1",  "PostId": "1",  "VoteTypeId": "2", "CreationDate": "2022-01-02T00:00:00.000"},
        {"Id": "2",  "PostId": "1",  "VoteTypeId": "2", "CreationDate": "2022-01-09T00:00:00.000"},
        {"Id": "4",  "PostId": "1",  "VoteTypeId": "2", "CreationDate": "2022-01-09T00:00:00.000"},
        {"Id": "9",  "PostId": "2",  "VoteTypeId": "2", "CreationDate": "2022-01-23T00:00:00.000"},
        {"Id": "10", "PostId": "2",  "VoteTypeId": "2", "CreationDate": "2022-01-23T00:00:00.000"},
        {"Id": "13", "PostId": "8",  "VoteTypeId": "2", "CreationDate": "2022-02-06T00:00:00.000"},
    ]
    file_path = tmp_path / "votes.jsonl"
    with open(file_path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

    # Set up warehouse.db first
    conn = duckdb.connect(str(tmp_path / "warehouse.db"))
    create_schema_and_table(conn)
    ingest_file(conn, file_path)
    conn.close()

    result = subprocess.run(
        [sys.executable, "-m", "equalexperts_dataeng_exercise.outliers"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert result.returncode == 0
    assert "Year" in result.stdout