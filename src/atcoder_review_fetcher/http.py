"""AtCoder への HTTP アクセス（レート制限付き）。"""

from __future__ import annotations

import logging
import time

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://atcoder.jp"
USER_AGENT = (
    "abc-review-fetcher/0.1 (personal study tool; +https://github.com/gontawara)"
)


class AtCoderClient:
    """リクエスト間隔を強制する AtCoder 用クライアント。

    AtCoder はスクレイピング時にリクエスト間隔を空けることを求めているため、
    どのページ取得でも最低 ``interval_sec`` 秒の間隔を保証する。
    """

    def __init__(self, interval_sec: float = 1.5, timeout_sec: float = 30.0) -> None:
        self._interval = interval_sec
        self._timeout = timeout_sec
        self._last_request_at = 0.0
        self._session = requests.Session()
        self._session.headers["User-Agent"] = USER_AGENT

    def get(self, path: str) -> str:
        """``/contests/...`` 形式のパスを取得して HTML を返す。"""
        self._wait_interval()
        url = f"{BASE_URL}{path}"
        logger.info("GET %s", url)
        resp = self._session.get(url, timeout=self._timeout)
        self._last_request_at = time.monotonic()
        resp.raise_for_status()
        if "/login" in resp.url:
            raise RuntimeError(
                f"{url} はログインが必要なページにリダイレクトされました"
            )
        return resp.text

    def _wait_interval(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self._interval:
            time.sleep(self._interval - elapsed)
