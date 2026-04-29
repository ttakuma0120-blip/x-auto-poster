import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "state.json"

PHASE1_END = 7   # 〜7日目：2日に1回（朝のみ）
PHASE2_END = 14  # 〜14日目：1日1回（朝のみ）
# 15日目以降：1日2回（朝・夜）


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"state.json読み込みエラー: {e}")
    return {}


def _save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def initialize_state() -> None:
    state = _load_state()
    if "start_date" not in state:
        state["start_date"] = date.today().isoformat()
        _save_state(state)
        logger.info(f"投稿スケジュール開始: {state['start_date']}")
    else:
        days_elapsed = (date.today() - date.fromisoformat(state["start_date"])).days
        phase = get_phase()
        logger.info(f"状態読み込み: 開始日 {state['start_date']} (経過 {days_elapsed}日 / フェーズ{phase})")


def get_days_elapsed() -> int:
    state = _load_state()
    if "start_date" not in state:
        return 0
    return (date.today() - date.fromisoformat(state["start_date"])).days


def get_phase() -> int:
    days = get_days_elapsed()
    if days < PHASE1_END:
        return 1
    elif days < PHASE2_END:
        return 2
    else:
        return 3


def should_post_morning() -> bool:
    phase = get_phase()
    if phase == 1:
        # 2日に1回（開始日から偶数日目のみ投稿）
        return get_days_elapsed() % 2 == 0
    return True  # フェーズ2・3は毎朝投稿


def should_post_evening() -> bool:
    return get_phase() == 3  # フェーズ3のみ夜も投稿


def get_phase_description() -> str:
    phase = get_phase()
    days = get_days_elapsed()
    if phase == 1:
        remaining = PHASE1_END - days
        return f"フェーズ1（2日に1回）→ 残り{remaining}日でフェーズ2へ"
    elif phase == 2:
        remaining = PHASE2_END - days
        return f"フェーズ2（1日1回）→ 残り{remaining}日でフェーズ3へ"
    else:
        return "フェーズ3（1日2回）通常運用中"


# 後方互換のため残す
def is_warm_up_mode() -> bool:
    return get_phase() < 3


def get_days_remaining() -> int:
    return max(0, PHASE2_END - get_days_elapsed())
