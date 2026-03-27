import os
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ── 初期化 ──────────────────────────────────────────────
app = App(token=os.environ["SLACK_BOT_TOKEN"])

# Claude APIキーが設定されている場合のみ使用
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
claude = None
if ANTHROPIC_API_KEY:
    import anthropic
    claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")  # 任意：検索対象フォルダを絞る場合


# ── Google Drive ─────────────────────────────────────────
def get_drive_service():
    creds = service_account.Credentials.from_service_account_info(
        json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]),
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds)


def search_drive(keywords: list[str]) -> list[dict]:
    service = get_drive_service()

    name_conditions = " or ".join([f"name contains '{kw}'" for kw in keywords])
    query = f"({name_conditions}) and trashed=false"
    if DRIVE_FOLDER_ID:
        query += f" and '{DRIVE_FOLDER_ID}' in parents"

    result = service.files().list(
        q=query,
        spaces="drive",
        fields="files(id, name, mimeType, webViewLink, modifiedTime)",
        pageSize=8,
        orderBy="modifiedTime desc",
    ).execute()

    return result.get("files", [])


# ── キーワード抽出 ────────────────────────────────────────
# ブランド名の表記ゆれ対応
BRAND_MAP = {
    "リビナ": "ReViNa", "revina": "ReViNa", "れびな": "ReViNa",
    "リミット": "LIMIT", "limit": "LIMIT",
    "リアライズ": "REALIZE", "realize": "REALIZE",
}

def extract_keywords(user_message: str) -> list[str]:
    # Claude APIが使える場合は賢く抽出
    if claude:
        try:
            response = claude.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": f"""社内のSlackで以下のメッセージが送られました。
Google Driveのファイル名を検索するための日本語キーワードを1〜4個抽出してください。

メッセージ:「{user_message}」

ブランド名の対応:
- revina / ReViNa / リビナ → ReViNa
- limit / LIMIT → LIMIT
- realize / REALIZE / リアライズ → REALIZE

JSON配列だけ返してください（例: ["ReViNa", "ロゴ"]）""",
                }],
            )
            return json.loads(response.content[0].text)
        except Exception:
            pass

    # APIなし：シンプルにメッセージをそのまま検索キーワードに
    msg = user_message.lower()
    keywords = []
    for k, v in BRAND_MAP.items():
        if k in msg:
            keywords.append(v)
    # 不要な語を除いてキーワード化
    stop_words = ["送って", "ください", "くれ", "ちょうだい", "教えて", "見せて", "ほしい", "お願い", "の", "を", "で", "が", "は"]
    words = user_message
    for w in stop_words:
        words = words.replace(w, " ")
    keywords += [w.strip() for w in words.split() if len(w.strip()) > 1]
    return list(dict.fromkeys(keywords))[:4] or [user_message]


# ── ファイル種別アイコン ──────────────────────────────────
def get_icon(mime_type: str) -> str:
    icons = {
        "application/pdf": "📄",
        "application/vnd.google-apps.document": "📝",
        "application/vnd.google-apps.spreadsheet": "📊",
        "application/vnd.google-apps.presentation": "📊",
        "image/png": "🖼️",
        "image/jpeg": "🖼️",
        "image/svg+xml": "🖼️",
    }
    return icons.get(mime_type, "📁")


# ── Slackメッセージハンドラ ──────────────────────────────
@app.message("")
def handle_message(message, say, client):
    # Bot自身のメッセージは無視
    if message.get("bot_id") or message.get("subtype"):
        return

    user_text = message.get("text", "").strip()
    if not user_text:
        return

    channel = message["channel"]
    ts = message["ts"]

    # 検索中リアクション
    client.reactions_add(channel=channel, timestamp=ts, name="mag")

    try:
        keywords = extract_keywords(user_text)
        files = search_drive(keywords)
    except Exception as e:
        client.reactions_remove(channel=channel, timestamp=ts, name="mag")
        say(f"エラーが発生しました: {e}")
        return

    client.reactions_remove(channel=channel, timestamp=ts, name="mag")

    if not files:
        say(
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":search: `{' / '.join(keywords)}` に一致するファイルが見つかりませんでした。\nキーワードを変えてみてください。",
                    },
                }
            ]
        )
        return

    # 結果を整形
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":file_folder: *{len(files)}件* 見つかりました（検索: `{'` `'.join(keywords)}`）",
            },
        },
        {"type": "divider"},
    ]

    for f in files:
        icon = get_icon(f["mimeType"])
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{icon} <{f['webViewLink']}|{f['name']}>",
                },
            }
        )

    say(blocks=blocks)


# ── 起動 ─────────────────────────────────────────────────
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    print("⚡ 資料Botが起動しました")
    handler.start()
