from atcoder_review_fetcher.statement import parse_statement, parse_task_list


def test_parse_task_list(fixture_html):
    tasks = parse_task_list(fixture_html("tasks_abc450.html"), "abc450")
    assert len(tasks) == 7
    assert tasks[0].letter == "a"
    assert tasks[0].slug == "abc450_a"
    assert tasks[2].letter == "c"


def test_parse_statement_ja(fixture_html):
    md = parse_statement(fixture_html("task_abc407_c.html"), lang="ja")
    assert "問題文" in md
    assert "制約" in md
    # <var>S</var> が $S$ に変換される
    assert "$S$" in md
    # 数式の不等号も LaTeX のまま $...$ に入る
    assert "$1 \\leq |S| \\leq 5 \\times 10^5$" in md
    # 英語文は含まれない
    assert "Problem Statement" not in md


def test_parse_statement_has_samples(fixture_html):
    md = parse_statement(fixture_html("task_abc407_c.html"), lang="ja")
    assert "入力例" in md
    assert "出力例" in md
