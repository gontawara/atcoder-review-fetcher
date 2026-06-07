"""CLI エントリポイント。

使い方:
    abc-fetch --config config.toml --latest    # 直近に終了した ABC を取得
    abc-fetch --config config.toml --contest abc455
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import archive, editorial, gitops, statement, writer
from .config import Config
from .http import BASE_URL, AtCoderClient

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="abc-fetch",
        description="ABC終了後に問題文・公式解説を取得しgitにコミットする",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.toml"),
        help="設定ファイルのパス (default: ./config.toml)",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--latest",
        action="store_true",
        help="直近に終了した ABC を自動検出して取得する",
    )
    group.add_argument(
        "--contest",
        help="コンテスト ID を明示指定する (例: abc455)",
    )
    parser.add_argument(
        "--no-git",
        action="store_true",
        help="git commit/push を行わない",
    )
    return parser


def resolve_contest(
    client: AtCoderClient, config: Config, args: argparse.Namespace
) -> tuple[str, str] | None:
    """(contest_id, title) を返す。対象がなければ None。"""
    if args.contest:
        return args.contest, args.contest.upper()

    html = client.get(archive.ARCHIVE_PATH)
    ref = archive.parse_latest_contest(html, prefix=config.contest_prefix)
    if ref is None:
        logger.warning("アーカイブに %s が見つかりません", config.contest_prefix)
        return None
    age = datetime.now(JST) - ref.start_at
    if age > timedelta(hours=config.max_age_hours):
        logger.info(
            "最新の %s は %s 開始 (%.1f 時間前) で対象外です",
            ref.contest_id,
            ref.start_at.isoformat(timespec="minutes"),
            age.total_seconds() / 3600,
        )
        return None
    return ref.contest_id, ref.title


def fetch_contest(
    client: AtCoderClient, config: Config, contest_id: str
) -> list[writer.ProblemBundle]:
    tasks_html = client.get(f"/contests/{contest_id}/tasks")
    tasks = statement.parse_task_list(tasks_html, contest_id)
    if not tasks:
        raise RuntimeError(f"{contest_id} の問題一覧を取得できませんでした")
    logger.info("%s: %d 問を検出", contest_id, len(tasks))

    editorial_index: dict[str, list[editorial.EditorialLink]] = {}
    try:
        index_html = client.get(f"/contests/{contest_id}/editorial")
        editorial_index = editorial.parse_editorial_index(index_html, contest_id)
    except Exception:
        logger.warning("解説一覧の取得に失敗（未公開の可能性）", exc_info=True)

    bundles: list[writer.ProblemBundle] = []
    for task in tasks:
        bundle = writer.ProblemBundle(
            letter=task.letter, slug=task.slug, title=task.title
        )
        target_dir = writer.problem_dir(config.practice_repo, contest_id, task.letter)

        if not (target_dir / "problem.md").exists():
            try:
                bundle.statement_md = statement.parse_statement(
                    client.get(task.path), lang=config.editorial_lang
                )
            except Exception:
                logger.error("%s: 問題文の取得に失敗", task.slug, exc_info=True)

        if not (target_dir / "editorial.md").exists():
            link = editorial.choose_editorial(
                editorial_index.get(task.slug, []), lang=config.editorial_lang
            )
            if link is not None:
                try:
                    _, body = editorial.parse_editorial_body(client.get(link.path))
                    bundle.editorial_md = body
                    bundle.editorial_url = f"{BASE_URL}{link.path}"
                except Exception:
                    logger.error("%s: 解説の取得に失敗", task.slug, exc_info=True)

        bundle.local_solutions = writer.collect_local_solutions(
            config.practice_repo, contest_id, task.letter
        )
        bundles.append(bundle)
    return bundles


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    args = build_parser().parse_args(argv)

    try:
        config = Config.load(args.config)
    except (OSError, ValueError) as exc:
        logger.error("設定の読み込みに失敗: %s", exc)
        return 1

    client = AtCoderClient(interval_sec=config.request_interval_sec)

    resolved = resolve_contest(client, config, args)
    if resolved is None:
        logger.info("取得対象のコンテストがないため終了します")
        return 0
    contest_id, contest_title = resolved

    try:
        bundles = fetch_contest(client, config, contest_id)
    except Exception as exc:
        logger.error("取得に失敗: %s", exc)
        return 1

    written = 0
    for bundle in bundles:
        written += len(writer.write_problem(config.practice_repo, contest_id, bundle))
    writer.write_contest_index(
        config.practice_repo,
        contest_id,
        contest_title,
        bundles,
        fetched_at=datetime.now(JST),
    )
    logger.info("%s: %d ファイルを書き出しました", contest_id, written)

    if config.git_enabled and not args.no_git:
        try:
            gitops.commit_and_push(
                config.practice_repo,
                contest_id,
                push=config.git_push,
                remote=config.git_remote,
                branch=config.git_branch,
            )
        except RuntimeError as exc:
            logger.error("%s", exc)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
