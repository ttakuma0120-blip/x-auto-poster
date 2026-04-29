import json
import logging
import re
import time
from pathlib import Path
from typing import Optional

import feedparser

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
POSTED_FILE = BASE_DIR / "posted.json"

RSS_FEEDS = [
    {"name": "Anthropic Blog", "url": "https://www.anthropic.com/blog/rss.xml"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog/rss.xml"},
    {"name": "Google AI Blog", "url": "https://blog.google/technology/ai/rss/"},
]

MAX_RETRIES = 3
RETRY_DELAY = 2


def load_posted() -> list:
    if POSTED_FILE.exists():
        try:
            with open(POSTED_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"posted.json読み込みエラー: {e}")
    return []


def save_posted(posted: list) -> None:
    with open(POSTED_FILE, "w", encoding="utf-8") as f:
        json.dump(posted, f, ensure_ascii=False, indent=2)


def mark_as_posted(article_id: str) -> None:
    posted = load_posted()
    if article_id not in posted:
        posted.append(article_id)
        if len(posted) > 1000:
            posted = posted[-1000:]
        save_posted(posted)
        logger.info(f"投稿済みとしてマーク完了")


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _fetch_feed_entries(feed_url: str) -> Optional[list]:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            feed = feedparser.parse(feed_url)
            if feed.get("bozo") and not feed.entries:
                raise ValueError(f"Feed parse error: {feed.get('bozo_exception')}")
            return feed.entries
        except Exception as e:
            logger.warning(f"RSS取得失敗 (試行{attempt}/{MAX_RETRIES}): {feed_url} - {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    logger.error(f"RSS取得を{MAX_RETRIES}回試みて失敗。スキップします: {feed_url}")
    return None


def fetch_latest_article() -> Optional[dict]:
    posted = load_posted()

    for feed_info in RSS_FEEDS:
        entries = _fetch_feed_entries(feed_info["url"])
        if entries is None:
            continue

        for entry in entries[:10]:
            article_id = entry.get("id") or entry.get("link", "")
            if not article_id or article_id in posted:
                continue

            title = _strip_html(entry.get("title", ""))
            if not title:
                continue

            raw_summary = entry.get("summary") or entry.get("description") or ""
            summary = _strip_html(raw_summary)[:500]
            link = entry.get("link", "")

            logger.info(f"未投稿記事を発見: [{feed_info['name']}] {title[:60]}...")
            return {
                "id": article_id,
                "title": title,
                "summary": summary,
                "link": link,
                "source": feed_info["name"],
            }

    logger.warning("全フィードで未投稿の記事が見つかりませんでした")
    return None
