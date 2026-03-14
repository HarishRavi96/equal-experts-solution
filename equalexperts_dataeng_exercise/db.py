import duckdb


def get_connection() -> duckdb.DuckDBPyConnection:
    """Returns a connection to the DuckDB warehouse."""
    return duckdb.connect("warehouse.db")