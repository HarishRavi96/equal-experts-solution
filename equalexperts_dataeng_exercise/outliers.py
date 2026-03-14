"""
Outlier detection script.

Usage:
    python -m equalexperts_dataeng_exercise.outliers

This script:
1. Creates (or replaces) a view `blog_analysis.outlier_weeks`.
2. Prints the contents of that view to the terminal.

Outlier rule:
    A week is an outlier when its vote count deviates from the overall
    mean votes-per-week by more than 20%, i.e.:
        |1 - (week_votes / mean_votes)| > 0.2

ISO week numbering note:
    DuckDB's isoyear() and isoweek() functions are used so that week boundaries
    are consistent and unambiguous. week() starts on Sunday and can give
    week 0; ISO weeks always start Monday and run 1-53.
    The sample data in the README uses week numbers 0-8 (Sunday-based),
    so we use strftime('%W', ...) which gives Sunday-based week numbers
    matching the expected output exactly.
"""

from equalexperts_dataeng_exercise.db import get_connection

CREATE_VIEW_SQL = """
CREATE OR REPLACE VIEW blog_analysis.outlier_weeks AS
WITH weekly_votes AS (
    SELECT
        YEAR(CreationDate)                        AS Year,
        CAST(strftime(CreationDate, '%W') AS INTEGER) AS WeekNumber,
        COUNT(*)                                  AS VoteCount
    FROM blog_analysis.votes
    GROUP BY Year, WeekNumber
),
mean_votes AS (
    SELECT AVG(VoteCount) AS AvgVotes
    FROM weekly_votes
)
SELECT
    w.Year,
    w.WeekNumber,
    w.VoteCount
FROM weekly_votes w, mean_votes m
WHERE ABS(1.0 - (w.VoteCount * 1.0 / m.AvgVotes)) > 0.2
ORDER BY w.Year, w.WeekNumber
"""


def create_outlier_view(conn) -> None:
    conn.execute(CREATE_VIEW_SQL)


def print_outlier_weeks(conn) -> None:
    result = conn.execute("SELECT * FROM blog_analysis.outlier_weeks")
    rows = result.fetchall()
    print(f"{'Year':<8} {'WeekNumber':<12} {'VoteCount':<10}")
    print("-" * 30)
    for row in rows:
        print(f"{row[0]:<8} {row[1]:<12} {row[2]:<10}")


def detect_outliers() -> None:
    conn = get_connection()
    create_outlier_view(conn)
    print_outlier_weeks(conn)
    conn.close()


if __name__ == "__main__":
    detect_outliers()