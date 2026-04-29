import logging
import os
from pathlib import Path

import tweepy
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
logger = logging.getLogger(__name__)


def post_tweet(text: str, dry_run: bool = False) -> bool:
    if dry_run:
        separator = "=" * 50
        print(f"\n{separator}")
        print(f"[DRY RUN] 投稿内容 ({len(text)}文字):")
        print(text)
        print(f"{separator}\n")
        logger.info(f"[DRY RUN] {len(text)}文字の投稿文を生成しました")
        return True

    client = tweepy.Client(
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
    )
    response = client.create_tweet(text=text)
    tweet_id = response.data["id"]
    logger.info(f"投稿成功 - Tweet ID: {tweet_id}")
    return True
