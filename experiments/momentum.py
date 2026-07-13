"""Does 20-day cross-sectional momentum survive costs? (H1, H2 in HYPOTHESES.md)

Runs the momentum long-short against buy-and-hold and a 200-draw random null
with turnover matched via the hold parameter, then prints per-year net Sharpe
so one lucky stretch can't carry the headline number.

    # H1 (original 10 mega caps):
    python experiments/momentum.py --tickers AAPL MSFT NVDA AMZN GOOGL META JPM XOM UNH PG
    # H2 (full universe file; ETFs excluded automatically):
    python experiments/momentum.py --universe universe.txt
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from qsignals import backtest, db, panel, signals
from qsignals.ingest.cli import read_universe

ETFS = {"SPY", "QQQ"}
N_NULL = 200
COST_BPS = 10.0


def match_hold(prices, target_turnover) -> int:
    """Smallest hold period whose random-null turnover is at or below the
    signal's. Coarse is fine; the point is not to hand the null a cost bill
    the signal doesn't pay."""
    rng = np.random.default_rng(0)
    for hold in range(1, 60):
        t = backtest.run(signals.random_ls(prices, rng, hold=hold), prices, COST_BPS).ann_turnover
        if t <= target_turnover:
            return hold
    return 60


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/market.duckdb")
    parser.add_argument("--start", default="2000-01-01", help="skip pre-2000 sparse history")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--universe", type=Path)
    group.add_argument("--tickers", nargs="+")
    parser.add_argument(
        "--flip", action="store_true", help="reversal book: long losers, short winners (H3)"
    )
    args = parser.parse_args()

    stocks = [t for t in (args.tickers or read_universe(args.universe)) if t not in ETFS]
    con = db.connect(args.db)
    prices = panel.adj_close_panel(con, stocks)
    prices = prices.loc[args.start :]

    weights = signals.momentum_ls(prices, lookback=20)
    if args.flip:
        weights = -weights
    mom = backtest.run(weights, prices, COST_BPS)
    hold = match_hold(prices, mom.ann_turnover)
    hold_bh = backtest.run(signals.equal_weight(prices), prices, COST_BPS)

    rng = np.random.default_rng(42)
    null_sharpes = np.array(
        [
            backtest.run(signals.random_ls(prices, rng, hold=hold), prices, COST_BPS).net_sharpe
            for _ in range(N_NULL)
        ]
    )
    p95 = np.percentile(null_sharpes, 95)

    print(f"universe: {len(stocks)} stocks, {prices.index[0]:%Y-%m-%d} to {prices.index[-1]:%Y-%m-%d}")
    print(f"cost assumption: {COST_BPS} bps per side; null hold={hold}d ({N_NULL} draws)\n")
    name = "reversal 20d L/S " if args.flip else "momentum 20d L/S"
    print(f"{name}  {mom.summary()}")
    print(f"buy and hold (EW)  {hold_bh.summary()}")
    print(
        f"random null        net sharpe p5/p50/p95: "
        f"{np.percentile(null_sharpes, 5):.2f} / {np.median(null_sharpes):.2f} / {p95:.2f}"
    )
    verdict = "SURVIVES" if mom.net_sharpe > p95 else "DEAD"
    print(f"\nH1 kill line: net sharpe {mom.net_sharpe:.2f} vs null p95 {p95:.2f} -> {verdict}")

    print("\nper-year net sharpe (momentum):")
    yearly = mom.net_returns.groupby(mom.net_returns.index.year).agg(
        lambda r: r.mean() / r.std() * np.sqrt(backtest.TRADING_DAYS) if r.std() > 0 else 0.0
    )
    for year, sharpe in yearly.items():
        print(f"  {year}: {sharpe:6.2f}")


if __name__ == "__main__":
    main()
