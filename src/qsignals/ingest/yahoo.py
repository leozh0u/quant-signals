"""Daily OHLCV from Yahoo Finance's chart API.

Uses the public v8 chart endpoint directly rather than the yfinance package:
it's one GET returning JSON, and a direct client is easier to debug when
Yahoo changes something. A browser-ish User-Agent is required; without it
Yahoo returns 429s. Rate limits are undocumented, so the fetcher sleeps
between requests and universes should stay small.
"""

from __future__ import annotations

import time

import pandas as pd
import requests

BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"
SOURCE = "yahoo"
_SLEEP_SECONDS = 1.0
_HEADERS = {"User-Agent": "Mozilla/5.0"}


class YahooError(RuntimeError):
    pass


def fetch_daily(ticker: str, session: requests.Session | None = None) -> pd.DataFrame:
    """Fetch full daily history for one ticker.

    Returns a frame with the bars-table columns (see qsignals.db.BAR_COLUMNS).
    Timestamps are converted to exchange-local dates so a bar dated 2024-01-02
    means that trading day, regardless of the machine's timezone.

    Uses explicit period1/period2 epochs rather than range=max: with range=max
    Yahoo silently downgrades interval=1d to monthly bars, and the granularity
    check below would reject the response.
    """
    sess = session or requests.Session()
    resp = sess.get(
        f"{BASE_URL}{ticker.upper()}",
        params={"period1": 0, "period2": 9_999_999_999, "interval": "1d"},
        headers=_HEADERS,
        timeout=30,
    )
    if resp.status_code != 200:
        raise YahooError(f"{ticker}: HTTP {resp.status_code}")

    payload = resp.json().get("chart", {})
    if payload.get("error"):
        raise YahooError(f"{ticker}: {payload['error']}")
    try:
        result = payload["result"][0]
        timestamps = result["timestamp"]
        quote = result["indicators"]["quote"][0]
        tz = result["meta"]["exchangeTimezoneName"]
    except (KeyError, IndexError, TypeError) as exc:
        raise YahooError(f"{ticker}: malformed response ({exc!r})") from exc

    granularity = result["meta"].get("dataGranularity")
    if granularity != "1d":
        raise YahooError(f"{ticker}: asked for 1d bars, got {granularity!r}")

    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(timestamps, unit="s", utc=True).tz_convert(tz).date,
            "open": quote["open"],
            "high": quote["high"],
            "low": quote["low"],
            "close": quote["close"],
            "volume": quote["volume"],
        }
    )
    # Yahoo pads holidays/halts with all-null rows; drop them.
    frame = frame.dropna(subset=["close"])
    frame["volume"] = frame["volume"].fillna(0).astype("int64")
    frame["ticker"] = ticker.upper()
    frame["source"] = SOURCE
    time.sleep(_SLEEP_SECONDS)
    return frame
