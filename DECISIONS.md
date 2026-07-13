# Decisions

Running log of engineering choices and why. Newest at the bottom.

## 2026-07-13: DuckDB over SQLite/Postgres

DuckDB because the workload is analytical (columnar scans over price history), it's a single file with zero ops, and pandas interop is one `register()` call. Postgres would be justified if anything else needed to connect to this data. Nothing does.

## 2026-07-13: Append-only bars table, dedupe via anti-join

No UPSERT, no primary key enforcement doing silent replaces. An ingest bug should either add nothing or add visibly wrong rows I can find through `ingest_log`, never rewrite history in place. The anti-join on (ticker, date) makes re-runs cheap and safe, which matters because the ingest will run on a schedule and schedules fail in dumb ways.

Tradeoff accepted: if a source restates a price (Stooq does occasionally adjust), the old row wins. Good. I want to know when that happens, and a later `source`-aware view can prefer newer data deliberately.

## 2026-07-13: Yahoo chart API as first data source (Stooq fell through)

Plan A was Stooq: free CSV, no key, full history per symbol. I wrote the fetcher, then found the endpoint now sits behind a JavaScript browser-verification challenge, so plain HTTP gets a 404. Not fighting that.

Plan B is Yahoo's public v8 chart endpoint, called directly with requests instead of through the yfinance package. It's a single GET returning JSON, and when Yahoo inevitably changes something I'd rather debug my own 60-line client than someone else's scraper. The endpoint needs a browser-ish User-Agent and has undocumented rate limits, so: 1s sleep between requests, small universe. One real gotcha handled in code: timestamps come back in UTC and have to be converted to the exchange timezone before taking the date, or bars can land on the wrong day. A second: `range=max&interval=1d` silently comes back as monthly bars, which I only caught because AAPL "since 1984" had 168 rows. The client now requests explicit period1/period2 epochs and rejects any response whose reported granularity isn't 1d. A second source later is still the plan, since cross-source disagreement is itself useful data.

## 2026-07-13: adj_close added after catching an unadjusted-price bug

The first schema stored Yahoo's `quote.close` only. Momentum on raw closes would have printed a fake -90% NVDA day at the 2024 split. Yahoo's chart prices turn out to be split-adjusted already, but not dividend-adjusted, so the schema now carries `adjclose` (total-return adjusted) in its own column and all return math uses it. Raw close stays for reference. Local db wiped and re-pulled since prices are fully backfillable.

## 2026-07-13: Backtester contract is a weights panel

Every strategy is a date x ticker DataFrame of target close-of-day weights; the engine applies `weights.shift(1) * returns` so day-t decisions earn day t+1. One line owns the no-lookahead guarantee and one test locks it. Baselines and random nulls go through identical cost math, so comparisons can't diverge by construction. Rejected an event-driven order simulator: at daily frequency it's extra machinery with nothing to say until there's an intraday fill model, which is out of scope.

## 2026-07-13: Random null gets turnover-matched

A daily-redrawn random long-short churns ~2x the momentum signal and its costs bury it, which makes "beats random" free. The null now redraws every k days with k chosen as the smallest hold whose turnover is at or below the signal's. This moved the null's p95 net Sharpe from silly to plausible and is the difference between a real kill line and theater.

## 2026-07-13: Universe widened to ~S&P 100; tickers are not stable identifiers

H1's loudest caveat was the 10-name cross-section, so the universe is now roughly the current S&P 100. Two tickers 404ed on ingest: Marsh & McLennan and Fiserv, which turned out to have changed symbols (MMC to MRSH, FI to FISV). Lesson recorded because it generalizes: a ticker is a mutable label, not an identity, and any pipeline keyed on tickers silently drops or duplicates companies across renames. Proper fix is a security-master table with symbol history; out of scope until it bites something that matters.

The widened universe is today's membership, hence survivorship-biased. Documented in universe.txt itself and carried as a standing caveat on every hypothesis, rather than pretended away.

## 2026-07-13: Headlines land in committed JSONL, not the database

Prices are backfillable at any time; headlines are not — Yahoo's RSS holds roughly 20 items per ticker, so history only exists if something was pulling it continuously. A scheduled GitHub Actions job pulls every 6 hours and commits monthly JSONL files under news/. The repo is the durable store because the DuckDB file is deliberately disposable; anything that can't be regenerated has to live in git. Volume is small text, so committing data is fine here.

## 2026-07-13: Walk-forward harness contract

`walk_forward(prices, fit)` rolls a fixed train window and stitches out-of-sample weights; `fit` returns a strategy closure. The subtle line: inside a test window the strategy sees price history across the train/test boundary, because a 20-day lookback on day one of the test window legitimately reads the prior month. What must not cross the boundary is parameter choice, and a test pins that (each fit's last train date precedes every date it produces weights for). Conflating those two leakage types is how backtests quietly rot.

## 2026-07-13: Sentiment layer deferred, on purpose

The headline archive is weeks old. Embeddings over that would produce a writeup with no statistical content, so the NLP phase waits until the news cron has accumulated a few months. The deferral is the decision: shipping the feature now would look productive and mean nothing.

## 2026-07-13: Start ingest before anything else

History depth only grows with calendar time. Features and the backtester can be built against whatever has accumulated; the reverse isn't true.
