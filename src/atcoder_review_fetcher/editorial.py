"""解説一覧・解説本文の取得とパース。"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

from .markdown import to_markdown


@dataclass(frozen=True)
class EditorialLink:
    path: str  # "/contests/abc407/editorial/13105"
    label: str  # "解説", "Editorial", "ユーザ解説" など
    official: bool


def parse_editorial_index(html: str, contest_id: str) -> dict[str, list[EditorialLink]]:
    """``/contests/{id}/editorial`` から問題スラッグ→解説リンク一覧の辞書を返す。

    解説放送などの外部リンク（``/jump?url=...``）は除外する。
    """
    soup = BeautifulSoup(html, "html.parser")
    task_pattern = re.compile(rf"^/contests/{re.escape(contest_id)}/tasks/(\w+)$")
    editorial_pattern = re.compile(
        rf"^/contests/{re.escape(contest_id)}/editorial/\d+$"
    )

    result: dict[str, list[EditorialLink]] = {}
    for heading in soup.find_all("h3"):
        task_link = heading.find("a", href=task_pattern)
        if task_link is None:
            continue
        match = task_pattern.match(task_link["href"])
        assert match is not None
        slug = match.group(1)

        section = heading.find_next_sibling("div", class_="editorial-section")
        if section is None:
            continue
        links: list[EditorialLink] = []
        for item in section.find_all("li"):
            anchor = item.find("a", href=editorial_pattern)
            if anchor is None:
                continue
            label_el = item.find("span", class_="label")
            links.append(
                EditorialLink(
                    path=anchor["href"],
                    label=anchor.get_text(strip=True),
                    official=label_el is not None
                    and "Official" in label_el.get_text(),
                )
            )
        result[slug] = links
    return result


def choose_editorial(
    links: list[EditorialLink], lang: str = "ja"
) -> EditorialLink | None:
    """公式解説を優先して 1 件選ぶ。

    優先順: 公式かつ指定言語（ja=解説 / en=Editorial）→ 公式 → 先頭。
    """
    if not links:
        return None
    preferred_label = "解説" if lang == "ja" else "Editorial"
    for link in links:
        if link.official and link.label == preferred_label:
            return link
    for link in links:
        if link.official:
            return link
    return links[0]


def parse_editorial_body(html: str) -> tuple[str, str]:
    """解説個別ページから (タイトル, 本文 Markdown) を返す。

    本文は ``div.col-sm-12`` 内の ``<hr>`` より後ろの要素。
    """
    soup = BeautifulSoup(html, "html.parser")
    container = None
    for candidate in soup.select("#main-container div.col-sm-12"):
        if candidate.find("h2") is not None:
            container = candidate
            break
    if container is None:
        raise ValueError("解説本文のコンテナが見つかりません")

    title_el = container.find("h2")
    assert isinstance(title_el, Tag)
    title = " ".join(title_el.get_text(" ", strip=True).split())

    hr = container.find("hr")
    if hr is None:
        raise ValueError("解説本文の区切り <hr> が見つかりません")

    parts: list[str] = []
    for sibling in hr.find_next_siblings():
        if isinstance(sibling, Tag):
            parts.append(to_markdown(sibling))
    return title, "\n".join(parts).strip() + "\n"
