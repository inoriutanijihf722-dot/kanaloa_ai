"""Achievement rules for Kanaloa Investor Game."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from data_manager import load_achievements, save_achievements


ACHIEVEMENT_DEFINITIONS = [
    {
        "title": "初見送り",
        "condition": "初めてレースを見送った",
        "rule": "first_skip",
    },
    {
        "title": "ボール球を振らない者",
        "condition": "C判定を見送った",
        "rule": "c_grade_skip",
    },
    {
        "title": "余白を守る者",
        "condition": "見送りを3回以上記録",
        "rule": "three_skips",
    },
    {
        "title": "取り返したい日に耐えた者",
        "condition": "感情状態が「取り返したい」の時に見送った",
        "rule": "chasing_skip",
    },
    {
        "title": "資金を守る番人",
        "condition": "実際の購入額が推奨購入額以内の購入を5回以上",
        "rule": "five_rule_buys",
    },
    {
        "title": "10レース修行達成",
        "condition": "記録レース数が10以上",
        "rule": "ten_races",
    },
    {
        "title": "EVハンターの芽",
        "condition": "B判定以上のレースで、推奨額以内の判断を3回以上",
        "rule": "three_ev_disciplined",
    },
    {
        "title": "退屈を愛する者",
        "condition": "見送りを5回以上記録",
        "rule": "five_skips",
    },
]


def _decision(row: pd.Series) -> str:
    return "Skip" if row.get("decision") in {"Skip", "見送り"} else "Buy"


def _emotion(row: pd.Series) -> str:
    value = row.get("emotional_state")
    if value in {"Chasing Losses", "取り返したい"}:
        return "Chasing Losses"
    return str(value)


def _grade(row: pd.Series) -> str:
    value = row.get("ai_grade")
    if value in {"A", "勝負候補"}:
        return "A"
    if value in {"B", "監視候補"}:
        return "B"
    if value in {"C", "見送り候補"}:
        return "C"
    return str(value)


def _is_recommended_or_less(row: pd.Series) -> bool:
    actual = float(row.get("actual_bet", 0) or 0)
    recommended = float(row.get("recommended_bet", 0) or 0)
    return actual <= recommended


def _count_skips(log: pd.DataFrame) -> int:
    return sum(_decision(row) == "Skip" for _, row in log.iterrows())


def _count_c_grade_skips(log: pd.DataFrame) -> int:
    return sum(_grade(row) == "C" and _decision(row) == "Skip" for _, row in log.iterrows())


def _count_chasing_skips(log: pd.DataFrame) -> int:
    return sum(
        _emotion(row) == "Chasing Losses" and _decision(row) == "Skip"
        for _, row in log.iterrows()
    )


def _count_rule_buys(log: pd.DataFrame) -> int:
    return sum(
        _decision(row) == "Buy" and _is_recommended_or_less(row)
        for _, row in log.iterrows()
    )


def _count_ev_disciplined(log: pd.DataFrame) -> int:
    return sum(
        _grade(row) in {"A", "B"} and _is_recommended_or_less(row)
        for _, row in log.iterrows()
    )


def is_achievement_unlocked(rule: str, log: pd.DataFrame) -> bool:
    """Check whether a single achievement rule is unlocked."""
    if log.empty:
        return False

    if rule == "first_skip":
        return _count_skips(log) >= 1
    if rule == "c_grade_skip":
        return _count_c_grade_skips(log) >= 1
    if rule == "three_skips":
        return _count_skips(log) >= 3
    if rule == "chasing_skip":
        return _count_chasing_skips(log) >= 1
    if rule == "five_rule_buys":
        return _count_rule_buys(log) >= 5
    if rule == "ten_races":
        return len(log) >= 10
    if rule == "three_ev_disciplined":
        return _count_ev_disciplined(log) >= 3
    if rule == "five_skips":
        return _count_skips(log) >= 5

    return False


def update_achievements(log: pd.DataFrame) -> list[str]:
    """Save newly unlocked achievements and return their titles."""
    achievements = load_achievements()
    acquired_titles = set(achievements["title"].dropna())
    new_rows = []

    for definition in ACHIEVEMENT_DEFINITIONS:
        title = definition["title"]
        if title in acquired_titles:
            continue
        if is_achievement_unlocked(definition["rule"], log):
            new_rows.append(
                {
                    "title": title,
                    "condition": definition["condition"],
                    "acquired_at": datetime.now().isoformat(timespec="seconds"),
                }
            )

    if new_rows:
        achievements = pd.concat([achievements, pd.DataFrame(new_rows)], ignore_index=True)
        save_achievements(achievements)

    return [row["title"] for row in new_rows]


def achievement_catalog() -> pd.DataFrame:
    """Return all achievements with their conditions."""
    return pd.DataFrame(
        [
            {"title": item["title"], "condition": item["condition"], "rule": item["rule"]}
            for item in ACHIEVEMENT_DEFINITIONS
        ]
    )


def achievement_progress(rule: str, log: pd.DataFrame) -> dict[str, object]:
    """Return progress text for a locked achievement."""
    progress_rules = {
        "first_skip": (_count_skips(log), 1, "回"),
        "c_grade_skip": (_count_c_grade_skips(log), 1, "回"),
        "three_skips": (_count_skips(log), 3, "回"),
        "chasing_skip": (_count_chasing_skips(log), 1, "回"),
        "five_rule_buys": (_count_rule_buys(log), 5, "回"),
        "ten_races": (len(log), 10, "レース"),
        "three_ev_disciplined": (_count_ev_disciplined(log), 3, "回"),
        "five_skips": (_count_skips(log), 5, "回"),
    }
    current, target, unit = progress_rules[rule]
    remaining = max(0, target - current)
    return {
        "current": current,
        "target": target,
        "remaining": remaining,
        "unit": unit,
    }
