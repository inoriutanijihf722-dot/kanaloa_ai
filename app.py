"""Streamlit MVP for Kanaloa Investor Game."""

from __future__ import annotations

import base64
import html
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from achievements import achievement_catalog, achievement_progress, update_achievements
from data_manager import (
    ensure_data_files,
    load_achievements,
    load_player_status,
    load_race_log,
    reset_training_data,
)
from game_engine import add_race_decision, evaluate_race, update_player_status
from scoring import get_next_rank_progress


st.set_page_config(page_title="カナロア投資道場", layout="wide")


GRADE_LABELS = {
    "A": "勝負候補",
    "B": "監視候補",
    "C": "見送り候補",
}

DECISION_LABELS = {
    "Buy": "購入",
    "Skip": "見送り",
    "購入": "購入",
    "見送り": "見送り",
}

EMOTION_LABELS = {
    "Calm": "冷静",
    "Excited": "興奮",
    "Chasing Losses": "取り返したい",
    "Fearful": "不安",
    "冷静": "冷静",
    "興奮": "興奮",
    "取り返したい": "取り返したい",
    "不安": "不安",
}

SCORE_LABELS = {
    "skip_skill": "見送り力",
    "rule_discipline": "ルール遵守力",
    "expected_value_judgment": "期待値判断力",
    "bankroll_stability": "資金管理力",
    "emotional_control": "感情コントロール力",
    "reflection_consistency": "振り返り力",
}

# Place optional character images here. The app falls back to icons if missing.
CHARACTERS = {
    "senpai": {
        "name": "先輩",
        "icon": "🔥",
        "image": "assets/characters/senpai.png",
    },
    "analyst": {
        "name": "分析者",
        "icon": "📊",
        "image": "assets/characters/analyst.png",
    },
    "kanaloa": {
        "name": "カナロア君",
        "icon": "🐴",
        "image": "assets/characters/kanaloa.png",
    },
}


def apply_layout_style() -> None:
    """Keep the dashboard readable without adding heavy UI complexity."""
    st.markdown(
        """
        <style>
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e8e8e8;
            border-radius: 8px;
            padding: 14px 16px;
            min-height: 104px;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.95rem;
            color: #555555;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.45rem;
            white-space: normal;
            line-height: 1.25;
        }
        .rank-card {
            background: #f7fbff;
            border: 1px solid #dbeafe;
            border-radius: 8px;
            padding: 16px 18px;
            margin: 8px 0 18px;
        }
        .rank-label {
            color: #475569;
            font-size: 0.95rem;
            margin-bottom: 4px;
        }
        .rank-value {
            color: #0f172a;
            font-size: 1.9rem;
            font-weight: 700;
            line-height: 1.25;
        }
        .rank-progress {
            border-top: 1px solid #dbeafe;
            color: #334155;
            line-height: 1.7;
            margin-top: 12px;
            padding-top: 10px;
        }
        .rank-progress-title {
            font-weight: 700;
            margin-bottom: 4px;
        }
        .training-card {
            background: linear-gradient(180deg, #fffaf0 0%, #ffffff 100%);
            border: 1px solid #e8c36a;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(124, 74, 3, 0.08);
            padding: 20px 22px;
            margin: 16px 0 20px;
        }
        .training-title {
            color: #7c4a03;
            font-size: 1.35rem;
            font-weight: 700;
            margin-bottom: 12px;
        }
        .training-section {
            color: #475569;
            font-size: 0.9rem;
            font-weight: 700;
            margin-top: 12px;
            margin-bottom: 4px;
        }
        .training-text {
            color: #111827;
            line-height: 1.65;
        }
        .skill-list {
            color: #0f172a;
            font-weight: 700;
            line-height: 1.8;
            margin: 4px 0 8px;
        }
        .comment-block {
            background: #f8fafc;
            border-left: 4px solid #93c5fd;
            border-radius: 6px;
            margin-top: 8px;
            padding: 10px 12px;
        }
        .achievement-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 8px 0 18px;
        }
        .achievement-badge {
            background: linear-gradient(180deg, #fff7ed 0%, #ffedd5 100%);
            border: 1px solid #fb923c;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(154, 52, 18, 0.08);
            color: #7c2d12;
            font-weight: 700;
            padding: 10px 12px;
        }
        .locked-achievement {
            border-bottom: 1px solid #e5e7eb;
            color: #64748b;
            line-height: 1.7;
            padding: 10px 0;
        }
        .locked-title {
            color: #334155;
            font-weight: 700;
        }
        .character-icon-fallback {
            font-size: 3.5rem;
            line-height: 1;
            text-align: center;
        }
        .character-talk-card {
            display: block;
            margin: 6px 0;
            width: 100%;
        }
        .character-header {
            align-items: center;
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-bottom: 6px;
            text-align: center;
        }
        .character-portrait {
            align-items: center;
            display: flex;
            justify-content: center;
            min-height: 108px;
            width: 100%;
            overflow: visible;
        }
        .character-portrait img {
            display: block;
            height: 108px;
            max-width: 108px;
            object-fit: contain;
            width: 100%;
        }
        .character-name {
            color: #334155;
            font-size: 1.05rem;
            font-weight: 800;
            margin: 0;
            white-space: nowrap;
        }
        .speech-bubble {
            border: 1px solid #dbe3ef;
            border-radius: 14px;
            box-sizing: border-box;
            color: #111827;
            font-size: 1rem;
            line-height: 1.75;
            margin: 0 auto;
            max-width: 100%;
            padding: 13px 15px;
            position: relative;
            white-space: normal;
            word-break: normal;
            overflow-wrap: break-word;
            width: 100%;
        }
        .speech-bubble::before {
            border-bottom: 12px solid #dbe3ef;
            border-left: 9px solid transparent;
            border-right: 9px solid transparent;
            content: "";
            left: 50%;
            position: absolute;
            top: -12px;
            transform: translateX(-50%);
        }
        .speech-bubble::after {
            border-bottom: 11px solid #ffffff;
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            content: "";
            left: 50%;
            position: absolute;
            top: -10px;
            transform: translateX(-50%);
        }
        .speech-senpai {
            background: #fff7ed;
            border-color: #fdba74;
        }
        .speech-senpai::before {
            border-bottom-color: #fdba74;
        }
        .speech-senpai::after {
            border-bottom-color: #fff7ed;
        }
        .speech-analyst {
            background: #f0f9ff;
            border-color: #93c5fd;
        }
        .speech-analyst::before {
            border-bottom-color: #93c5fd;
        }
        .speech-analyst::after {
            border-bottom-color: #f0f9ff;
        }
        .speech-kanaloa {
            background: #f0fdf4;
            border-color: #86efac;
        }
        .speech-kanaloa::before {
            border-bottom-color: #86efac;
        }
        .speech-kanaloa::after {
            border-bottom-color: #f0fdf4;
        }
        @media (max-width: 640px) {
            .character-portrait img {
                height: 94px;
                max-width: 86px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_grade(grade: object) -> str:
    """Show A/B/C grades with Japanese training labels."""
    grade_text = str(grade)
    return f"{grade_text}：{GRADE_LABELS.get(grade_text, grade_text)}"


def localize_log(log: pd.DataFrame) -> pd.DataFrame:
    """Return a Japanese-labeled copy of the decision log for display."""
    if log.empty:
        return log

    display_log = log.copy()
    display_log["ai_grade"] = display_log["ai_grade"].map(
        lambda grade: format_grade(grade)
    )
    display_log["decision"] = display_log["decision"].map(
        lambda decision: DECISION_LABELS.get(decision, decision)
    )
    display_log["emotional_state"] = display_log["emotional_state"].map(
        lambda emotion: EMOTION_LABELS.get(emotion, emotion)
    )

    column_labels = {
        "date": "日付",
        "race_name": "レース名",
        "ai_grade": "AI判定",
        "decision": "判断",
        "confidence": "自信度",
        "emotional_state": "感情状態",
        "recommended_bet": "推奨購入額",
        "actual_bet": "実際の購入額",
        "result_amount": "払戻額",
        "profit_loss": "損益",
        "bankroll_before": "レース前資金",
        "odds": "単勝オッズ",
        "estimated_edge": "推定エッジ（%）",
        "thesis": "期待値の根拠メモ",
        "ai_reason": "AIコメント",
        "reflection": "振り返りメモ",
    }
    return display_log.rename(columns=column_labels)


def character_image_path(character_key: str) -> Path | None:
    """Return a character image path when the file exists."""
    image_path = Path(CHARACTERS[character_key]["image"])
    return image_path if image_path.exists() else None


def character_image_data_uri(character_key: str) -> str | None:
    """Return a base64 data URI for a character image when available."""
    image_path = character_image_path(character_key)
    if image_path is None:
        return None
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_character_comment(character_key: str, comment: str) -> None:
    """Render one character comment with image fallback."""
    character = CHARACTERS[character_key]
    image_uri = character_image_data_uri(character_key)
    safe_name = html.escape(character["name"])
    safe_comment = html.escape(comment)
    safe_icon = html.escape(character["icon"])

    if image_uri:
        portrait_html = f'<img src="{image_uri}" alt="{safe_name}">'
    else:
        portrait_html = f'<div class="character-icon-fallback">{safe_icon}</div>'

    with st.container(border=True):
        st.markdown(
            f"""
            <div class="character-talk-card">
              <div class="character-header">
                <div class="character-name">{safe_name}</div>
                <div class="character-portrait">{portrait_html}</div>
              </div>
              <div class="speech-bubble speech-{character_key}">「{safe_comment}」</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_character_talk(comments: dict[str, str]) -> None:
    """Render the three character comments vertically."""
    for character_key in ["senpai", "analyst", "kanaloa"]:
        if character_key in comments:
            render_character_comment(character_key, comments[character_key])


def get_pre_decision_character_comments(
    ai_grade: str,
    emotional_state: str,
    confidence_level: int,
    recommended_bet: float,
) -> dict[str, str]:
    """Return pre-decision comments based on the current race setup."""
    if confidence_level <= 2:
        return {
            "senpai": "自信ないのに買うの、昔の俺すぎるな……。",
            "analyst": "自信度が低い場合、期待値の見積もり誤差が大きくなります。無理に買う必要はありません。",
            "kanaloa": "わからない時に見送れる人が、長期戦で残ります。",
        }

    if emotional_state == "取り返したい":
        return {
            "senpai": "次で取り返せば実質ノーダメ……って言いたいけど、それ毎回フラグなんだよな。",
            "analyst": "前の損失を基準にすると、判断の独立性が崩れます。期待値ではなく感情で買いやすい状態です。",
            "kanaloa": "今日は利益を取り返す日ではありません。ルールを守る日です。",
        }

    if ai_grade == "A":
        return {
            "senpai": "これは勝負候補だな！……でも調子に乗って張りすぎるなよ、俺。",
            "analyst": "A判定です。根拠が揃っているなら、推奨額の範囲で検討できます。",
            "kanaloa": "勝負する時も、資金管理が先です。大きく勝つより、崩れないことを優先しましょう。",
        }
    if ai_grade == "B":
        return {
            "senpai": "夢はあるけど、ちょっと迷うな……こういう時の“少しだけ”が怖いんだよな。",
            "analyst": "B判定は監視候補です。期待値は残りますが、購入するなら小さく、迷うなら見送りが妥当です。",
            "kanaloa": "見送っても機会損失とは限りません。資金を残せば、次の好機を待てます。",
        }
    return {
        "senpai": "え、見送り？……でもここで無理に振ると、だいたいロクなことないんだよな。",
        "analyst": "C判定です。根拠・自信度・感情面のどれかに不安があります。見送りは合理的です。",
        "kanaloa": "ボール球を振らないことも、投資家の技術です。",
    }


def show_chasing_loss_warning() -> None:
    """Show a training event when the user feels like chasing losses."""
    st.warning("⚠️ 取り返したい日の罠")
    with st.container(border=True):
        st.markdown("**取り返したい日は、勝負の日ではありません。余白を守る日です。**")
        render_character_talk(
            {
                "senpai": "次で取り返せば実質ノーダメだろ！……って言いたいけど、それ毎回フラグなんだよな。",
                "analyst": "前の損失を基準にすると、判断の独立性が崩れます。期待値ではなく感情で買いやすい状態です。",
                "kanaloa": "今日は利益を取り返す日ではありません。ルールを守る日です。見送れたなら、それは大きな勝利です。",
            }
        )


def build_reflection_template(decision: str, emotional_state: str) -> str:
    """Build a reflection note template from the current form choices."""
    lines = [
        "今日の判断：",
        decision,
        "",
        "判断理由：",
        "なぜ買う、または見送る判断をしたか：",
        "",
        "感情状態：",
        emotional_state,
        "",
        "守れたルール：",
        "推奨額を守れたか、見送り判断ができたか：",
        "",
    ]
    if emotional_state == "取り返したい":
        lines.extend(
            [
                "取り返したい衝動への対処：",
                "今日、自分は衝動にどう対応したか：",
                "",
            ]
        )
    lines.extend(
        [
            "次回への改善：",
            "次に同じ場面が来たらどうするか：",
        ]
    )
    return "\n".join(lines)


def build_training_result(
    entry: dict[str, object],
    evaluation: dict[str, object],
    before_status: pd.Series,
    after_status: pd.Series,
    new_achievements: list[str],
) -> dict[str, object]:
    """Create the post-save game feedback card."""
    decision = str(entry["decision"])
    confidence = int(entry["confidence"])
    actual_bet = float(entry["actual_bet"])
    recommended_bet = float(entry["recommended_bet"])
    emotional_state = str(entry["emotional_state"])
    reflection = str(entry.get("reflection", "")).strip()
    grade = str(evaluation["ai_grade"])

    if emotional_state == "取り返したい" and decision == "見送り":
        action = "取り返したい衝動に勝ちました。これは今日もっとも価値のある判断です。"
    elif emotional_state == "取り返したい" and decision == "購入" and actual_bet > recommended_bet:
        action = "取り返したい日に推奨額を超えました。期待値より感情が強くなっていた可能性があります。"
    elif grade == "C" and decision == "見送り":
        action = "ボール球を見送りました。これは勝利と同じ価値のある判断です。"
    elif grade == "B" and confidence <= 2 and decision == "見送り":
        action = "期待値はありそうでも、決め手が弱い場面で余白を守れました。"
    elif grade == "A" and decision == "購入" and actual_bet <= recommended_bet:
        action = "勝負候補をルール内の金額で購入できました。"
    elif decision == "購入" and actual_bet > recommended_bet:
        action = "期待値があっても、資金管理を崩すと長期戦では危険です。"
    elif decision == "見送り":
        action = "迷いのあるレースで資金を守りました。長期戦では大切な判断です。"
    else:
        action = "購入判断を記録できました。次は結果よりもプロセスを振り返りましょう。"

    score_changes = []
    for key, label in SCORE_LABELS.items():
        before = float(before_status.get(key, 50.0))
        after = float(after_status.get(key, 50.0))
        delta = round(after - before, 1)
        if delta != 0:
            score_changes.append(
                {
                    "label": label,
                    "before": round(before, 1),
                    "after": round(after, 1),
                    "delta": delta,
                }
            )

    if not score_changes:
        score_changes.append(
            {
                "label": "プロセス評価",
                "before": round(float(before_status.get("investor_score", 50.0)), 1),
                "after": round(float(after_status.get("investor_score", 50.0)), 1),
                "delta": round(
                    float(after_status.get("investor_score", 50.0))
                    - float(before_status.get("investor_score", 50.0)),
                    1,
                ),
            }
        )

    if emotional_state == "取り返したい" and decision == "見送り":
        senpai = "買わずに耐えたのか……それ普通に強いな。俺なら高配当の幻を見てたかもしれん。"
    elif emotional_state == "取り返したい" and decision == "購入" and actual_bet > recommended_bet:
        senpai = "取り返したい日に上乗せ購入は危ないぞ。俺もその道で何回も転んだ。今日は反省メモ案件だ。"
    elif decision == "見送り" and actual_bet == 0:
        senpai = "え、買わないの！？……でも資金が減ってないの、地味に強いな。高配当だけ見てた昔の俺なら買ってた。"
    elif decision == "購入" and actual_bet <= recommended_bet:
        senpai = "買ったのか！いいねえ。しかも推奨額以内？俺より大人じゃん。いや、俺も少しずつ成長中だけど。"
    else:
        senpai = "高配当の匂いで手が伸びる気持ちは分かる。でも推奨額オーバーは財布に回し蹴りしてるのと同じだぞ。"

    if emotional_state == "取り返したい" and decision == "購入" and actual_bet > recommended_bet:
        analyst = "感情状態が取り返したいで、購入額が推奨額を超えています。ルール遵守と感情コントロールの両面でリスクが高い判断です。"
    elif emotional_state == "取り返したい" and decision == "見送り":
        analyst = "前の損失から判断を切り離せています。感情リスクが高い場面での見送りは、非常に合理的です。"
    elif grade == "A" and decision == "購入" and actual_bet <= recommended_bet:
        analyst = "A判定かつ購入額は推奨範囲内です。期待値判断と資金管理の両方で合理性があります。"
    elif grade == "A":
        analyst = "A判定は勝負候補です。ただし自信度と購入額の上限管理をセットで見る必要があります。"
    elif grade == "B" and confidence <= 2 and decision == "見送り":
        analyst = "B判定かつ自信度が低い場面です。見送りは合理的な選択です。"
    elif grade == "B":
        analyst = "B判定は監視候補です。期待値は残りますが、購入するなら小さく、迷うなら見送りが妥当です。"
    else:
        analyst = "C判定は見送り候補です。判定、自信度、資金管理の観点から、買わない判断に合理性があります。"

    if emotional_state == "取り返したい" and decision == "見送り":
        kanaloa = "今日は利益を取り返す日ではありませんでした。ルールを守る日でした。見送れたなら、それは大きな勝利です。"
    elif emotional_state == "取り返したい" and decision == "購入" and actual_bet > recommended_bet:
        kanaloa = "取り返したい日の購入は、判断を曇らせます。次は購入前に一度止まり、余白と上限額を確認しましょう。"
    elif confidence <= 2 and decision == "見送り":
        kanaloa = "買わない判断も投資です。余白を守れたことが、今日の成果です。"
    elif actual_bet > recommended_bet:
        kanaloa = "期待値が見えても、資金管理を崩すと長期戦では苦しくなります。次は上限を守る判断まで含めて修行しましょう。"
    else:
        kanaloa = "今日の判断は記録できました。結果だけでなく、余白、資金管理、感情の安定を次の一手につなげましょう。"

    if new_achievements:
        kanaloa = "新しい称号を獲得しました。これは一回の結果ではなく、積み上げた判断の証です。"

    return {
        "action": action,
        "score_changes": score_changes,
        "new_achievements": new_achievements,
        "reflection_note": "" if reflection else "振り返りメモが短い、または空欄のため、振り返り力は伸びませんでした。",
        "senpai": senpai,
        "analyst": analyst,
        "kanaloa": kanaloa,
    }


def show_training_result(result: dict[str, object]) -> None:
    """Render the training result card shown after saving a decision."""
    change_lines = []
    for change in result["score_changes"]:
        sign = "+" if change["delta"] >= 0 else ""
        change_lines.append(
            f'<div>・{change["label"]}：'
            f'{change["before"]:.1f} → {change["after"]:.1f}'
            f'（{sign}{change["delta"]:.1f}）</div>'
        )
    change_html = "".join(change_lines)
    reflection_note_html = ""
    if result.get("reflection_note"):
        reflection_note_html = f'<div class="training-text">{result["reflection_note"]}</div>'
    achievement_html = ""
    if result.get("new_achievements"):
        badges = "".join(
            f'<div class="achievement-badge">「{title}」</div>'
            for title in result["new_achievements"]
        )
        achievement_html = f"""
          <div class="training-section">🏅 新しい称号を獲得！</div>
          <div class="achievement-list">{badges}</div>
        """
    st.markdown(
        f"""
        <div class="training-card">
          <div class="training-title">🏇 今回の修行結果</div>
          {achievement_html}
          <div class="training-section">今回の行動評価</div>
          <div class="training-text">{result["action"]}</div>
          <div class="training-section">📈 スコア変化（保存前 → 保存後）</div>
          <div class="skill-list">{change_html}</div>
          <div class="training-text">※表示は保存前 → 保存後の実スコア差分です。総合スコアには重み付き計算で反映されます。</div>
          {reflection_note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**💬 キャラクターコメント**")
    render_character_talk(
        {
            "senpai": result["senpai"],
            "analyst": result["analyst"],
            "kanaloa": result["kanaloa"],
        }
    )


def format_rank_progress(progress: dict[str, object] | None) -> str:
    """Build the next-rank requirement text shown inside the rank card."""
    if progress is None:
        return """
          <div class="rank-progress">
            <div class="rank-progress-title">最高ランク到達</div>
            <div>すべてのランク条件を達成しています。</div>
          </div>
        """

    lines = []
    for condition in progress["conditions"]:
        if condition["achieved"]:
            status = "達成"
        elif condition["unit"] == "レース":
            status = f'あと{int(condition["remaining"])}レース'
        else:
            status = f'あと{condition["remaining"]:.1f}pt'
        lines.append(f'<div>・{condition["label"]}：{status}</div>')

    return f"""
      <div class="rank-progress">
        <div class="rank-progress-title">次のランク：{progress["next_rank"]}</div>
        <div>必要条件：</div>
        {''.join(lines)}
      </div>
    """


def show_metric_row(status: pd.Series, race_count: int) -> None:
    """Render the main player dashboard metrics."""
    scores = {
        "investor_score": float(status["investor_score"]),
        "skip_skill": float(status["skip_skill"]),
        "rule_discipline": float(status["rule_discipline"]),
        "expected_value_judgment": float(status["expected_value_judgment"]),
        "bankroll_stability": float(status["bankroll_stability"]),
        "emotional_control": float(status["emotional_control"]),
        "reflection_consistency": float(status["reflection_consistency"]),
    }
    rank_progress = get_next_rank_progress(scores, race_count)
    progress_html = format_rank_progress(rank_progress)

    st.markdown(
        f"""
        <div class="rank-card">
          <div class="rank-label">投資家ランク</div>
          <div class="rank-value">{status["investor_rank"]}</div>
          {progress_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("投資家スコア", f'{status["investor_score"]:.1f}')
    col2.metric("現在の資金", f'{status["current_bankroll"]:,.0f}円')
    col3.metric("記録レース数", race_count)


def show_score_breakdown(status: pd.Series) -> None:
    """Render process score components."""
    st.subheader("プロセススコア内訳")
    score_items = [
        ("見送り力", "skip_skill"),
        ("ルール遵守力", "rule_discipline"),
        ("期待値判断力", "expected_value_judgment"),
        ("資金管理力", "bankroll_stability"),
        ("感情コントロール力", "emotional_control"),
        ("振り返り力", "reflection_consistency"),
    ]
    for row_start in range(0, len(score_items), 3):
        columns = st.columns(3)
        for column, (label, key) in zip(columns, score_items[row_start : row_start + 3]):
            with column.container(border=True):
                st.markdown(f"**{label}**")
                st.metric("スコア", f"{float(status[key]):.1f}", label_visibility="collapsed")


def show_achievements(log: pd.DataFrame) -> None:
    """Render acquired and locked achievements on the dashboard."""
    achievements = load_achievements()
    catalog = achievement_catalog()
    acquired_titles = set(achievements["title"].dropna())

    st.subheader("獲得称号")
    if achievements.empty:
        st.write("まだ称号はありません。最初の見送りから修行を始めましょう。")
    else:
        badge_html = "".join(
            f'<div class="achievement-badge">🏅 {title}</div>'
            for title in achievements["title"].dropna()
        )
        st.markdown(
            f'<div class="achievement-list">{badge_html}</div>',
            unsafe_allow_html=True,
        )

    locked = catalog[~catalog["title"].isin(acquired_titles)]
    if not locked.empty:
        with st.expander("未獲得の称号条件"):
            for _, row in locked.iterrows():
                progress = achievement_progress(row["rule"], log)
                if progress["remaining"] == 0:
                    progress_text = "条件達成済み。次の保存時に獲得します。"
                else:
                    progress_text = f'あと{progress["remaining"]}{progress["unit"]}'
                st.markdown(
                    f"""
                    <div class="locked-achievement">
                      <div class="locked-title">・{row["title"]}</div>
                      <div>条件：{row["condition"]}</div>
                      <div>進捗：{progress_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def show_reset_controls() -> None:
    """Render guarded controls for resetting all training data."""
    with st.sidebar:
        st.subheader("修行データ管理")
        confirmed = st.checkbox("本当にすべての修行データをリセットします")
        if st.button("修行データをリセットする", disabled=not confirmed):
            reset_training_data()
            st.session_state.pop("latest_feedback", None)
            st.session_state["reset_message"] = (
                "修行データをリセットしました。今日から新しい投資家修行を始めましょう。"
            )
            st.rerun()


def main() -> None:
    """Run the Streamlit app."""
    ensure_data_files()
    show_reset_controls()
    update_player_status()
    apply_layout_style()

    st.title("カナロア投資道場")
    st.caption("ボール球を見送れ！競馬投資家育成ゲーム")

    if "reset_message" in st.session_state:
        st.success(st.session_state.pop("reset_message"))

    status_table = load_player_status()
    status = status_table.iloc[0]
    log = load_race_log()
    update_achievements(log)

    show_metric_row(status, len(log))
    show_score_breakdown(status)
    show_achievements(log)

    st.divider()
    left, right = st.columns([1.1, 0.9])

    with left:
        if "latest_feedback" in st.session_state:
            st.success("判断ログを保存しました。投資家スコアを更新しました。")
            show_training_result(st.session_state.pop("latest_feedback"))

        st.subheader("レース判断入力")
        with st.form("race_decision_form"):
            race_date = st.date_input("日付", value=date.today())
            race_name = st.text_input("レース名", placeholder="例：東京11R")
            bankroll_before = st.number_input(
                "レース前資金",
                min_value=0.0,
                value=float(status["current_bankroll"]),
                step=1000.0,
            )
            odds = st.number_input("単勝オッズ", min_value=1.0, value=8.0, step=0.1)
            estimated_edge = st.number_input(
                "推定エッジ（%）",
                min_value=-50.0,
                max_value=100.0,
                value=5.0,
                step=1.0,
            )
            thesis = st.text_area(
                "期待値の根拠メモ",
                placeholder="なぜ購入候補なのか、またはなぜ見送るべきなのかを書いてください。",
            )
            confidence = st.slider("自信度", min_value=1, max_value=5, value=3)
            emotional_state = st.selectbox(
                "感情状態",
                ["冷静", "興奮", "取り返したい", "不安"],
            )
            if emotional_state == "取り返したい":
                show_chasing_loss_warning()

            evaluation = evaluate_race(
                bankroll=bankroll_before,
                confidence=confidence,
                estimated_edge=estimated_edge,
                odds=odds,
                emotional_state=emotional_state,
                thesis=thesis,
            )

            st.info(
                f'カナロアAI判定：{format_grade(evaluation["ai_grade"])} - {evaluation["ai_reason"]}'
            )
            with st.expander("💬 3人のひとこと", expanded=False):
                render_character_talk(
                    get_pre_decision_character_comments(
                        ai_grade=str(evaluation["ai_grade"]),
                        emotional_state=emotional_state,
                        confidence_level=confidence,
                        recommended_bet=float(evaluation["recommended_bet"]),
                    )
                )
            st.write(f'推奨購入額：{evaluation["recommended_bet"]:,.0f}円')

            decision = st.radio("判断", ["見送り", "購入"], horizontal=True)
            st.session_state["template_decision"] = decision
            st.session_state["template_emotional_state"] = emotional_state
            actual_bet_default = float(evaluation["recommended_bet"]) if decision == "購入" else 0.0
            actual_bet = st.number_input(
                "実際の購入額",
                min_value=0.0,
                value=actual_bet_default,
                step=100.0,
            )
            result_amount = st.number_input(
                "払戻額",
                help="実際に返ってきた金額です。的中なし・見送りは0円、マイナス値は入力できません。",
                min_value=0.0,
                value=0.0,
                step=100.0,
            )
            profit_loss = result_amount - actual_bet
            st.write(f"損益：{profit_loss:,.0f}円（払戻額 - 実際の購入額）")

            with st.expander("振り返りテンプレート"):
                st.markdown("**今日の判断：** 買った / 見送った")
                st.markdown("**判断理由：** なぜ買う、または見送る判断をしたか")
                st.markdown("**感情状態：** 冷静 / 興奮 / 取り返したい / 不安")
                st.markdown("**守れたルール：** 推奨額を守れたか、見送り判断ができたか")
                if emotional_state == "取り返したい":
                    st.markdown("**取り返したい衝動への対処：** 今日、自分は衝動にどう対応したか")
                st.markdown("**次回への改善：** 次に同じ場面が来たらどうするか")
                template_requested = st.form_submit_button("テンプレートを使う")

            reflection = st.text_area(
                "振り返りメモ",
                value=st.session_state.get("reflection_draft", ""),
                placeholder="このレースから何を学びましたか？",
            )

            submitted = st.form_submit_button("判断を保存")

        if template_requested:
            st.session_state["reflection_draft"] = build_reflection_template(
                decision, emotional_state
            )
            st.rerun()

        if submitted:
            if not race_name.strip():
                st.error("保存する前にレース名を入力してください。")
            else:
                entry = {
                    "date": race_date.isoformat(),
                    "race_name": race_name.strip(),
                    "bankroll_before": bankroll_before,
                    "odds": odds,
                    "estimated_edge": estimated_edge,
                    "thesis": thesis.strip(),
                    "ai_grade": evaluation["ai_grade"],
                    "ai_reason": evaluation["ai_reason"],
                    "decision": decision,
                    "confidence": confidence,
                    "emotional_state": emotional_state,
                    "recommended_bet": evaluation["recommended_bet"],
                    "actual_bet": actual_bet,
                    "result_amount": result_amount,
                    "profit_loss": profit_loss,
                    "reflection": reflection.strip(),
                }
                before_status = update_player_status(log).iloc[0]
                updated_log, after_status_table = add_race_decision(entry)
                new_achievements = update_achievements(updated_log)
                after_status = after_status_table.iloc[0]
                st.session_state["latest_feedback"] = build_training_result(
                    entry, evaluation, before_status, after_status, new_achievements
                )
                st.session_state["reflection_draft"] = ""
                st.rerun()

    with right:
        st.subheader("CSV保存情報")
        st.write("判断ログは `sample_data/race_decision_log.csv` に保存されます。")
        st.write("プレイヤー状態は `sample_data/player_status.csv` に保存されます。")

    st.divider()
    st.subheader("判断ログ")
    if log.empty:
        st.write("まだレースは記録されていません。")
    else:
        localized_log = localize_log(log)
        display_columns = [
            "日付",
            "レース名",
            "AI判定",
            "判断",
            "自信度",
            "感情状態",
            "実際の購入額",
            "払戻額",
            "損益",
        ]
        st.dataframe(localized_log[display_columns].tail(20), width="stretch", height=360)

    with st.expander("全判断ログ"):
        st.dataframe(localize_log(log), width="stretch", height=420)


if __name__ == "__main__":
    main()
