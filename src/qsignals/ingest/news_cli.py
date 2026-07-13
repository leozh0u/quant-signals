"""Headline ingest runner: pull RSS headlines for the universe into news/.

    qs-news --news-dir news --universe universe.txt

Idempotent: items already stored (by GUID) are skipped.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

from qsignals.ingest import news
from qsignals.ingest.cli import read_universe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--news-dir", type=Path, default=Path("news"))
    parser.add_argument("--universe", type=Path, default=Path("universe.txt"))
    args = parser.parse_args()

    session = requests.Session()
    total, failures = 0, 0
    for ticker in read_universe(args.universe):
        try:
            items = news.fetch_headlines(ticker, session=session)
        except requests.RequestException as exc:
            print(f"FAIL {ticker}: {exc}", file=sys.stderr)
            failures += 1
            continue
        total += news.append_new(args.news_dir, items)
    print(f"{total} new headlines ({failures} feed failures)")
    # Feeds flake; only a fully failed run should fail the job.
    sys.exit(1 if failures and total == 0 else 0)


if __name__ == "__main__":
    main()
