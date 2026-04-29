import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure imports resolve from this file's directory
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

BASE_DIR = Path(__file__).parent


def setup_logging() -> None:
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    file_handler = logging.FileHandler(BASE_DIR / "error.log", encoding="utf-8")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(logging.Formatter(log_format))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def run_post(dry_run: bool = False) -> bool:
    from fetcher import fetch_latest_article, mark_as_posted
    from generator import generate_post
    from poster import post_tweet
    from warm_up import get_days_remaining, is_warm_up_mode

    logger = logging.getLogger(__name__)

    warm_up = is_warm_up_mode()
    if warm_up:
        logger.info(f"モード: warm_up (残り{get_days_remaining()}日で通常モードへ移行)")
    else:
        logger.info("モード: 通常 (1日2回投稿)")

    article = fetch_latest_article()
    if not article:
        logger.error("投稿可能な記事が見つかりませんでした")
        return False

    logger.info(f"記事取得: [{article['source']}] {article['title']}")

    try:
        post_text = generate_post(article)
    except Exception as e:
        logger.error(f"投稿文の生成に失敗しました: {e}")
        return False

    logger.info(f"生成した投稿文 ({len(post_text)}文字):\n{post_text}")

    try:
        success = post_tweet(post_text, dry_run=dry_run)
        if success and not dry_run:
            mark_as_posted(article["id"])
        return success
    except Exception as e:
        logger.error(f"X APIへの投稿に失敗しました: {e}")
        return False


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="X自動投稿システム")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="投稿せずに生成内容をコンソールで確認するモード",
    )
    parser.add_argument(
        "--post-now",
        action="store_true",
        help="スケジュールを無視して今すぐ投稿する",
    )
    args = parser.parse_args()

    from warm_up import initialize_state

    initialize_state()

    if args.dry_run or args.post_now:
        mode = "dry-run" if args.dry_run else "即時投稿"
        logger.info(f"--- {mode}モード ---")
        success = run_post(dry_run=args.dry_run)
        sys.exit(0 if success else 1)

    from scheduler import start_scheduler

    logger.info("スケジューラーを起動します (Ctrl+C で停止)")
    start_scheduler(run_post)


if __name__ == "__main__":
    main()
