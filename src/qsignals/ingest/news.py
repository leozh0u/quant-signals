"""Headline ingest from Yahoo Finance's per-ticker RSS feeds.

Headlines are the one dataset here that can't be backfilled: the feed only
serves recent items, so history exists only if something was pulling it. A
scheduled job appends to monthly JSONL files under news/ (committed to the
repo; the volume is tiny text), deduped by item GUID across all months.
JSONL over the DuckDB file because the database is disposable and rebuilt
from source data; these files ARE the source data.
"""

from __future__ import annotations

import email.utils
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

FEED_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline"
_HEADERS = {"User-Agent": "Mozilla/5.0"}
_SLEEP_SECONDS = 0.5


def fetch_headlines(ticker: str, session: requests.Session | None = None) -> list[dict]:
    """Fetch current RSS items for one ticker as JSON-ready dicts."""
    sess = session or requests.Session()
    resp = sess.get(
        FEED_URL,
        params={"s": ticker.upper(), "region": "US", "lang": "en-US"},
        headers=_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    items = []
    for item in ET.fromstring(resp.content).iter("item"):
        pub = item.findtext("pubDate")
        items.append(
            {
                "ticker": ticker.upper(),
                "guid": item.findtext("guid"),
                "published": email.utils.parsedate_to_datetime(pub).isoformat() if pub else None,
                "title": (item.findtext("title") or "").strip(),
                "link": item.findtext("link"),
            }
        )
    time.sleep(_SLEEP_SECONDS)
    return items


def seen_guids(news_dir: Path) -> set[str]:
    guids = set()
    for path in news_dir.glob("*.jsonl"):
        for line in path.read_text().splitlines():
            guids.add(json.loads(line)["guid"])
    return guids


def append_new(news_dir: Path, items: list[dict]) -> int:
    """Append items whose GUID hasn't been stored, into files named by the
    item's publication month. Returns the number written."""
    news_dir.mkdir(parents=True, exist_ok=True)
    seen = seen_guids(news_dir)
    written = 0
    for item in items:
        if not item["guid"] or item["guid"] in seen or not item["published"]:
            continue
        seen.add(item["guid"])
        month_file = news_dir / f"{item['published'][:7]}.jsonl"
        with month_file.open("a") as fh:
            fh.write(json.dumps(item, sort_keys=True) + "\n")
        written += 1
    return written
