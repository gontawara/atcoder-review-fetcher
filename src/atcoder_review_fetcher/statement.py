"""問題一覧・問題文の取得とパース。"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

from .markdown import to_markdown


@dataclass(frozen=True)
class TaskRef:
    letter: str  # "a", "b", ...
    slug: str  # "abc407_c"
    title: str  # "Security 2"

    @property
    def path(self) -> str:
        contest_id = self.slug.rsplit("_", 1)[0]
        return f"/contests/{contest_id}/tasks/{self.slug}"


def parse_task_list(html: str, contest_id: str) -> list[TaskRef]:
    """``/contests/{id}/tasks`` のテーブルから問題一覧を得る。"""
    soup = BeautifulSoup(html, "html.parser")
    pattern = re.compile(rf"^/contests/{re.escape(contest_id)}/tasks/(\w+)$")
    tasks: dict[str, TaskRef] = {}
    for row in soup.select("table tbody tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        letter_link = cells[0].find("a", href=pattern)
        title_link = cells[1].find("a", href=pattern)
        if letter_link is None or title_link is None:
            continue
        match = pattern.match(letter_link["href"])
        assert match is not None
        slug = match.group(1)
        if slug not in tasks:
            tasks[slug] = TaskRef(
                letter=letter_link.get_text(strip=True).lower(),
                slug=slug,
                title=title_link.get_text(strip=True),
            )
    return list(tasks.values())


def parse_statement(html: str, lang: str = "ja") -> str:
    """問題ページから指定言語の問題文を Markdown で返す。"""
    soup = BeautifulSoup(html, "html.parser")
    statement = soup.select_one("#task-statement")
    if statement is None:
        raise ValueError("#task-statement が見つかりません")
    target: Tag | None = statement.select_one(f"span.lang-{lang}")
    if target is None:
        target = statement  # 言語別 span がない古い形式
    return to_markdown(target)
