"""AtCoder の HTML を Markdown に変換する。

AtCoder 固有のマークアップ:
- 問題文の数式は ``<var>N \\leq 10^5</var>`` 形式
- 解説の数式はテキスト中の ``\\(...\\)`` / ``\\[...\\]`` 形式
どちらも GitHub で描画できる ``$...$`` / ``$$...$$`` に統一する。
"""

from __future__ import annotations

import re
from typing import Any

from bs4 import Tag
from markdownify import MarkdownConverter


class AtCoderConverter(MarkdownConverter):
    """AtCoder 向けカスタム変換。

    markdownify はバージョンにより convert_* の引数が異なるため、
    el, text 以外は可変長で受ける。
    """

    def convert_var(self, el: Tag, text: str, *args: Any, **kwargs: Any) -> str:
        return f"${text.strip()}$"

    def convert_pre(self, el: Tag, text: str, *args: Any, **kwargs: Any) -> str:
        code = el.get_text()
        lang = ""
        code_el = el.find("code")
        if isinstance(code_el, Tag):
            classes = code_el.get("class") or []
            for cls in classes:
                if cls.startswith("language-"):
                    lang = cls.removeprefix("language-")
                    break
        return f"\n```{lang}\n{code.rstrip()}\n```\n"


_converter = AtCoderConverter(heading_style="ATX", bullets="-")

_INLINE_MATH = re.compile(r"\\\((.+?)\\\)", re.S)
_BLOCK_MATH = re.compile(r"\\\[(.+?)\\\]", re.S)
_EXCESS_NEWLINES = re.compile(r"\n{3,}")


def to_markdown(element: Tag) -> str:
    """HTML 要素を Markdown 文字列に変換する。"""
    md = _converter.convert_soup(element)
    md = _INLINE_MATH.sub(lambda m: f"${m.group(1).strip()}$", md)
    md = _BLOCK_MATH.sub(lambda m: f"$${m.group(1).strip()}$$", md)
    md = _EXCESS_NEWLINES.sub("\n\n", md)
    return md.strip() + "\n"
