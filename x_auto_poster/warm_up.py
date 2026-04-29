import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "state.json"
WARM_UP_DAYS = 14


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
        logger.info(f"warm_upモード開始: {state['start_date']} ({WARM_UP_DAYS}日間)")
    else:
        days_elapsed = (date.today() - date.fromisoformat(state["start_date"])).days
        logger.info(f"状態読み込み: 開始日 {state['start_date']} (経過 {days_elapsed}日)")


def is_warm_up_mode() -> bool:
    state = _load_state()
    if "start_date" not in state:
        return True
    days_elapsed = (date.today() - date.fromisoformat(state["start_date"])).days
    return days_elapsed < WARM_UP_DAYS


def get_days_remaining() -> int:
    state = _load_state()
    if "start_date" not in state:
        return WARM_UP_DAYS
    days_elapsed = (date.today() - date.fromisoformat(state["start_date"])).days
    return max(0, WARM_UP_DAYS - days_elapsed)
