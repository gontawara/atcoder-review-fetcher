"""練習リポジトリの git commit / push。"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} が失敗しました:\n{result.stderr.strip()}"
        )
    return result


def commit_and_push(
    repo: Path,
    contest_id: str,
    push: bool = True,
    remote: str = "origin",
    branch: str = "main",
) -> bool:
    """contests/{id} 配下の変更をコミットし push する。

    変更がなければ何もせず False を返す。
    """
    _git(repo, "add", f"contests/{contest_id}")
    diff = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--quiet"],
    )
    if diff.returncode == 0:
        logger.info("変更なし: コミットをスキップします")
        return False

    # 注: 問題文・解説は practice リポの .gitignore でローカルのみ扱いのため、
    # 実際にコミットされるのは自分のコードと acc 雛形だけになる
    _git(repo, "commit", "-m", f"[add]{contest_id}: コンテストのコードを追加")
    logger.info("コミット完了: %s", contest_id)

    if push:
        _git(repo, "push", remote, branch)
        logger.info("push 完了: %s/%s", remote, branch)
    return True
