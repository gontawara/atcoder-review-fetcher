# HANDOFF: Claude Code で行うセットアップ手順

このファイルは、ユーザーの Mac 上で Claude Code に読ませて実行するための手順書。
ツール本体（コード・テスト）は実装・検証済み。ここでやるのは
**リポジトリ作成・依存インストール・launchd 登録・push 確認**のみ。

実行前提: `uv` と `git` がインストール済みで、GitHub への push 認証
（`gh auth login` または SSH キー）が通っていること。

パスの定義（以下で使用）:

- TOOL = `~/Documents/Claude/Projects/プログラミング/projects/atcoder-review-fetcher`
- PRACTICE = `~/Documents/Claude/Projects/プログラミング/atcoder-practice`

## 1. 練習リポジトリ（atcoder-practice）の作成

PRACTICE ディレクトリは README / .gitignore 作成済み。
**方針決定済み**: リポジトリは public。ただし問題文・解説・テストケース・
復習資料（problem.md / editorial.md / contest.md / test/ / review/）は
AtCoder の著作物および個人メモのため `.gitignore` でローカルのみとする
（設定済み。push されるのは自分のコードと acc 雛形だけ）。

```bash
cd $PRACTICE
git init -b main
git add .
git commit -m "[add]リポジトリ初期化"
gh repo create atcoder-practice --public --source=. --push
```

## 1.5. 過去分の移行（~/Documents/AtCoder）

`~/Documents/AtCoder` にある過去に解いたコードを
`$PRACTICE/contests/{contest_id}/{a..g}/` 形式へ移行する。

1. まず中身の構造を調べる（命名規則からコンテストIDと問題を判別）
2. 判別できたものを `contests/abc398/c/main.py` の形へコピー（元は消さない）
3. 判別できないファイルはユーザーに確認する
4. `git commit -m "[add]過去に解いた問題のコードを移行"` して push

過去分の problem.md / editorial.md の一括取得は**行わない**
（サーバー負荷への配慮。復習するコンテストだけ後から
`uv run abc-fetch --config config.toml --contest abc398` で個別取得する）。

## 1.6. acc / oj の確認（任意・ユーザーに使うか確認）

ユーザーは acc（atcoder-cli）でコンテスト雛形を生成する想定。
acc が作るタスクフォルダ名が `a, b, c...`（小文字）になるよう設定を確認する。
設定キーは acc の公式 README（https://github.com/Tatamo/atcoder-cli）を
一次情報として参照すること。`acc new` の実行先は `$PRACTICE/contests/` 直下。

## 2. ツールリポジトリ（atcoder-review-fetcher）のセットアップ

```bash
cd $TOOL
uv sync
cp config.example.toml config.toml
# config.toml の practice_repo が PRACTICE の絶対パスと一致しているか確認

uv run pytest          # 14 件パスすること
```

```bash
git init -b main
git add .
git commit -m "[add]ABC復習用フェッチャーを実装"
gh repo create atcoder-review-fetcher --public --source=. --push
```

## 3. 動作確認（実際に1コンテスト取得して push）

```bash
cd $TOOL
uv run abc-fetch --config config.toml --contest abc460
```

成功すると PRACTICE に `contests/abc460/` が作られる。
problem.md / editorial.md はローカルに生成されるが .gitignore により
push されない（コードがあればコードのみ commit / push される）。
GitHub 上に取得物が**載っていない**ことも確認すること。

## 4. 自動実行の登録（このリポでは作業なし）

**方針変更（2026-06-07確定）**: launchd / pmset は使わない。
自動実行は Claude デスクトップアプリのローカルスケジュールタスクで行う
（毎週土曜 23:30。スリープ中はスキップされ、起床時に1回分だけ補完実行される。
公式: https://code.claude.com/docs/en/desktop-scheduled-tasks の Missed runs 参照）。

タスクの登録はセットアップ完了後に Cowork 側で行うため、
**ここでは何もしなくてよい**。以下の旧手順（launchd / pmset）は実行しないこと。

<details>
<summary>旧手順（不採用・参考のみ）</summary>

### launchd 登録（毎週土曜 23:30）

`~/Library/LaunchAgents/com.gontawara.abc-fetch.plist` を作成する。
**パスはすべて絶対パスに展開すること**（launchd は `~` や PATH を解決しない）。

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.gontawara.abc-fetch</string>
    <key>ProgramArguments</key>
    <array>
        <string>{TOOL絶対パス}/.venv/bin/abc-fetch</string>
        <string>--config</string>
        <string>{TOOL絶対パス}/config.toml</string>
        <string>--latest</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{TOOL絶対パス}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>6</integer>
        <key>Hour</key>
        <integer>23</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{TOOL絶対パス}/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>{TOOL絶対パス}/launchd.log</string>
</dict>
</plist>
```

登録と手動テスト:

```bash
launchctl load ~/Library/LaunchAgents/com.gontawara.abc-fetch.plist
launchctl start com.gontawara.abc-fetch   # 即時実行テスト
cat {TOOL絶対パス}/launchd.log            # 「対象外」ログが出れば正常
```

注意点:

- `.venv/bin/abc-fetch` は `uv sync` 後に存在する。先に手順2を終えること
- launchd の仕様・キーの意味は `man launchd.plist` を一次情報として確認すること
- launchd.log は .gitignore に追加すること

### スリープへの対処（旧方針）

**ユーザーの要件は「夜間に中断なく実行されること」**。launchd 単体では
スリープ中の実行が起床時まで延期されるため、毎週土曜 23:25 に
自動起床するよう設定する:

```bash
sudo pmset repeat wakeorpoweron S 23:25:00   # S = 土曜
pmset -g sched                                # 登録確認
```

注意（`man pmset` を一次情報として確認すること）:

- 管理者権限が必要。実行前にユーザーに確認する
- ノート型は**電源アダプタ接続時のみ**スケジュール起床が確実。
  土曜夜は電源をつないで寝るようユーザーに伝える
- クラムシェル（蓋閉じ）状態での挙動は環境依存のため、
  初回は蓋を開けたまま（ディスプレイスリープのみ）で検証する

**検証手順**: 設定後、近い時刻（例: 5分後）に一時的な
wakeorpoweron + launchctl start で実際にスリープ→起床→実行→
launchd.log 出力までを通しで確認し、確認後に本来の土曜設定へ戻す。

</details>

## 5. 完了後

Cowork（このプロジェクト）に戻って「セットアップ完了」と伝えること。
スケジュールタスク（土23:30: abc-fetch 実行→復習準備の生成）の登録は
Cowork 側で行う。
