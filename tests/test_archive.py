from datetime import datetime, timedelta, timezone

from atcoder_review_fetcher.archive import parse_latest_contest

JST = timezone(timedelta(hours=9))


def test_parse_latest_contest(fixture_html):
    ref = parse_latest_contest(fixture_html("archive.html"), prefix="abc")
    assert ref is not None
    assert ref.contest_id == "abc460"
    assert ref.start_at == datetime(2026, 5, 30, 21, 0, 0, tzinfo=JST)


def test_parse_latest_contest_no_match(fixture_html):
    ref = parse_latest_contest(fixture_html("archive.html"), prefix="zzz")
    assert ref is None
