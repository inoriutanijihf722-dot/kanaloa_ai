"""Growth candidate helper for Kanaloa AI.

This module is intentionally independent from the existing A/B/C judgement,
scoring logic, CSV save flow, and app UI. It only supports tracking horses
whose own growth may make them interesting for the next run.
"""

from __future__ import annotations

from dataclasses import dataclass, field


TAG_GROWTH_SIGN = "【成長サイン】"
TAG_BODY_GROWTH = "【馬体成長】"
TAG_TRAINING_PB = "【調教自己ベスト】"
TAG_STABLE_COMMENT = "【コメント成長示唆】"
TAG_POSITION_IMPROVED = "【位置取り改善】"
TAG_STRETCH_RESPONSE = "【直線手応え良化】"
TAG_FRONT_OR_MID = "【先団中団可】"
TAG_GROWTH_HYPOTHESIS = "【成長仮説あり】"
TAG_NEXT_RUN_TARGET = "【次走成長狙い】"
WARNING_POPULAR_ODDS = "【人気時注意】"

POPULAR_ODDS_RANKS = {"A", "B", "C"}


@dataclass(frozen=True)
class GrowthInput:
    horse_name: str
    body_weight_delta: int | None = None
    has_training_pb: bool = False
    has_stable_growth_comment: bool = False
    position_improved: bool = False
    stretch_response_improved: bool = False
    can_take_front_or_mid_position: bool = False
    odds_rank: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class GrowthJudgment:
    level: str
    tags: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: str = ""


def judge_growth_candidate(input: GrowthInput) -> GrowthJudgment:
    """Judge whether a horse is a next-run growth target candidate."""
    tags: list[str] = []
    reasons: list[str] = []
    warnings: list[str] = []

    if input.body_weight_delta is not None and input.body_weight_delta >= 8:
        tags.append(TAG_BODY_GROWTH)
        reasons.append("馬体重が+8kg以上で、馬体成長の入口サインがあります。")

    if input.has_training_pb:
        tags.append(TAG_TRAINING_PB)
        reasons.append("調教時計で自己ベスト更新が確認されています。")

    if input.has_stable_growth_comment:
        tags.append(TAG_STABLE_COMMENT)
        reasons.append("厩舎コメントに成長示唆があります。")

    has_growth_sign = bool(tags)
    if has_growth_sign:
        tags.insert(0, TAG_GROWTH_SIGN)

    if input.position_improved:
        tags.append(TAG_POSITION_IMPROVED)
        reasons.append("近走映像で位置取り改善が確認されています。")

    if input.stretch_response_improved:
        tags.append(TAG_STRETCH_RESPONSE)
        reasons.append("近走映像で直線の手応え良化が確認されています。")

    has_video_improvement = input.position_improved or input.stretch_response_improved

    if input.can_take_front_or_mid_position:
        tags.append(TAG_FRONT_OR_MID)
        reasons.append("次走で先団または中団を取れる可能性があります。")

    if has_growth_sign and has_video_improvement:
        tags.append(TAG_GROWTH_HYPOTHESIS)

    if (
        has_growth_sign
        and has_video_improvement
        and input.can_take_front_or_mid_position
    ):
        level = "next_run_growth_target"
        tags.append(TAG_NEXT_RUN_TARGET)
        summary = "成長サインと映像改善が揃い、次走成長狙い候補です。"
    elif has_growth_sign:
        level = "growth_hypothesis"
        summary = "成長サインはありますが、次走狙いには追加確認が必要です。"
    elif has_video_improvement:
        level = "watch"
        summary = "映像改善はありますが、成長サイン未確認のため観察対象です。"
    else:
        level = "none"
        summary = "成長サインや映像改善は確認されていません。"
        reasons.append("成長候補として扱う材料が不足しています。")

    odds_rank = (input.odds_rank or "").strip().upper()
    if odds_rank in POPULAR_ODDS_RANKS:
        warnings.append(WARNING_POPULAR_ODDS)

    return GrowthJudgment(
        level=level,
        tags=tags,
        reasons=reasons,
        warnings=warnings,
        summary=summary,
    )
