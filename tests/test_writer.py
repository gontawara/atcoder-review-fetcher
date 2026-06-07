from datetime import datetime, timedelta, timezone

from atcoder_review_fetcher.writer import (
    ProblemBundle,
    collect_local_solutions,
    write_contest_index,
    write_problem,
)

JST = timezone(timedelta(hours=9))


def _bundle() -> ProblemBundle:
    return ProblemBundle(
        letter="c",
        slug="abc999_c",
        title="Test Problem",
        statement_md="問題文です。\n",
        editorial_md="解説です。\n",
        editorial_url="https://atcoder.jp/contests/abc999/editorial/1",
    )


def test_write_problem_creates_files(tmp_path):
    written = write_problem(tmp_path, "abc999", _bundle())
    assert len(written) == 2
    assert (tmp_path / "contests/abc999/c/problem.md").exists()
    assert (tmp_path / "contests/abc999/c/editorial.md").exists()
    content = (tmp_path / "contests/abc999/c/problem.md").read_text(encoding="utf-8")
    assert content.startswith("# C - Test Problem")


def test_write_problem_does_not_overwrite(tmp_path):
    target = tmp_path / "contests/abc999/c"
    target.mkdir(parents=True)
    (target / "problem.md").write_text("手で編集済み", encoding="utf-8")
    written = write_problem(tmp_path, "abc999", _bundle())
    assert [p.name for p in written] == ["editorial.md"]
    assert (target / "problem.md").read_text(encoding="utf-8") == "手で編集済み"


def test_collect_local_solutions(tmp_path):
    target = tmp_path / "contests/abc999/c"
    target.mkdir(parents=True)
    (target / "main.py").write_text("print()", encoding="utf-8")
    (target / "problem.md").write_text("x", encoding="utf-8")
    assert collect_local_solutions(tmp_path, "abc999", "c") == ["main.py"]
    assert collect_local_solutions(tmp_path, "abc999", "d") == []


def test_write_contest_index(tmp_path):
    bundle = _bundle()
    write_problem(tmp_path, "abc999", bundle)
    bundle.local_solutions = ["main.py"]
    path = write_contest_index(
        tmp_path, "abc999", "ABC999", [bundle], fetched_at=datetime.now(JST)
    )
    content = path.read_text(encoding="utf-8")
    assert "| C | Test Problem | あり | あり | main.py | [ ] |" in content
