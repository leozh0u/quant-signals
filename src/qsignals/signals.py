"""Signals as weight-panel constructors.

Every function returns a date x ticker DataFrame of target weights at each
day's close, ready for backtest.run. Signals only look backward: anything
derived from prices uses data up to and including day t to set day t's row,
and the backtester's shift(1) delays execution to t+1.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def equal_weight(prices: pd.DataFrame) -> pd.DataFrame:
    """Buy and hold everything listed that day, equally weighted."""
    listed = prices.notna()
    return listed.div(listed.sum(axis=1), axis=0).fillna(0.0)


def momentum_ls(prices: pd.DataFrame, lookback: int = 20, quantile: float = 0.2) -> pd.DataFrame:
    """Cross-sectional momentum: long the top quantile of trailing returns,
    short the bottom, dollar neutral, equal weight within each leg.
    """
    mom = prices.pct_change(lookback, fill_method=None)
    ranks = mom.rank(axis=1, pct=True)
    long = (ranks >= 1 - quantile).astype(float)
    short = (ranks <= quantile).astype(float)
    weights = long.div(long.sum(axis=1), axis=0).fillna(0.0) - short.div(
        short.sum(axis=1), axis=0
    ).fillna(0.0)
    return weights


def random_ls(
    prices: pd.DataFrame,
    rng: np.random.Generator,
    quantile: float = 0.2,
    hold: int = 1,
) -> pd.DataFrame:
    """Same long-short construction as momentum_ls but ranks are random.

    The null baseline: identical position sizing and legs, no information.
    Ranks redraw every `hold` days; daily redraws churn far more than a
    persistent signal does, so the caller should pick `hold` to match the
    tested signal's turnover, otherwise costs sink the null unfairly and
    'beats random' means nothing.
    """
    noise = pd.DataFrame(
        rng.random(prices.shape), index=prices.index, columns=prices.columns
    )
    if hold > 1:
        redraw = np.arange(len(noise)) % hold != 0
        noise[redraw] = np.nan
        noise = noise.ffill()
    noise = noise.where(prices.notna())
    ranks = noise.rank(axis=1, pct=True)
    long = (ranks >= 1 - quantile).astype(float)
    short = (ranks <= quantile).astype(float)
    return long.div(long.sum(axis=1), axis=0).fillna(0.0) - short.div(
        short.sum(axis=1), axis=0
    ).fillna(0.0)
