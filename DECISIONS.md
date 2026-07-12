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

## 2026-07-13: Start ingest before anything else

History depth only grows with calendar time. Features and the backtester can be built against whatever has accumulated; the reverse isn't true.
