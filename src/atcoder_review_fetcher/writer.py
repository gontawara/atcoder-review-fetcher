"""練習リポジトリへのファイル書き出し。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_URL = "https://atcoder.jp"


@dataclass
class ProblemBundle:
    letter: str
    slug: str
    title: str
    statement_md: str | None = None
    editorial_md: str | None = None
    editorial_url: str | None = None
    local_solutions: list[str] = field(default_factory=list)


def problem_dir(repo: Path, contest_id: str, letter: str) -> Path:
    return repo / "contests" / contest_id / letter


def collect_local_solutions(repo: Path, contest_id: str, letter: str) -> list[str]:
    """コンテスト中にユーザーが書いたコードファイル名の一覧。"""
    directory = problem_dir(repo, contest_id, letter)
    if not directory.is_dir():
        return []
    return sorted(
        p.name
        for p in directory.iterdir()
        if p.is_file() and p.suffix in {".py", ".cpp", ".rs", ".java"}
    )


def write_problem(repo: Path, contest_id: str, bundle: ProblemBundle) -> list[Path]:
    """problem.md / editorial.md を書き出す。既存ファイルは上書きしない。"""
    directory = problem_dir(repo, contest_id, bundle.letter)
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    problem_url = f"{BASE_URL}/contests/{contest_id}/tasks/{bundle.slug}"
    if bundle.statement_md is not None:
        path = directory / "problem.md"
        if not path.exists():
            header = (
                f"# {bundle.letter.upper()} - {bundle.title}\n\n"
                f"[問題ページ]({problem_url})\n\n---\n\n"
            )
            path.write_text(header + bundle.statement_md, encoding="utf-8")
            written.append(path)

    if bundle.editorial_md is not None:
        path = directory / "editorial.md"
        if not path.exists():
            header = (
                f"# 公式解説: {bundle.letter.upper()} - {bundle.title}\n\n"
                f"[解説ページ]({bundle.editorial_url})\n\n---\n\n"
            )
            path.write_text(header + bundle.editorial_md, encoding="utf-8")
            written.append(path)

    return written


def write_contest_index(
    repo: Path,
    contest_id: str,
    contest_title: str,
    bundles: list[ProblemBundle],
    fetched_at: datetime,
) -> Path:
    """contests/{id}/contest.md（取得サマリ兼復習チェックリスト）を書き出す。"""
    lines = [
        f"# {contest_title}",
        "",
        f"- コンテスト: {BASE_URL}/contests/{contest_id}",
        f"- 解説一覧: {BASE_URL}/contests/{contest_id}/editorial",
        f"- 取得日時: {fetched_at.isoformat(timespec='seconds')}",
        "",
        "| 問題 | タイトル | 問題文 | 解説 | 自分のコード | 復習 |",
        "|---|---|---|---|---|---|",
    ]
    for b in bundles:
        directory = problem_dir(repo, contest_id, b.letter)
        statement = "あり" if (directory / "problem.md").exists() else "-"
        editorial = "あり" if (directory / "editorial.md").exists() else "未公開"
        code = ", ".join(b.local_solutions) if b.local_solutions else "なし"
        lines.append(
            f"| {b.letter.upper()} | {b.title} | {statement} | {editorial} "
            f"| {code} | [ ] |"
        )
    lines += [
        "",
        "復習が終わった問題は「復習」列にチェックを入れる。",
        "",
    ]
    path = repo / "contests" / contest_id / "contest.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
