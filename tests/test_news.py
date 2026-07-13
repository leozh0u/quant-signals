import json

from qsignals.ingest import news


def item(guid, published="2026-07-13T10:00:00+00:00", **kw):
    return {
        "ticker": "AAPL",
        "guid": guid,
        "published": published,
        "title": "t",
        "link": "l",
        **kw,
    }


def test_append_dedupes_by_guid(tmp_path):
    assert news.append_new(tmp_path, [item("a"), item("b"), item("a")]) == 2
    assert news.append_new(tmp_path, [item("a"), item("c")]) == 1


def test_dedupe_spans_months(tmp_path):
    news.append_new(tmp_path, [item("a", published="2026-06-30T23:00:00+00:00")])
    assert news.append_new(tmp_path, [item("a", published="2026-07-01T01:00:00+00:00")]) == 0
    assert {p.name for p in tmp_path.glob("*.jsonl")} == {"2026-06.jsonl"}


def test_files_named_by_publication_month(tmp_path):
    news.append_new(tmp_path, [item("a"), item("b", published="2026-06-01T00:00:00+00:00")])
    assert {p.name for p in tmp_path.glob("*.jsonl")} == {"2026-06.jsonl", "2026-07.jsonl"}


def test_missing_guid_or_date_skipped(tmp_path):
    assert news.append_new(tmp_path, [item(None), item("x", published=None)]) == 0


def test_lines_are_valid_json(tmp_path):
    news.append_new(tmp_path, [item("a")])
    line = (tmp_path / "2026-07.jsonl").read_text().splitlines()[0]
    assert json.loads(line)["guid"] == "a"
