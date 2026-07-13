"""H4/H5: do slower or tighter reversal variants survive costs, and does
walk-forward parameter selection help? (HYPOTHESES.md)

    python experiments/reversal_variants.py --universe universe.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from qsignals import backtest, db, panel, signals, walkforward
from qsignals.ingest.cli import read_universe

ETFS = {"SPY", "QQQ"}
GRID = [(reb, q) for reb in (1, 5, 10) for q in (0.2, 0.1)]
N_NULL = 100
COST_BPS = 10.0


def reversal(prices, rebalance, quantile):
    return -signals.momentum_ls(prices, lookback=20, quantile=quantile, rebalance=rebalance)


def null_p99(prices, quantile, target_turnover) -> float:
    """p99 of net Sharpe over turnover-matched random books."""
    rng = np.random.default_rng(0)
    hold = next(
        h
        for h in range(1, 61)
        if h == 60
        or backtest.run(signals.random_ls(prices, rng, quantile, hold=h), prices, COST_BPS).ann_turnover
        <= target_turnover
    )
    rng = np.random.default_rng(42)
    sharpes = [
        backtest.run(signals.random_ls(prices, rng, quantile, hold=hold), prices, COST_BPS).net_sharpe
        for _ in range(N_NULL)
    ]
    return float(np.percentile(sharpes, 99))


def fit_best_variant(train):
    """H5 fit: pick the grid variant with the best net Sharpe on the train
    slice. Returns a strategy closure for walk_forward."""
    best = max(GRID, key=lambda p: backtest.run(reversal(train, *p), train, COST_BPS).net_sharpe)
    return lambda prices: reversal(prices, *best)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/market.duckdb")
    parser.add_argument("--universe", type=Path, default=Path("universe.txt"))
    parser.add_argument("--start", default="2000-01-01")
    args = parser.parse_args()

    con = db.connect(args.db)
    stocks = [t for t in read_universe(args.universe) if t not in ETFS]
    prices = panel.adj_close_panel(con, stocks).loc[args.start :]

    print(f"H4 grid ({len(GRID)} variants, kill bar = null p99 AND net > 0):")
    survivors = []
    for reb, q in GRID:
        res = backtest.run(reversal(prices, reb, q), prices, COST_BPS)
        p99 = null_p99(prices, q, res.ann_turnover)
        ok = res.net_sharpe > 0 and res.net_sharpe > p99
        survivors += [(reb, q)] if ok else []
        print(f"  reb={reb:2d} q={q}  {res.summary()} | null p99 {p99:5.2f} -> {'SURVIVES' if ok else 'dead'}")
    print(f"H4: {'SUPPORTED ' + str(survivors) if survivors else 'DEAD, no variant survives'}\n")

    oos = walkforward.walk_forward(prices, fit_best_variant)
    res = backtest.run(oos, prices.loc[oos.index], COST_BPS)
    print("H5 walk-forward selection (504d train / 126d test), OOS:")
    print(f"  {res.summary()}")


if __name__ == "__main__":
    main()
