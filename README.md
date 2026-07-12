# quant-signals

Can news sentiment plus price history predict short-horizon equity moves? Probably not, and this project takes that possibility seriously. It is a small signal research platform where the evaluation is the point: walk-forward splits, transaction costs on every trade, and pre-registered hypotheses. A signal that dies after costs gets written up, not deleted.

## Status

Early. The ingest layer works and data is accumulating; features and the backtester come next.

- [x] Daily OHLCV ingest (Yahoo chart API) into DuckDB, append-only with dedupe
- [ ] Headline ingest
- [ ] Feature engineering (returns, vol, momentum lags)
- [ ] Baselines: buy-and-hold, momentum, random signal at matched turnover
- [ ] Walk-forward backtester with cost model
- [ ] Sentiment features from headline embeddings

## Ground rules

These are fixed, and every experiment gets checked against them:

1. Splits are time-ordered. A feature at time t only uses information available at t.
2. Costs are applied to every simulated trade. Results get reported gross and net.
3. Every signal hypothesis is written down in [HYPOTHESES.md](HYPOTHESES.md) before it is tested, so there is a record of what was tried, not just what worked.
4. Negative results stay in the writeups.

## Setup

```
pip install -e ".[dev]"
qs-ingest --db data/market.duckdb --universe universe.txt
pytest
```

Ingest is idempotent. Rows already in the database are skipped on re-run, and every run lands in an `ingest_log` table for auditing.

## Layout

```
src/qsignals/db.py       DuckDB schema and append-only writes
src/qsignals/ingest/     data pulls (Yahoo daily bars, CLI runner)
tests/                   pytest suite
universe.txt             tickers under study
HYPOTHESES.md            pre-registered signal hypotheses
DECISIONS.md             engineering decision log
```
