"""Walk-forward evaluation for anything with parameters to choose.

The rule: parameters may be chosen only from data strictly before the test
window they're used in. walk_forward rolls a train window along the panel,
lets `fit` pick a strategy from each train slice, and stitches the resulting
out-of-sample weights into one panel that backtest.run scores like any other
strategy. Selection bias in the fit stays in the train windows, where it
belongs.

fit(train_prices) returns a strategy: a function mapping a price panel to a
weight panel. Inside the test window the strategy receives history up to the
day being weighted (so lookbacks work across the boundary), which is fine:
the *parameters* are what must not see the future, not the price history a
signal naturally consumes.
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

Strategy = Callable[[pd.DataFrame], pd.DataFrame]
Fit = Callable[[pd.DataFrame], Strategy]


def walk_forward(
    prices: pd.DataFrame,
    fit: Fit,
    train_days: int = 504,
    test_days: int = 126,
) -> pd.DataFrame:
    """Stitched out-of-sample weights over every test window."""
    if len(prices) <= train_days:
        raise ValueError(f"need more than {train_days} rows, have {len(prices)}")
    chunks = []
    for start in range(train_days, len(prices), test_days):
        strategy = fit(prices.iloc[start - train_days : start])
        end = min(start + test_days, len(prices))
        # full history in, test rows out: lookbacks span the boundary,
        # weights are only kept for days the fit never saw
        chunks.append(strategy(prices.iloc[:end]).iloc[start:end])
    return pd.concat(chunks)
