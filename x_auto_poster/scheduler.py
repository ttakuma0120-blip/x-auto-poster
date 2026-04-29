import logging
from typing import Callable

from apscheduler.schedulers.blocking import BlockingScheduler

logger = logging.getLogger(__name__)

# APSchedulerのjitterは「指定時刻 + 0〜jitter秒のランダム」を加算する。
# 朝8:00 ±30分 → 7:30スタート + jitter=3600秒(0〜60分) → 7:30〜8:30
# 夜20:00 ±30分 → 19:30スタート + jitter=3600秒 → 19:30〜20:30
MORNING_HOUR = 7
MORNING_MINUTE = 30
EVENING_HOUR = 19
EVENING_MINUTE = 30
JITTER_SECONDS = 3600


def _morning_job(run_post_func: Callable) -> None:
    logger.info("朝の投稿を開始します")
    try:
        run_post_func(dry_run=False)
    except Exception as e:
        logger.error(f"朝の投稿でエラーが発生しました: {e}")


def _evening_job(run_post_func: Callable) -> None:
    from warm_up import is_warm_up_mode

    if is_warm_up_mode():
        logger.info("warm_upモード中のため夜の投稿をスキップします")
        return

    logger.info("夜の投稿を開始します")
    try:
        run_post_func(dry_run=False)
    except Exception as e:
        logger.error(f"夜の投稿でエラーが発生しました: {e}")


def start_scheduler(run_post_func: Callable) -> None:
    scheduler = BlockingScheduler(timezone="Asia/Tokyo")

    scheduler.add_job(
        _morning_job,
        "cron",
        hour=MORNING_HOUR,
        minute=MORNING_MINUTE,
        jitter=JITTER_SECONDS,
        args=[run_post_func],
        id="morning_post",
    )

    scheduler.add_job(
        _evening_job,
        "cron",
        hour=EVENING_HOUR,
        minute=EVENING_MINUTE,
        jitter=JITTER_SECONDS,
        args=[run_post_func],
        id="evening_post",
    )

    logger.info("スケジュール設定:")
    logger.info("  朝: 7:30〜8:30 の間でランダム投稿")
    logger.info("  夜: 19:30〜20:30 の間でランダム投稿 (warm_upモード中はスキップ)")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("スケジューラーを停止しました")
