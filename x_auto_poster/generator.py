import json
import logging
import os
import random
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "state.json"

HASHTAGS = ["#AI", "#生成AI", "#ChatGPT", "#Claude"]

SYSTEM_PROMPT = """あなたはAI・テック情報をわかりやすく広める発信者です。
AIに詳しくない人にも届くよう、以下のルールで投稿文を作成してください：

【文体ルール】
- 必ず「ですます調」で書く
- 語尾の例：「〜です！」「〜ました！」「〜しています。」「〜できます！」「〜でしょうか？」
- 友達に話しかけるような親しみやすいトーンで
- 専門用語は使わず、中学生でも理解できる言葉に言い換える
- 「私たちの生活にどう関係するか」が伝わる書き方にする

【構成ルール】
- 日本語で80〜100文字（URLが別途付くため短めにする）
- 書き出しの絵文字は毎回異なるものを使う
- 「これが何の役に立つのか」「何がすごいのか」を一言で伝える
- 読んだ人が「これは知らなかった！」「シェアしたい！」と思えるような内容にする
- ハッシュタグは指定されたものを文末に1つだけ付ける
- URLは含めない（別途追加されます）

【良い投稿文の例】
「🤖 OpenAIが新モデルを発表しました！難しい質問への回答精度が大幅アップ。勉強や仕事の調べものがもっと楽になりそうです。 #AI」

「✨ Googleが画像を自動で作るAIを強化しましたよ！文章を入力するだけで写真みたいな画像が作れます。デザインの素人でも使えそう！ #生成AI」"""


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _pick_hashtag() -> str:
    state = _load_state()
    last_hashtag = state.get("last_hashtag", "")
    available = [h for h in HASHTAGS if h != last_hashtag]
    return random.choice(available)


def _save_last_hashtag(hashtag: str) -> None:
    state = _load_state()
    state["last_hashtag"] = hashtag
    _save_state(state)


def generate_post(article: dict) -> str:
    hashtag = _pick_hashtag()

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    user_message = (
        f"以下の記事を元に投稿文を作成してください。\n"
        f"ハッシュタグは「{hashtag}」を文末に使用してください。\n\n"
        f"記事タイトル：{article['title']}\n"
        f"記事概要：{article['summary']}\n"
        f"情報ソース：{article['source']}\n\n"
        f"投稿文のみを出力してください。説明や前置き・引用符は不要です。"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    post_text = response.content[0].text.strip()
    _save_last_hashtag(hashtag)

    # URLを末尾に追加（X上ではt.coで自動短縮される）
    if article.get("link"):
        post_text = f"{post_text}\n{article['link']}"

    return post_text
