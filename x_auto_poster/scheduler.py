import logging
from typing import Callable

from apscheduler.schedulers.blocking import BlockingScheduler

logger = logging.getLogger(__name__)

# 7:30 + jitter(0〜60分) = 7:30〜8:30（朝8時±30分）
# 19:30 + jitter(0〜60分) = 19:30〜20:30（夜20時±30分）
MORNING_HOUR = 7
MORNING_MINUTE = 30
EVENING_HOUR = 19
EVENING_MINUTE = 30
JITTER_SECONDS = 3600


def _morning_job(run_post_func: Callable) -> None:
    from warm_up import get_phase, get_phase_description, should_post_morning

    phase = get_phase()
    logger.info(f"現在の状態: {get_phase_description()}")

    if not should_post_morning():
        logger.info("フェーズ1: 本日は投稿スキップ（2日に1回のスケジュール）")
        return

    logger.info(f"朝の投稿を開始します（フェーズ{phase}）")
    try:
        run_post_func(dry_run=False)
    except Exception as e:
        logger.error(f"朝の投稿でエラーが発生しました: {e}")


def _evening_job(run_post_func: Callable) -> None:
    from warm_up import get_phase, get_phase_description, should_post_evening

    phase = get_phase()
    logger.info(f"現在の状態: {get_phase_description()}")

    if not should_post_evening():
        logger.info(f"フェーズ{phase}: 夜の投稿をスキップします（フェーズ3から開始）")
        return

    logger.info("夜の投稿を開始します（フェーズ3）")
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

    logger.info("投稿スケジュール:")
    logger.info("  フェーズ1（〜7日目） : 2日に1回 朝7:30〜8:30")
    logger.info("  フェーズ2（8〜14日目）: 毎朝 7:30〜8:30")
    logger.info("  フェーズ3（15日目〜） : 朝7:30〜8:30 + 夜19:30〜20:30")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("スケジューラーを停止しました")
