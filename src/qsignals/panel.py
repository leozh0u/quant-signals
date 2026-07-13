"""Load bars out of DuckDB as wide date-by-ticker panels."""

from __future__ import annotations

import duckdb
import pandas as pd


def adj_close_panel(
    con: duckdb.DuckDBPyConnection, tickers: list[str] | None = None
) -> pd.DataFrame:
    """Dividend-and-split-adjusted closes, one column per ticker, DatetimeIndex.

    Rows are trading dates; a ticker that wasn't listed yet is NaN, which
    downstream code must treat as 'not in the universe that day' rather than
    filling. Forward-filling here would manufacture stale prices.
    """
    query = "SELECT date, ticker, adj_close FROM bars"
    params: list = []
    if tickers:
        query += f" WHERE ticker IN ({','.join('?' * len(tickers))})"
        params = list(tickers)
    frame = con.execute(query, params).df()
    panel = frame.pivot(index="date", columns="ticker", values="adj_close").sort_index()
    panel.index = pd.to_datetime(panel.index)
    return panel
