"""Scoring rules for Kanaloa Investor Game.

The app rewards process quality more than short-term profit. The formulas here
are intentionally simple so the user can understand why their rank changed.
"""

from __future__ import annotations

import pandas as pd


SCORE_WEIGHTS = {
    "skip_skill": 0.35,
    "rule_discipline": 0.30,
    "expected_value_judgment": 0.20,
    "bankroll_stability": 0.10,
    "reflection_consistency": 0.05,
}

DECISION_ALIASES = {
    "Buy": "Buy",
    "購入": "Buy",
    "Skip": "Skip",
    "見送り": "Skip",
}

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

GRADE_ALIASES = {
    "A": "A",
    "勝負候補": "A",
    "B": "B",
    "監視候補": "B",
    "C": "C",
    "見送り候補": "C",
}

SKILL_LABELS = {
    "skip_skill": "見送り力",
    "rule_discipline": "ルール遵守力",
    "expected_value_judgment": "期待値判断力",
    "bankroll_stability": "資金管理力",
    "emotional_control": "感情コントロール力",
    "reflection_consistency": "振り返り力",
}

RANK_REQUIREMENTS = [
    {
        "name": "ビギナーギャンブラー",
        "score": 0,
        "races": 0,
        "skills": {},
    },
    {
        "name": "見習い投資家",
        "score": 50,
        "races": 3,
        "skills": {},
    },
    {
        "name": "余白キーパー",
        "score": 60,
        "races": 5,
        "skills": {},
    },
    {
        "name": "ボール球見極め師",
        "score": 70,
        "races": 10,
        "skills": {},
    },
    {
        "name": "EVハンター",
        "score": 75,
        "races": 20,
        "skills": {},
    },
    {
        "name": "資金管理マスター",
        "score": 80,
        "races": 30,
        "skills": {"bankroll_stability": 80},
    },
    {
        "name": "カナロア投資家",
        "score": 85,
        "races": 50,
        "skills": {"skip_skill": 80, "rule_discipline": 80},
    },
    {
        "name": "複利の賢者",
        "score": 90,
        "races": 100,
        "skills": {
            "skip_skill": 75,
            "rule_discipline": 75,
            "expected_value_judgment": 75,
            "bankroll_stability": 75,
            "emotional_control": 75,
            "reflection_consistency": 75,
        },
    },
]


def clamp_score(value: float) -> float:
    """Keep any score inside the 0-100 range."""
    return max(0.0, min(100.0, float(value)))


def _empty_scores() -> dict[str, float]:
    return {
        "skip_skill": 50.0,
        "rule_discipline": 50.0,
        "expected_value_judgment": 50.0,
        "bankroll_stability": 50.0,
        "emotional_control": 50.0,
        "reflection_consistency": 50.0,
        "investor_score": 50.0,
    }


def calculate_skip_skill(log: pd.DataFrame) -> float:
    """Reward disciplined skips, especially weak or low-confidence races."""
    if log.empty:
        return 50.0

    score = 25.0
    for _, row in log.iterrows():
        decision = DECISION_ALIASES.get(row.get("decision", ""), row.get("decision", ""))
        ai_grade = GRADE_ALIASES.get(row.get("ai_grade", ""), row.get("ai_grade", ""))
        emotional_state = EMOTIONAL_STATE_ALIASES.get(
            row.get("emotional_state", ""), row.get("emotional_state", "")
        )
        confidence = int(row.get("confidence", 3))
        thesis = str(row.get("thesis", "")).strip()

        if decision == "Skip":
            if ai_grade == "C":
                score += 10
            elif ai_grade == "B":
                score += 5
            elif ai_grade == "A":
                if confidence <= 2 or emotional_state in {"Excited", "Chasing Losses"}:
                    score += 2
                elif len(thesis) >= 25:
                    score -= 2
                else:
                    score -= 4

            if confidence <= 2:
                score += 8
            elif confidence == 3:
                score += 3

            if emotional_state == "Chasing Losses":
                score += 5
            elif emotional_state == "Excited":
                score += 4

        elif decision == "Buy" and ai_grade == "C":
            score -= 7
        elif decision == "Buy" and confidence <= 2:
            score -= 5

    return clamp_score(score)


def calculate_rule_discipline(log: pd.DataFrame) -> float:
    """Measure whether actual behavior followed bankroll and emotion rules."""
    if log.empty:
        return 50.0

    score = 55.0
    for _, row in log.iterrows():
        recommended = float(row.get("recommended_bet", 0))
        actual = float(row.get("actual_bet", 0))
        decision = DECISION_ALIASES.get(row.get("decision", ""), row.get("decision", ""))
        emotional_state = EMOTIONAL_STATE_ALIASES.get(
            row.get("emotional_state", ""), row.get("emotional_state", "")
        )

        if decision == "Skip" and actual == 0:
            score += 5
        elif decision == "Skip" and actual > 0:
            score -= 12

        if recommended > 0 and actual <= recommended:
            score += 3
        elif recommended > 0 and actual > recommended:
            score -= min(12, (actual - recommended) / recommended * 8)

        if emotional_state == "Chasing Losses" and actual > 0:
            score -= 10
            if recommended > 0 and actual > recommended:
                score -= 35
        elif emotional_state == "Calm":
            score += 2

    return clamp_score(score)


def calculate_expected_value_judgment(log: pd.DataFrame) -> float:
    """Reward alignment between AI grade, confidence, and buy/skip decisions."""
    if log.empty:
        return 50.0

    score = 50.0
    for _, row in log.iterrows():
        ai_grade = GRADE_ALIASES.get(row.get("ai_grade", ""), row.get("ai_grade", ""))
        decision = DECISION_ALIASES.get(row.get("decision", ""), row.get("decision", ""))
        confidence = int(row.get("confidence", 3))

        if ai_grade == "A" and decision == "Buy" and confidence >= 4:
            score += 6
        elif ai_grade == "B" and decision in {"Buy", "Skip"} and confidence >= 3:
            score += 2
        elif ai_grade == "C" and decision == "Skip":
            score += 6
        elif ai_grade == "C" and decision == "Buy":
            score -= 8
        elif ai_grade == "A" and decision == "Buy" and confidence <= 2:
            score -= 3

    return clamp_score(score)


def calculate_bankroll_stability(log: pd.DataFrame) -> float:
    """Reward small, stable position sizing and penalize oversized bets."""
    if log.empty:
        return 50.0

    score = 60.0
    for _, row in log.iterrows():
        actual = float(row.get("actual_bet", 0))
        bankroll = float(row.get("bankroll_before", 0))
        profit_loss = float(row.get("profit_loss", 0))

        if bankroll <= 0:
            continue

        bet_ratio = actual / bankroll
        if actual == 0:
            score += 1
        elif bet_ratio <= 0.02:
            score += 3
        elif bet_ratio <= 0.05:
            score += 1
        else:
            score -= min(15, bet_ratio * 100)

        if profit_loss < 0 and bet_ratio > 0.03:
            score -= 5

    return clamp_score(score)


def calculate_emotional_control(log: pd.DataFrame) -> float:
    """Reward calm decisions and resisting the urge to chase losses."""
    if log.empty:
        return 50.0

    score = 55.0
    for _, row in log.iterrows():
        decision = DECISION_ALIASES.get(row.get("decision", ""), row.get("decision", ""))
        emotional_state = EMOTIONAL_STATE_ALIASES.get(
            row.get("emotional_state", ""), row.get("emotional_state", "")
        )

        if emotional_state == "Calm":
            score += 4
        elif emotional_state == "Chasing Losses" and decision == "Skip":
            score += 8
        elif emotional_state == "Chasing Losses" and decision == "Buy":
            score -= 12
        elif emotional_state in {"Excited", "Fearful"} and decision == "Skip":
            score += 2
        elif emotional_state in {"Excited", "Fearful"} and decision == "Buy":
            score -= 3

    return clamp_score(score)


def calculate_reflection_consistency(log: pd.DataFrame) -> float:
    """Reward useful reflection notes, especially structured ones."""
    if log.empty:
        return 50.0

    template_terms = [
        "今日の判断",
        "判断理由",
        "感情状態",
        "守れたルール",
        "次回への改善",
    ]
    score = 35.0

    for note in log["reflection"].fillna("").astype(str):
        note = note.strip()
        if not note:
            score -= 3
        elif len(note) >= 80 or all(term in note for term in template_terms):
            score += 8
        elif len(note) >= 30:
            score += 4
        else:
            score += 1

        if "取り返したい衝動への対処" in note:
            score += 3

    return clamp_score(score)


def calculate_scores(log: pd.DataFrame) -> dict[str, float]:
    """Calculate all component scores and the weighted investor score."""
    if log.empty:
        return _empty_scores()

    scores = {
        "skip_skill": calculate_skip_skill(log),
        "rule_discipline": calculate_rule_discipline(log),
        "expected_value_judgment": calculate_expected_value_judgment(log),
        "bankroll_stability": calculate_bankroll_stability(log),
        "emotional_control": calculate_emotional_control(log),
        "reflection_consistency": calculate_reflection_consistency(log),
    }
    investor_score = sum(scores[name] * weight for name, weight in SCORE_WEIGHTS.items())
    scores["investor_score"] = clamp_score(investor_score)
    return scores


def _meets_rank_requirement(
    scores: dict[str, float], race_count: int, requirement: dict[str, object]
) -> bool:
    """Check whether the player meets one rank requirement."""
    if scores.get("investor_score", 0) < float(requirement["score"]):
        return False
    if race_count < int(requirement["races"]):
        return False

    required_skills = requirement.get("skills", {})
    for skill, required_score in required_skills.items():
        if scores.get(skill, 0) < float(required_score):
            return False

    return True


def rank_from_score(
    score: float, scores: dict[str, float] | None = None, race_count: int = 0
) -> str:
    """Translate score, race count, and skill gates into a training rank."""
    rank_scores = dict(scores or {})
    rank_scores["investor_score"] = score

    for requirement in reversed(RANK_REQUIREMENTS):
        if _meets_rank_requirement(rank_scores, race_count, requirement):
            return str(requirement["name"])

    return "ビギナーギャンブラー"


def get_next_rank_progress(
    scores: dict[str, float], race_count: int
) -> dict[str, object] | None:
    """Return requirement progress for the next locked rank."""
    current_rank = rank_from_score(scores["investor_score"], scores, race_count)
    current_index = next(
        index
        for index, requirement in enumerate(RANK_REQUIREMENTS)
        if requirement["name"] == current_rank
    )

    if current_index >= len(RANK_REQUIREMENTS) - 1:
        return None

    next_requirement = RANK_REQUIREMENTS[current_index + 1]
    conditions = [
        {
            "label": f"投資家スコア {next_requirement['score']}以上",
            "achieved": scores["investor_score"] >= float(next_requirement["score"]),
            "remaining": max(0.0, float(next_requirement["score"]) - scores["investor_score"]),
            "unit": "pt",
        },
        {
            "label": f"記録レース数 {next_requirement['races']}以上",
            "achieved": race_count >= int(next_requirement["races"]),
            "remaining": max(0, int(next_requirement["races"]) - race_count),
            "unit": "レース",
        },
    ]

    for skill, required_score in next_requirement.get("skills", {}).items():
        current_score = scores.get(skill, 0)
        conditions.append(
            {
                "label": f"{SKILL_LABELS[skill]} {required_score}以上",
                "achieved": current_score >= float(required_score),
                "remaining": max(0.0, float(required_score) - current_score),
                "unit": "pt",
            }
        )

    return {
        "next_rank": next_requirement["name"],
        "conditions": conditions,
    }
