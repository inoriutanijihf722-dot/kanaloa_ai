from __future__ import annotations

from growth_candidate_judge import (
    TAG_NEXT_RUN_TARGET,
    WARNING_POPULAR_ODDS,
    GrowthInput,
    judge_growth_candidate,
)


def test_body_weight_growth_only_does_not_become_next_run_target() -> None:
    result = judge_growth_candidate(
        GrowthInput(horse_name="馬体成長のみ", body_weight_delta=8)
    )

    assert result.level == "growth_hypothesis"
    assert TAG_NEXT_RUN_TARGET not in result.tags


def test_training_pb_position_improved_and_front_or_mid_is_next_run_target() -> None:
    result = judge_growth_candidate(
        GrowthInput(
            horse_name="成長狙い型",
            has_training_pb=True,
            position_improved=True,
            can_take_front_or_mid_position=True,
        )
    )

    assert result.level == "next_run_growth_target"
    assert TAG_NEXT_RUN_TARGET in result.tags


def test_stable_comment_and_stretch_response_is_growth_hypothesis_or_better() -> None:
    result = judge_growth_candidate(
        GrowthInput(
            horse_name="コメント映像型",
            has_stable_growth_comment=True,
            stretch_response_improved=True,
        )
    )

    assert result.level in {"growth_hypothesis", "next_run_growth_target"}


def test_video_improvement_only_is_watch() -> None:
    result = judge_growth_candidate(
        GrowthInput(horse_name="映像だけ型", position_improved=True)
    )

    assert result.level == "watch"


def test_popular_odds_rank_adds_warning() -> None:
    result = judge_growth_candidate(
        GrowthInput(
            horse_name="人気注意型",
            has_training_pb=True,
            position_improved=True,
            can_take_front_or_mid_position=True,
            odds_rank="B",
        )
    )

    assert WARNING_POPULAR_ODDS in result.warnings


def test_no_growth_sign_or_video_improvement_is_none() -> None:
    result = judge_growth_candidate(GrowthInput(horse_name="材料なし"))

    assert result.level == "none"
