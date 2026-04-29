"""CSV loading and saving helpers for Kanaloa Investor Game."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


DATA_DIR = Path("sample_data")
RACE_LOG_PATH = DATA_DIR / "race_decision_log.csv"
PLAYER_STATUS_PATH = DATA_DIR / "player_status.csv"
ACHIEVEMENTS_PATH = DATA_DIR / "achievements.csv"


RACE_LOG_COLUMNS = [
    "date",
    "race_name",
    "bankroll_before",
    "odds",
    "estimated_edge",
    "thesis",
    "ai_grade",
    "ai_reason",
    "decision",
    "confidence",
    "emotional_state",
    "recommended_bet",
    "actual_bet",
    "result_amount",
    "profit_loss",
    "reflection",
]


PLAYER_STATUS_COLUMNS = [
    "player_name",
    "current_bankroll",
    "investor_score",
    "investor_rank",
    "skip_skill",
    "rule_discipline",
    "expected_value_judgment",
    "bankroll_stability",
    "emotional_control",
    "reflection_consistency",
]

ACHIEVEMENT_COLUMNS = [
    "title",
    "condition",
    "acquired_at",
]


def ensure_data_files() -> None:
    """Create CSV files with an empty training state when they do not exist."""
    DATA_DIR.mkdir(exist_ok=True)

    if not RACE_LOG_PATH.exists():
        empty_log().to_csv(RACE_LOG_PATH, index=False)

    if not PLAYER_STATUS_PATH.exists():
        initial_player_status().to_csv(PLAYER_STATUS_PATH, index=False)

    if not ACHIEVEMENTS_PATH.exists():
        empty_achievements().to_csv(ACHIEVEMENTS_PATH, index=False)


def empty_log() -> pd.DataFrame:
    """Return an empty race log with the expected columns."""
    return pd.DataFrame(columns=RACE_LOG_COLUMNS)


def initial_player_status() -> pd.DataFrame:
    """Return the default player status for a fresh training start."""
    return pd.DataFrame(
        [
            {
                "player_name": "Kanaloa Trainee",
                "current_bankroll": 100000,
                "investor_score": 50.0,
                "investor_rank": "ビギナーギャンブラー",
                "skip_skill": 50.0,
                "rule_discipline": 50.0,
                "expected_value_judgment": 50.0,
                "bankroll_stability": 50.0,
                "emotional_control": 50.0,
                "reflection_consistency": 50.0,
            }
        ],
        columns=PLAYER_STATUS_COLUMNS,
    )


def reset_training_data() -> None:
    """Reset race decisions and player status for a fresh real-use start."""
    DATA_DIR.mkdir(exist_ok=True)
    empty_log().to_csv(RACE_LOG_PATH, index=False)
    initial_player_status().to_csv(PLAYER_STATUS_PATH, index=False)
    empty_achievements().to_csv(ACHIEVEMENTS_PATH, index=False)


def empty_achievements() -> pd.DataFrame:
    """Return an empty achievement table with the expected columns."""
    return pd.DataFrame(columns=ACHIEVEMENT_COLUMNS)


def load_race_log() -> pd.DataFrame:
    """Load the race decision log."""
    ensure_data_files()
    log = pd.read_csv(RACE_LOG_PATH)
    return normalize_race_log(log)


def save_race_log(log: pd.DataFrame) -> None:
    """Save the race decision log with stable column order."""
    DATA_DIR.mkdir(exist_ok=True)
    log = normalize_race_log(log)
    log = log.reindex(columns=RACE_LOG_COLUMNS)
    log.to_csv(RACE_LOG_PATH, index=False)


def normalize_race_log(log: pd.DataFrame) -> pd.DataFrame:
    """Keep payout and profit/loss columns valid for old and new CSV files."""
    if log.empty:
        return log.reindex(columns=RACE_LOG_COLUMNS)

    log = log.copy()

    if "actual_bet" not in log.columns:
        log["actual_bet"] = 0
    if "result_amount" not in log.columns:
        log["result_amount"] = 0

    actual_bet = pd.to_numeric(log["actual_bet"], errors="coerce").fillna(0)
    payout = pd.to_numeric(log["result_amount"], errors="coerce").fillna(0)

    if "profit_loss" not in log.columns:
        old_net_result = payout < 0
        log["profit_loss"] = payout - actual_bet
        log.loc[old_net_result, "profit_loss"] = payout[old_net_result]
        payout = payout.mask(old_net_result, actual_bet + payout)
    else:
        log["profit_loss"] = pd.to_numeric(log["profit_loss"], errors="coerce").fillna(
            payout - actual_bet
        )

    log["result_amount"] = payout.clip(lower=0)
    log["profit_loss"] = pd.to_numeric(log["result_amount"], errors="coerce").fillna(0) - actual_bet

    return log.reindex(columns=RACE_LOG_COLUMNS)


def load_player_status() -> pd.DataFrame:
    """Load the single-row player status table."""
    ensure_data_files()
    return pd.read_csv(PLAYER_STATUS_PATH)


def save_player_status(status: pd.DataFrame) -> None:
    """Save the player status table with stable column order."""
    DATA_DIR.mkdir(exist_ok=True)
    status = status.reindex(columns=PLAYER_STATUS_COLUMNS)
    status.to_csv(PLAYER_STATUS_PATH, index=False)


def load_achievements() -> pd.DataFrame:
    """Load acquired achievement titles."""
    ensure_data_files()
    try:
        return pd.read_csv(ACHIEVEMENTS_PATH).reindex(columns=ACHIEVEMENT_COLUMNS)
    except pd.errors.EmptyDataError:
        achievements = empty_achievements()
        achievements.to_csv(ACHIEVEMENTS_PATH, index=False)
        return achievements


def save_achievements(achievements: pd.DataFrame) -> None:
    """Save acquired achievement titles with stable column order."""
    DATA_DIR.mkdir(exist_ok=True)
    achievements = achievements.reindex(columns=ACHIEVEMENT_COLUMNS)
    achievements.to_csv(ACHIEVEMENTS_PATH, index=False)
