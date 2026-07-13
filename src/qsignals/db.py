"""DuckDB storage layer.

All market data lands here append-only: rows are never updated or deleted,
so a bad ingest run can't silently rewrite history. Re-running an ingest for
a (ticker, date) range that already exists is a no-op thanks to the anti-join
in insert_bars.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS bars (
    ticker      VARCHAR NOT NULL,
    date        DATE    NOT NULL,
    open        DOUBLE,
    high        DOUBLE,
    low         DOUBLE,
    close       DOUBLE,
    adj_close   DOUBLE,
    volume      BIGINT,
    source      VARCHAR NOT NULL,
    ingested_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS ingest_log (
    run_at   TIMESTAMP NOT NULL DEFAULT current_timestamp,
    ticker   VARCHAR NOT NULL,
    source   VARCHAR NOT NULL,
    rows_new BIGINT  NOT NULL,
    note     VARCHAR
);
"""

BAR_COLUMNS = ["ticker", "date", "open", "high", "low", "close", "adj_close", "volume", "source"]


def connect(path: str | Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(path))
    con.execute(SCHEMA)
    return con


def insert_bars(con: duckdb.DuckDBPyConnection, frame: pd.DataFrame) -> int:
    """Append bars, skipping (ticker, date) pairs already stored.

    Returns the number of rows actually inserted.
    """
    missing = [c for c in BAR_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"bars frame missing columns: {missing}")
    if frame.empty:
        return 0

    staged = frame[BAR_COLUMNS]  # noqa: F841 - registered below by name
    con.register("staged", staged)
    before = con.execute("SELECT count(*) FROM bars").fetchone()[0]
    con.execute(
        """
        INSERT INTO bars (ticker, date, open, high, low, close, adj_close, volume, source)
        SELECT s.* FROM staged s
        ANTI JOIN bars b ON b.ticker = s.ticker AND b.date = s.date
        """
    )
    after = con.execute("SELECT count(*) FROM bars").fetchone()[0]
    con.unregister("staged")
    return after - before


def log_ingest(
    con: duckdb.DuckDBPyConnection, ticker: str, source: str, rows_new: int, note: str = ""
) -> None:
    con.execute(
        "INSERT INTO ingest_log (ticker, source, rows_new, note) VALUES (?, ?, ?, ?)",
        [ticker, source, rows_new, note],
    )


def latest_date(con: duckdb.DuckDBPyConnection, ticker: str) -> pd.Timestamp | None:
    row = con.execute("SELECT max(date) FROM bars WHERE ticker = ?", [ticker]).fetchone()
    return pd.Timestamp(row[0]) if row and row[0] is not None else None
