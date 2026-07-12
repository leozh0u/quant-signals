import duckdb
import pandas as pd
import pytest

from qsignals import db


@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    c.execute(db.SCHEMA)
    return c


def make_bars(ticker="AAPL", dates=("2024-01-02", "2024-01-03")):
    return pd.DataFrame(
        {
            "ticker": ticker,
            "date": [pd.Timestamp(d).date() for d in dates],
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1_000_000,
            "source": "test",
        }
    )


def test_insert_and_count(con):
    assert db.insert_bars(con, make_bars()) == 2


def test_reinsert_is_noop(con):
    frame = make_bars()
    db.insert_bars(con, frame)
    assert db.insert_bars(con, frame) == 0
    total = con.execute("SELECT count(*) FROM bars").fetchone()[0]
    assert total == 2


def test_partial_overlap_inserts_only_new(con):
    db.insert_bars(con, make_bars(dates=("2024-01-02",)))
    inserted = db.insert_bars(con, make_bars(dates=("2024-01-02", "2024-01-03")))
    assert inserted == 1


def test_same_date_different_ticker_both_kept(con):
    db.insert_bars(con, make_bars(ticker="AAPL"))
    assert db.insert_bars(con, make_bars(ticker="MSFT")) == 2


def test_missing_column_raises(con):
    with pytest.raises(ValueError, match="volume"):
        db.insert_bars(con, make_bars().drop(columns=["volume"]))


def test_empty_frame(con):
    assert db.insert_bars(con, make_bars().iloc[:0]) == 0


def test_latest_date(con):
    assert db.latest_date(con, "AAPL") is None
    db.insert_bars(con, make_bars())
    assert db.latest_date(con, "AAPL") == pd.Timestamp("2024-01-03")
