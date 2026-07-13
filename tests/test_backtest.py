import numpy as np
import pandas as pd
import pytest

from qsignals import backtest, signals

DATES = pd.bdate_range("2024-01-01", periods=6)


def panel(**cols):
    return pd.DataFrame(cols, index=DATES[: len(next(iter(cols.values())))], dtype=float)


def test_no_lookahead():
    # Price doubles on day 3. A weight set on day 3 must not capture day 3's
    # return; only a weight already held from day 2 does.
    prices = panel(A=[1, 1, 2, 2, 2, 2])
    late = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    late.iloc[2:, 0] = 1.0  # enters at day-3 close, after the move
    res = backtest.run(late, prices, cost_bps=0)
    assert res.ann_gross == 0.0

    early = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    early.iloc[1:, 0] = 1.0  # holds through the move
    assert backtest.run(early, prices, cost_bps=0).ann_gross > 0


def test_costs_charged_on_turnover():
    prices = panel(A=[1, 1, 1, 1, 1, 1])  # flat prices: net return is pure cost
    weights = pd.DataFrame({"A": [1, 0, 1, 0, 1, 0]}, index=prices.index, dtype=float)
    res = backtest.run(weights, prices, cost_bps=100)  # 1% per side
    # every day flips the full position: 1.0 turnover per live day
    assert res.net_returns.mean() == pytest.approx(-0.01)


def test_max_drawdown_known_value():
    rets = pd.Series([0.10, -0.50, 0.10])
    assert backtest.max_drawdown(rets) == pytest.approx(-0.50)


def test_nan_prices_do_not_poison_returns():
    prices = panel(A=[1, 1.1, 1.21, 1.331, 1.4641, 1.61051], B=[np.nan] * 6)
    weights = signals.equal_weight(prices)
    res = backtest.run(weights, prices, cost_bps=0)
    assert np.isfinite(res.ann_gross)
    assert res.ann_gross > 0


def test_momentum_weights_are_dollar_neutral():
    rng = np.random.default_rng(0)
    prices = pd.DataFrame(
        np.cumprod(1 + rng.normal(0, 0.01, (300, 10)), axis=0),
        index=pd.bdate_range("2020-01-01", periods=300),
        columns=list("ABCDEFGHIJ"),
    )
    w = signals.momentum_ls(prices, lookback=20)
    live = w.abs().sum(axis=1) > 0
    assert live.any()
    assert np.allclose(w[live].sum(axis=1), 0, atol=1e-12)
    assert np.allclose(w[live].abs().sum(axis=1), 2, atol=1e-12)


def test_random_ls_hold_reduces_turnover():
    rng = np.random.default_rng(0)
    prices = pd.DataFrame(
        np.cumprod(1 + rng.normal(0, 0.01, (300, 10)), axis=0),
        index=pd.bdate_range("2020-01-01", periods=300),
        columns=list("ABCDEFGHIJ"),
    )
    fast = backtest.run(signals.random_ls(prices, np.random.default_rng(1)), prices)
    slow = backtest.run(signals.random_ls(prices, np.random.default_rng(1), hold=10), prices)
    assert slow.ann_turnover < fast.ann_turnover / 3
