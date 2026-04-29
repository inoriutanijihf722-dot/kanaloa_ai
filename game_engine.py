"""Application-level game actions for Kanaloa Investor Game."""

from __future__ import annotations

import pandas as pd

from data_manager import load_player_status, load_race_log, save_player_status, save_race_log
from kanaloa_logic import judge_expected_value, recommend_bet_amount
from scoring import calculate_scores, rank_from_score


def evaluate_race(
    bankroll: float,
    confidence: int,
    estimated_edge: float,
    odds: float,
    emotional_state: str,
    thesis: str,
) -> dict[str, object]:
    """Run the Kanaloa judgment and recommended bet sizing."""
    ai_grade, ai_reason = judge_expected_value(
        confidence=confidence,
        estimated_edge=estimated_edge,
        odds=odds,
        emotional_state=emotional_state,
        thesis=thesis,
    )
    recommended_bet = recommend_bet_amount(bankroll, confidence, ai_grade)
    return {
        "ai_grade": ai_grade,
        "ai_reason": ai_reason,
        "recommended_bet": recommended_bet,
    }


def add_race_decision(entry: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Append one race decision and refresh player status."""
    log = load_race_log()
    log = pd.concat([log, pd.DataFrame([entry])], ignore_index=True)
    save_race_log(log)
    status = update_player_status(log)
    return log, status


def update_player_status(log: pd.DataFrame | None = None) -> pd.DataFrame:
    """Recalculate score, rank, and bankroll from the saved race log."""
    if log is None:
        log = load_race_log()

    old_status = load_player_status()
    player_name = old_status.iloc[0].get("player_name", "Kanaloa Trainee")
    scores = calculate_scores(log)
    investor_rank = rank_from_score(scores["investor_score"], scores, len(log))

    if log.empty:
        current_bankroll = float(old_status.iloc[0].get("current_bankroll", 100000))
    else:
        first_bankroll = float(log.iloc[0].get("bankroll_before", 100000))
        current_bankroll = first_bankroll + float(log["profit_loss"].fillna(0).sum())

    status = pd.DataFrame(
        [
            {
                "player_name": player_name,
                "current_bankroll": round(current_bankroll, 0),
                "investor_score": round(scores["investor_score"], 1),
                "investor_rank": investor_rank,
                "skip_skill": round(scores["skip_skill"], 1),
                "rule_discipline": round(scores["rule_discipline"], 1),
                "expected_value_judgment": round(scores["expected_value_judgment"], 1),
                "bankroll_stability": round(scores["bankroll_stability"], 1),
                "emotional_control": round(scores["emotional_control"], 1),
                "reflection_consistency": round(scores["reflection_consistency"], 1),
            }
        ]
    )
    save_player_status(status)
    return status
