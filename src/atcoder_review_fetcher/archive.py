"""コンテストアーカイブページから直近の ABC を特定する。

https://atcoder.jp/contests/archive?ratedType=1 は「終了済み」の
Rated ～1999 コンテストを新しい順に列挙するため、先頭から
URL スラッグが ``abc\\d+`` の行を探せば最新の終了済み ABC が得られる。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from bs4 import BeautifulSoup

ARCHIVE_PATH = "/contests/archive?ratedType=1"
_TIME_FORMAT = "%Y-%m-%d %H:%M:%S%z"


@dataclass(frozen=True)
class ContestRef:
    contest_id: str
    title: str
    start_at: datetime


def parse_latest_contest(html: str, prefix: str = "abc") -> ContestRef | None:
    """アーカイブ HTML から最新の終了済みコンテストを返す。見つからなければ None。"""
    soup = BeautifulSoup(html, "html.parser")
    pattern = re.compile(rf"^/contests/({re.escape(prefix)}\d+)$")
    for row in soup.select("table tbody tr"):
        link = row.find("a", href=pattern)
        if link is None:
            continue
        match = pattern.match(link["href"])
        assert match is not None
        time_el = row.select_one("time")
        if time_el is None:
            continue
        start_at = datetime.strptime(time_el.get_text(strip=True), _TIME_FORMAT)
        return ContestRef(
            contest_id=match.group(1),
            title=link.get_text(strip=True),
            start_at=start_at,
        )
    return None
