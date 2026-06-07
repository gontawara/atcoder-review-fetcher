from atcoder_review_fetcher.editorial import (
    EditorialLink,
    choose_editorial,
    parse_editorial_body,
    parse_editorial_index,
)


def test_parse_editorial_index(fixture_html):
    index = parse_editorial_index(fixture_html("editorial_index_abc407.html"), "abc407")
    assert "abc407_c" in index
    links = index["abc407_c"]
    # 外部リンク（解説放送）は含まれない
    assert all(link.path.startswith("/contests/abc407/editorial/") for link in links)
    # 公式の日本語解説 13105 が含まれる
    assert any(link.path.endswith("/13105") and link.official for link in links)


def test_choose_editorial_prefers_official_ja():
    links = [
        EditorialLink("/contests/x/editorial/2", "Editorial", official=True),
        EditorialLink("/contests/x/editorial/1", "解説", official=True),
        EditorialLink("/contests/x/editorial/3", "ユーザ解説", official=False),
    ]
    chosen = choose_editorial(links, lang="ja")
    assert chosen is not None
    assert chosen.path.endswith("/1")


def test_choose_editorial_fallback_official():
    links = [
        EditorialLink("/contests/x/editorial/3", "ユーザ解説", official=False),
        EditorialLink("/contests/x/editorial/2", "Editorial", official=True),
    ]
    chosen = choose_editorial(links, lang="ja")
    assert chosen is not None
    assert chosen.path.endswith("/2")


def test_choose_editorial_empty():
    assert choose_editorial([], lang="ja") is None


def test_parse_editorial_body(fixture_html):
    title, body = parse_editorial_body(fixture_html("editorial_abc407_c.html"))
    assert "C - Security 2" in title
    # \(S\) → $S$ に変換される
    assert "$S$" in body
    assert "\\(" not in body
    # C++ 実装例がコードフェンスで残る
    assert "```cpp" in body
    assert "int main" in body
