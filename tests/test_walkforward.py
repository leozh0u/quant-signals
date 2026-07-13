import numpy as np
import pandas as pd
import pytest

from qsignals import signals, walkforward

PRICES = pd.DataFrame(
    np.cumprod(1 + np.random.default_rng(0).normal(0, 0.01, (400, 5)), axis=0),
    index=pd.bdate_range("2020-01-01", periods=400),
    columns=list("ABCDE"),
)


def test_covers_exactly_the_out_of_sample_rows():
    w = walkforward.walk_forward(PRICES, lambda tr: signals.equal_weight, 100, 50)
    assert w.index.equals(PRICES.index[100:])
    assert not w.index.duplicated().any()


def test_fit_never_sees_its_test_window():
    boundaries = []

    def fit(train):
        boundaries.append(train.index[-1])
        return signals.equal_weight

    w = walkforward.walk_forward(PRICES, fit, 100, 50)
    # each fit's last training date precedes every date it produced weights for
    for i, last_train in enumerate(boundaries):
        window = w.index[i * 50 : (i + 1) * 50]
        assert (window > last_train).all()


def test_train_slices_have_fixed_length():
    lengths = []
    walkforward.walk_forward(PRICES, lambda tr: (lengths.append(len(tr)), signals.equal_weight)[1], 100, 50)
    assert set(lengths) == {100}


def test_too_little_data_raises():
    with pytest.raises(ValueError, match="need more than"):
        walkforward.walk_forward(PRICES.iloc[:50], lambda tr: signals.equal_weight, 100, 50)


def test_momentum_rebalance_reduces_turnover():
    daily = signals.momentum_ls(PRICES, lookback=20)
    weekly = signals.momentum_ls(PRICES, lookback=20, rebalance=5)
    t = lambda w: w.diff().abs().sum().sum()  # noqa: E731
    assert t(weekly) < t(daily) / 2
