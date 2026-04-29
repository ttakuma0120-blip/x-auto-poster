# X 自動投稿システム

AI・テック系の最新情報をRSSから自動収集し、Claude APIで日本語の投稿文を生成してXに自動投稿するシステムです。

## 機能

- **RSSフィード自動収集**: Anthropic / OpenAI / Google AI / TechCrunch AI / Zenn から最新記事を取得
- **AI投稿文生成**: Claude API（claude-sonnet-4-6）でですます調の自然な投稿文を自動生成
- **凍結リスク対策**: 投稿時刻の±30分ランダムシフト、文体のゆらぎ、ハッシュタグローテーション
- **warm_upモード**: 最初の2週間は1日1回のみ投稿し、アカウント育成を安全に行う
- **重複防止**: `posted.json`で投稿済み記事を管理し、同じ記事を2度投稿しない
- **dry-runモード**: 実際には投稿せず、生成内容をコンソールで確認できる

---

## セットアップ手順

### 1. 必要なAPIキーの取得

#### X (Twitter) API
1. [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard) にアクセス
2. アプリを作成し、**OAuth 1.0a** を有効化（Read and Write権限）
3. 以下の4つのキーを取得:
   - API Key（Consumer Key）
   - API Secret（Consumer Secret）
   - Access Token
   - Access Token Secret

#### Anthropic API
1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. API Keys ページからキーを発行

---

### 2. 環境変数の設定

```bash
cd x_auto_poster
cp .env.example .env
```

`.env` ファイルを編集して各キーを設定します:

```env
X_API_KEY=取得したAPI Key
X_API_SECRET=取得したAPI Secret
X_ACCESS_TOKEN=取得したAccess Token
X_ACCESS_TOKEN_SECRET=取得したAccess Token Secret
ANTHROPIC_API_KEY=取得したAnthropicキー
```

---

### 3. 依存パッケージのインストール

```bash
cd x_auto_poster
pip install -r requirements.txt
```

Python 3.9 以上を推奨します。仮想環境を使う場合:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

### 4. 動作確認（dry-run）

実際には投稿せず、生成内容だけ確認できます:

```bash
cd x_auto_poster
python main.py --dry-run
```

出力例:
```
==================================================
[DRY RUN] 投稿内容 (118文字):
🚀 Anthropicが新しい推論モデルを発表しました！複雑な数学問題や長文の分析が格段に得意になったそうです。APIも公開されているので、早速使ってみたいですね。 #Claude
==================================================
```

---

### 5. 今すぐ投稿（テスト）

```bash
python main.py --post-now
```

---

### 6. スケジューラー起動（通常運用）

```bash
python main.py
```

プロセスが常駐し、以下のスケジュールで自動投稿します:

| モード | 朝 | 夜 |
|--------|----|----|
| warm_up（最初の2週間） | 7:30〜8:30 のランダムな時刻 | スキップ |
| 通常（2週間後〜） | 7:30〜8:30 のランダムな時刻 | 19:30〜20:30 のランダムな時刻 |

---

## ファイル構成

```
x_auto_poster/
├── main.py           # メイン実行・モード管理
├── fetcher.py        # RSSフィード取得・記事管理
├── generator.py      # Claude APIで投稿文生成
├── poster.py         # X API投稿
├── scheduler.py      # APSchedulerによるスケジュール管理
├── warm_up.py        # warm_upモード管理・開始日記録
├── .env              # APIキー（要作成、gitignore済み）
├── .env.example      # キーのサンプル
├── posted.json       # 投稿済み記事ID管理
├── state.json        # warm_upモード状態・最終ハッシュタグ
├── error.log         # エラーログ（自動生成）
└── requirements.txt
```

---

## クラウドへのデプロイ

### Render（推奨）

1. GitHubにリポジトリをプッシュ
2. [Render](https://render.com/) でアカウント作成
3. **New → Background Worker** を選択
4. GitHubリポジトリを接続
5. `render.yaml` が自動検出されます
6. Environment Variables に `.env` の内容を設定
7. **Create Background Worker** をクリック

> **注意（無料枠の制限）**: Renderの無料プランではデプロイのたびにファイルシステムがリセットされます。`posted.json`（投稿済み管理）と `state.json`（warm_up状態）が消えるため、**有料プランのDiskオプション**（月$0.25/GB〜）を使うか、Supabaseなどの外部DBへの移行を検討してください。

### Railway

1. [Railway](https://railway.app/) でアカウント作成
2. **New Project → Deploy from GitHub repo** を選択
3. リポジトリを接続（`Procfile` が自動検出されます）
4. **Variables** タブで `.env` の内容を設定
5. `TZ=Asia/Tokyo` も追加

---

## 凍結リスク対策の詳細

| 対策 | 実装 |
|------|------|
| 投稿時刻のランダムシフト | ±30分（APSchedulerのjitter機能） |
| warm_upモード | 最初の14日間は1日1回のみ |
| 文体のゆらぎ | Claudeが毎回異なる文字数・絵文字・構成を生成 |
| ハッシュタグローテーション | 直前と同じハッシュタグを使わないよう制御 |
| 重複投稿防止 | posted.jsonで記事URLをハッシュ管理 |

---

## トラブルシューティング

**RSSの取得に失敗する場合**
- `error.log` を確認してください
- 各フィードは3回リトライ後スキップします

**X APIの認証エラー**
- `.env` のキーが正しいか確認
- Twitter Developer Portal でアプリのPermissionsが **Read and Write** になっているか確認
- Access TokenはPermission変更後に再発行が必要な場合があります

**文字数が130文字を超える場合**
- Claude APIへのプロンプトで明示しているため通常は守られますが、稀に超過することがあります
- Xの上限（280文字）内なので投稿自体は問題ありません
