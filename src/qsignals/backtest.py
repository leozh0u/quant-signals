"""Vectorized daily backtester over target-weight panels.

The contract that prevents lookahead lives in one line: weights decided at
the close of day t earn day t+1's return (`weights.shift(1) * rets`). Any
signal is expressed as a weights DataFrame (date x ticker, rows are target
portfolio weights as of that close), so every strategy, baseline, and random
null goes through the identical return and cost math.

Costs are charged on turnover: cost_bps per side times the sum of absolute
weight changes. That's a simple model (no market impact, no spread widening
in stress), which overstates nothing except its own precision.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass(frozen=True)
class Result:
    gross_sharpe: float
    net_sharpe: float
    ann_gross: float
    ann_net: float
    max_drawdown: float
    ann_turnover: float
    n_days: int
    net_returns: pd.Series

    def summary(self) -> str:
        return (
            f"sharpe {self.gross_sharpe:6.2f} gross / {self.net_sharpe:6.2f} net | "
            f"ann ret {self.ann_gross:7.2%} / {self.ann_net:7.2%} | "
            f"maxDD {self.max_drawdown:7.2%} | turnover {self.ann_turnover:6.1f}x/yr"
        )


def _sharpe(returns: pd.Series) -> float:
    std = returns.std()
    return float(returns.mean() / std * np.sqrt(TRADING_DAYS)) if std > 0 else 0.0


def max_drawdown(returns: pd.Series) -> float:
    equity = (1 + returns).cumprod()
    return float((equity / equity.cummax() - 1).min())


def run(weights: pd.DataFrame, prices: pd.DataFrame, cost_bps: float = 10.0) -> Result:
    """Backtest target weights against an adjusted-close panel.

    weights and prices share the same index/columns; weights rows are the
    target portfolio at that day's close. NaN weights are treated as zero.
    """
    weights = weights.reindex(index=prices.index, columns=prices.columns).fillna(0.0)
    rets = prices.pct_change(fill_method=None)

    held = weights.shift(1)
    gross = (held * rets).sum(axis=1)
    turnover = (weights - held).abs().sum(axis=1)
    net = gross - turnover * cost_bps / 10_000

    # Score only days the strategy could have held a position.
    live = held.abs().sum(axis=1) > 0
    gross, net, turnover = gross[live], net[live], turnover[live]
    if gross.empty:
        raise ValueError("strategy never holds a position")

    return Result(
        gross_sharpe=_sharpe(gross),
        net_sharpe=_sharpe(net),
        ann_gross=float(gross.mean() * TRADING_DAYS),
        ann_net=float(net.mean() * TRADING_DAYS),
        max_drawdown=max_drawdown(net),
        ann_turnover=float(turnover.mean() * TRADING_DAYS),
        n_days=len(net),
        net_returns=net,
    )
