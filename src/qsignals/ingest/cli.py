"""Ingest runner: pull daily bars for the configured universe into DuckDB.

Usage:
    qs-ingest --db data/market.duckdb --universe universe.txt
    qs-ingest --db data/market.duckdb --tickers AAPL MSFT

Safe to re-run: already-stored (ticker, date) rows are skipped, and every
run is recorded in ingest_log either way.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

from qsignals import db
from qsignals.ingest import yahoo


def read_universe(path: Path) -> list[str]:
    tickers = []
    for line in path.read_text().splitlines():
        line = line.split("#")[0].strip()
        if line:
            tickers.append(line.upper())
    return tickers


def run(db_path: Path, tickers: list[str]) -> int:
    con = db.connect(db_path)
    session = requests.Session()
    failures = 0
    for ticker in tickers:
        try:
            frame = yahoo.fetch_daily(ticker, session=session)
        except yahoo.YahooError as exc:
            print(f"FAIL {exc}", file=sys.stderr)
            db.log_ingest(con, ticker, yahoo.SOURCE, 0, note=str(exc))
            failures += 1
            continue
        rows = db.insert_bars(con, frame)
        db.log_ingest(con, ticker, yahoo.SOURCE, rows)
        print(f"ok   {ticker}: {rows} new rows ({len(frame)} fetched)")
    con.close()
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("data/market.duckdb"))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--universe", type=Path, help="text file, one ticker per line")
    group.add_argument("--tickers", nargs="+", help="tickers on the command line")
    args = parser.parse_args()

    tickers = args.tickers or read_universe(args.universe)
    args.db.parent.mkdir(parents=True, exist_ok=True)
    failures = run(args.db, tickers)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
