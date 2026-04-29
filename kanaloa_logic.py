"""Simple Kanaloa-style expected value judgment.

This is not a prediction model. It is a training aid that checks whether the
user's thesis, confidence, odds, and emotional state suggest a disciplined race.
"""

from __future__ import annotations


EMOTIONAL_STATE_ALIASES = {
    "Calm": "Calm",
    "冷静": "Calm",
    "Excited": "Excited",
    "興奮": "Excited",
    "Chasing Losses": "Chasing Losses",
    "取り返したい": "Chasing Losses",
    "Fearful": "Fearful",
    "不安": "Fearful",
}


def judge_expected_value(
    confidence: int,
    estimated_edge: float,
    odds: float,
    emotional_state: str,
    thesis: str,
) -> tuple[str, str]:
    """Return an A/B/C grade and a short explanation."""
    score = 0
    emotional_state_key = EMOTIONAL_STATE_ALIASES.get(emotional_state, emotional_state)

    if confidence >= 4:
        score += 2
    elif confidence <= 2:
        score -= 2

    if estimated_edge >= 10:
        score += 2
    elif estimated_edge >= 3:
        score += 1
    else:
        score -= 2

    if 2.0 <= odds <= 20.0:
        score += 1
    elif odds > 40.0:
        score -= 1

    if len(thesis.strip()) >= 25:
        score += 1
    else:
        score -= 1

    if emotional_state_key == "Calm":
        score += 1
    elif emotional_state_key == "Chasing Losses":
        score -= 3
    elif emotional_state_key in {"Excited", "Fearful"}:
        score -= 1

    if score >= 4:
        return "A", "根拠・自信度・感情のバランスがよい勝負候補です。購入する場合も資金配分は守りましょう。"
    if score >= 1:
        return "B", "期待値はありそうですが、決め手はまだ弱めです。少額か見送りを検討しましょう。"
    return "C", "自信度または感情面に不安があります。見送りも立派な投資判断です。"


def recommend_bet_amount(bankroll: float, confidence: int, ai_grade: str) -> float:
    """Recommend a conservative training bet amount based on process quality."""
    if bankroll <= 0 or ai_grade == "C" or confidence <= 2:
        return 0.0

    if ai_grade == "A" and confidence >= 5:
        ratio = 0.02
    elif ai_grade == "A":
        ratio = 0.015
    else:
        ratio = 0.01

    return round(bankroll * ratio, 0)
