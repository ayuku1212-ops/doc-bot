# 資料Bot セットアップ手順（初心者向け）

## 全体の流れ（30〜60分）

```
Step 1: Slack Appを作る         （15分）
Step 2: Google Drive APIを設定  （15分）
Step 3: Railwayにデプロイ       （10分）
Step 4: 動作確認                （5分）
```

---

## Step 1: Slack Appを作る

### 1-1. Slack APIページを開く

ブラウザで以下にアクセス（Slackにログインした状態で）
👉 https://api.slack.com/apps

右上の「**Create New App**」をクリック

---

### 1-2. Appの基本設定

「**From scratch**」を選択

- **App Name**: `資料Bot`（なんでもOK）
- **Pick a workspace**: `株式会社REJUVENATE` のワークスペースを選択

「**Create App**」をクリック

---

### 1-3. Bot Token Scopesを設定

左メニュー「**OAuth & Permissions**」をクリック

下にスクロールして「**Bot Token Scopes**」を見つける
「**Add an OAuth Scope**」をクリックして以下を3つ追加:

| 追加するScope | 説明 |
|-------------|------|
| `channels:history` | チャンネルのメッセージを読む |
| `chat:write` | メッセージを送る |
| `reactions:write` | リアクション（絵文字）をつける |

---

### 1-4. Socket Modeを有効にする

左メニュー「**Socket Mode**」をクリック

「**Enable Socket Mode**」をオンにする

トークン名を聞かれる → 「`my-token`」など何でもOK → 「**Generate**」

**⚠️ ここで表示されるトークン（xapp-から始まる）をコピーしてメモ帳に保存**
→ これが `SLACK_APP_TOKEN`

---

### 1-5. Event Subscriptionsを設定

左メニュー「**Event Subscriptions**」をクリック

「**Enable Events**」をオンにする

下にある「**Subscribe to bot events**」を開く
「**Add Bot User Event**」をクリック → `message.channels` を追加

右下「**Save Changes**」をクリック

---

### 1-6. アプリをワークスペースにインストール

左メニュー「**OAuth & Permissions**」をクリック

上部の「**Install to Workspace**」をクリック → 「**許可する**」

**⚠️ 表示される「Bot User OAuth Token」（xoxb-から始まる）をコピーしてメモ帳に保存**
→ これが `SLACK_BOT_TOKEN`

---

## Step 2: Google Drive APIを設定

### 2-1. Google Cloud Consoleを開く

👉 https://console.cloud.google.com

Googleアカウントでログイン（会社のGoogleアカウント推奨）

---

### 2-2. プロジェクトを作成

上部の「**プロジェクトを選択**」→「**新しいプロジェクト**」

- プロジェクト名: `rejuvenate-doc-bot`
- 「**作成**」をクリック

作成後、そのプロジェクトが選択されているか確認（上部に名前が表示される）

---

### 2-3. Google Drive APIを有効化

左メニュー「**APIとサービス**」→「**ライブラリ**」

検索欄に「**Google Drive API**」と入力 → 出てきたらクリック

「**有効にする**」をクリック

---

### 2-4. サービスアカウントを作成

左メニュー「**APIとサービス**」→「**認証情報**」

上部「**認証情報を作成**」→「**サービスアカウント**」

- サービスアカウント名: `doc-bot`
- 「**作成して続行**」→「**完了**」

---

### 2-5. サービスアカウントのキー（JSON）をダウンロード

「認証情報」ページに戻る

作成した `doc-bot` のサービスアカウントをクリック

上部タブ「**キー**」→「**鍵を追加**」→「**新しい鍵を作成**」

「**JSON**」を選択 →「**作成**」

**⚠️ JSONファイルが自動でダウンロードされる。このファイルをメモ帳などで開いて中身を全部コピー**
→ これが `GOOGLE_SERVICE_ACCOUNT_JSON`

---

### 2-6. Google Driveのフォルダをサービスアカウントと共有

**⚠️ これが最重要。やらないとBotがファイルを見つけられない。**

ダウンロードしたJSONファイルをメモ帳で開いて
`"client_email"` の値（xxxx@xxxx.iam.gserviceaccount.comというメールアドレス）をコピー

Google Driveを開く
→ Botに検索させたいフォルダを右クリック
→「**共有**」
→ 上記のメールアドレスを入力して「**閲覧者**」として追加
→「**送信**」

---

## Step 3: Railwayにデプロイ

### 3-1. GitHubにコードをプッシュ

まずこのフォルダ（`doc-bot`）をGitHubにアップロードする必要がある。

**GitHubアカウントがない場合:**
👉 https://github.com でアカウント作成（無料）

**リポジトリを作成:**
GitHubで「**New repository**」→ 名前: `rejuvenate-doc-bot` → 「**Create repository**」

**コードをアップロード（ターミナルで）:**
```bash
cd /Users/nakajimaayumiki/REJUVENATE/tools/doc-bot
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/あなたのユーザー名/rejuvenate-doc-bot.git
git push -u origin main
```

---

### 3-2. Railwayでデプロイ

👉 https://railway.app にアクセス

「**Login with GitHub**」でログイン

「**New Project**」→「**Deploy from GitHub repo**」

先ほど作った `rejuvenate-doc-bot` を選択

---

### 3-3. 環境変数を設定

デプロイしたプロジェクトをクリック
→「**Variables**」タブ

以下を1つずつ「**+ Add Variable**」で追加:

| 変数名 | 値 |
|--------|-----|
| `SLACK_BOT_TOKEN` | xoxb-... （Step1-6でメモしたもの） |
| `SLACK_APP_TOKEN` | xapp-... （Step1-4でメモしたもの） |
| `ANTHROPIC_API_KEY` | sk-ant-... （Claudeの APIキー） |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | JSONファイルの中身を全部貼り付け |

---

### 3-4. スタートコマンドを設定

「**Settings**」タブ → 「**Start Command**」に以下を入力:

```
python bot.py
```

---

### 3-5. デプロイ確認

「**Deployments**」タブを開く
ログに `⚡ 資料Botが起動しました` と表示されればOK

---

## Step 4: Slackチャンネルを作成して動作確認

### 4-1. Slackチャンネルを作る

Slackで新しいチャンネルを作成
- チャンネル名: `#資料bot`（なんでもOK）
- 公開チャンネルでOK

### 4-2. BotをInvite

チャンネル内で以下を投稿:
```
/invite @資料Bot
```

### 4-3. テスト

チャンネルに以下を投稿して試す:
```
ReViNaのロゴ送って
```
```
FC加盟契約書
```
```
料金表ください
```

ファイルのリンクが返ってきたら成功 🎉

---

## うまくいかないときのチェックリスト

| 症状 | 確認箇所 |
|------|---------|
| Botが反応しない | BotをチャンネルにInviteしたか |
| 「エラーが発生しました」と出る | RailwayのログでエラーメッセージをClaude Codeに貼る |
| ファイルが見つからないと出る | Google DriveのフォルダをサービスアカウントのメールアドレスとShare済みか |
| Railwayのデプロイが失敗する | 環境変数が正しく設定されているか |

---

## 詰まったら

Claude Codeに「〇〇のところで詰まった」と言えばその場でサポートします。
