"""設定ファイル (TOML) の読み込み。"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """ツール全体の設定。config.toml から読み込む。"""

    username: str
    practice_repo: Path
    contest_prefix: str = "abc"
    request_interval_sec: float = 1.5
    max_age_hours: int = 12
    editorial_lang: str = "ja"
    git_enabled: bool = True
    git_push: bool = True
    git_remote: str = "origin"
    git_branch: str = "main"

    @classmethod
    def load(cls, path: Path) -> Config:
        with path.open("rb") as f:
            raw = tomllib.load(f)

        atcoder = raw.get("atcoder", {})
        paths = raw.get("paths", {})
        fetch = raw.get("fetch", {})
        git = raw.get("git", {})

        username = atcoder.get("username")
        practice_repo = paths.get("practice_repo")
        if not username:
            raise ValueError(f"{path}: [atcoder] username が未設定です")
        if not practice_repo:
            raise ValueError(f"{path}: [paths] practice_repo が未設定です")

        return cls(
            username=username,
            practice_repo=Path(practice_repo).expanduser(),
            contest_prefix=atcoder.get("contest_prefix", cls.contest_prefix),
            request_interval_sec=fetch.get(
                "request_interval_sec", cls.request_interval_sec
            ),
            max_age_hours=fetch.get("max_age_hours", cls.max_age_hours),
            editorial_lang=fetch.get("editorial_lang", cls.editorial_lang),
            git_enabled=git.get("enabled", cls.git_enabled),
            git_push=git.get("push", cls.git_push),
            git_remote=git.get("remote", cls.git_remote),
            git_branch=git.get("branch", cls.git_branch),
        )
