# quant-signals

Can news sentiment plus price history predict short-horizon equity moves? Probably not, and this project takes that possibility seriously. It is a small signal research platform where the evaluation is the point: walk-forward splits, transaction costs on every trade, and pre-registered hypotheses. A signal that dies after costs gets written up, not deleted.

## Status

The ingest layer, backtester, and walk-forward harness are built, and five hypotheses have been tested and written up. Sentiment features wait on a deeper news archive.

- [x] Daily OHLCV ingest (Yahoo chart API) into DuckDB, append-only with dedupe
- [x] Vectorized backtester with cost model and no-lookahead tests
- [x] Baselines: buy-and-hold, momentum, random signal at matched turnover
- [x] Results so far (writeups in HYPOTHESES.md): H1 and H2 dead; 20d momentum
      has no edge here at any universe size. H3 supported: the sign flips, and
      short-term reversal is real gross (+0.49 Sharpe) but costs eat it entirely.
- [x] Universe: ~S&P 100 (survivorship caveat documented in universe.txt)
- [x] Headline ingest: scheduled RSS pulls committed to news/ every 6h, since
      headlines can't be backfilled later
- [x] CI: lint + tests on every push
- [x] H4/H5: the best reversal variant is cost-breakeven (net Sharpe 0.01),
      and walk-forward parameter selection makes it worse, not better
- [x] Walk-forward harness with a leakage test on the train/test boundary
- [ ] Sentiment features from headline embeddings, deferred until the news
      archive is months deep; embedding three weeks of RSS proves nothing

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
src/qsignals/db.py        DuckDB schema and append-only writes
src/qsignals/ingest/      data pulls (Yahoo daily bars, CLI runner)
src/qsignals/panel.py     bars -> wide date x ticker price panels
src/qsignals/signals.py   strategies as target-weight panels
src/qsignals/backtest.py  vectorized engine: shift(1), costs, Sharpe, drawdown
src/qsignals/walkforward.py  rolling train/test parameter selection
experiments/              one runnable script per hypothesis
tests/                    pytest suite (incl. an explicit no-lookahead test)
universe.txt              tickers under study
HYPOTHESES.md             pre-registered signal hypotheses and results
DECISIONS.md              engineering decision log
```
