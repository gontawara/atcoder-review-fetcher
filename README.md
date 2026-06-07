# atcoder-review-fetcher

AtCoder Beginner Contest (ABC) の終了後に、問題文・公式解説を取得して
練習リポジトリに Markdown で保存し、コンテスト中に書いたローカルの提出コードと
あわせて git に commit / push する CLI ツール。

launchd で毎週土曜の深夜に自動実行し、翌朝には復習に必要な材料が
リポジトリに揃っている状態を作ることを目的とする。

## 動作の流れ

1. コンテストアーカイブから直近に終了した ABC を検出（`--latest`）
2. 各問題の問題文（日本語）を取得 → `problem.md`
3. 公式解説（日本語優先）を取得 → `editorial.md`
4. コンテスト中に書いたローカルコード（`main.py` など）の存在を記録
5. `contest.md`（サマリ兼復習チェックリスト）を生成
6. `contests/{contest_id}` を commit し、リモートに push

ログインは不要。取得するのはすべて公開ページのみで、
リクエスト間隔は 1.5 秒以上空ける（AtCoder のスクレイピングマナーに準拠）。

## 練習リポジトリの想定レイアウト

```
atcoder-practice/
└── contests/
    └── abc455/
        ├── contest.md      # 自動生成: サマリ・復習チェックリスト
        ├── a/
        │   ├── main.py     # コンテスト中に自分で書く
        │   ├── problem.md  # 自動生成
        │   └── editorial.md# 自動生成
        └── b/ ...
```

コンテスト中は `contests/{id}/{a..g}/main.py` にコードを書く運用にする。
既存ファイルは一切上書きしない（再実行しても安全）。

## セットアップ

```bash
uv sync
cp config.example.toml config.toml
# config.toml の practice_repo / username を確認
```

## 使い方

```bash
# 直近に終了した ABC を取得（max_age_hours 以内に開始したもののみ）
uv run abc-fetch --config config.toml --latest

# コンテストを明示指定
uv run abc-fetch --config config.toml --contest abc455

# git 操作なしで取得だけ試す
uv run abc-fetch --config config.toml --contest abc455 --no-git
```

`--latest` で対象がない場合（その日に ABC がなかった等）は何もせず正常終了する。
launchd に毎週登録しても ABC のない週は安全にスキップされる。

## テスト

```bash
uv run pytest
```

実際の AtCoder ページの HTML をフィクスチャとして
パーサー（アーカイブ・問題一覧・問題文・解説）を検証している。

## 設定 (config.toml)

| キー | 意味 | 既定値 |
|---|---|---|
| `atcoder.username` | AtCoder ユーザー名（記録用） | - |
| `atcoder.contest_prefix` | 対象コンテストの接頭辞 | `abc` |
| `paths.practice_repo` | 練習リポジトリの絶対パス | - |
| `fetch.request_interval_sec` | リクエスト間隔（秒） | `1.5` |
| `fetch.max_age_hours` | `--latest` の対象とする開始からの経過時間 | `12` |
| `fetch.editorial_lang` | 解説の言語 | `ja` |
| `git.enabled` / `git.push` | git 操作の有効化 | `true` |

## 既知の制約

- 提出コードのページは現在ログイン必須のため、自分の提出は取得しない。
  ローカルでコードを書く運用でカバーする（WA 提出の履歴は残らない）
- 解説放送（YouTube）と外部ブログのユーザー解説はリンクのみで本文は取得しない
- 公式解説が未公開の場合、その問題の `editorial.md` は作られない
  （後日 `--contest` で再実行すれば追加取得できる）
