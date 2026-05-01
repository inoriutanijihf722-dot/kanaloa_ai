import re
import unicodedata
from typing import Any, Optional

EXPECTED_FIELDS = [
    "馬名",
    "性齢",
    "騎手",
    "厩舎",
    "馬主",
    "父",
    "母父",
    "人気ランク",
    "単勝オッズ",
    "複勝オッズ",
    "前走距離",
    "前走馬体重",
    "最終追い切りコース",
    "4F",
    "3F",
    "2F",
    "1F",
    "負荷",
    "成長示唆",
    "攻め解説コメント",
    "要確認項目",
]

LABEL_ALIASES = {
    "馬名": "馬名",
    "性齢": "性齢",
    "騎手": "騎手",
    "厩舎": "厩舎",
    "調教師": "厩舎",
    "馬主": "馬主",
    "父": "父",
    "母父": "母父",
    "母父(父)": "母父",
    "母父（父）": "母父",
    "人気ランク": "人気ランク",
    "推定人気ランク": "人気ランク",
    "単勝オッズ": "単勝オッズ",
    "単勝": "単勝オッズ",
    "複勝オッズ": "複勝オッズ",
    "複勝": "複勝オッズ",
    "前走距離": "前走距離",
    "前走馬体重": "前走馬体重",
    "追い切りコース": "最終追い切りコース",
    "最終追い切りコース": "最終追い切りコース",
    "4F": "4F",
    "3F": "3F",
    "2F": "2F",
    "1F": "1F",
    "負荷": "負荷",
    "成長示唆": "成長示唆",
    "攻め解説コメント": "攻め解説コメント",
    "要確認項目": "要確認項目",
}

CONFIDENCE_HIGH_FIELDS = {
    "馬名",
    "性齢",
    "騎手",
    "厩舎",
    "馬主",
    "父",
    "母父",
    "人気ランク",
    "単勝オッズ",
    "複勝オッズ",
    "前走距離",
}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return unicodedata.normalize("NFKC", str(value)).strip()


def _normalize_label(label: str) -> str:
    label = _normalize_text(label)
    label = re.sub(r"\s+", "", label)
    return LABEL_ALIASES.get(label, label)


def _first_number(value: Any, *, as_float: bool = False):
    text = _normalize_text(value)
    if not text:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        number = float(match.group(0))
        return number if as_float else int(number)
    except ValueError:
        return None


def _sex_from_sex_age(value: Any) -> Optional[str]:
    text = _normalize_text(value)
    if "牡" in text:
        return "牡"
    if "牝" in text:
        return "牝"
    if "セ" in text or "せん" in text:
        return "セ"
    return None


def _rank(value: Any) -> Optional[str]:
    text = _normalize_text(value).upper()
    return text if text in {"A", "B", "C", "D", "E"} else None


def _contains_kanaloa(value: Any) -> bool:
    text = _normalize_text(value)
    return "ロードカナロア" in text or "カナロア" in text


def parse_screenshot_text(text: str) -> dict:
    """Parse explicitly labeled screenshot transcription text.

    This parser is intentionally conservative: it only uses lines that look like
    "label: value" or "label：value" and never infers pedigree from table layout.
    """
    parsed = {field: "" for field in EXPECTED_FIELDS}
    raw_lines = str(text or "").splitlines()

    for raw_line in raw_lines:
        line = _normalize_text(raw_line)
        if not line:
            continue
        match = re.match(r"^\s*([^:：]+?)\s*[:：]\s*(.*)\s*$", line)
        if not match:
            continue
        label = _normalize_label(match.group(1))
        value = _normalize_text(match.group(2))
        if label in parsed:
            parsed[label] = value

    return parsed


def build_preview_rows(parsed: dict) -> list[dict]:
    rows = []
    for field in EXPECTED_FIELDS:
        value = _normalize_text(parsed.get(field, ""))
        confidence = 0.95 if value and field in CONFIDENCE_HIGH_FIELDS else 0.70 if value else 0.0
        status = "OK" if confidence >= 0.75 else "要確認" if value else "未読取"
        rows.append({
            "項目": field,
            "値": value,
            "confidence": confidence,
            "状態": status,
        })
    return rows


def sanitize_draft_for_session(parsed: dict) -> dict:
    """Return only safe first-horse session_state values.

    No scoring, diagnosis, saving, betting, or IPAT-related state is touched here.
    """
    draft = {}

    text_fields = {
        "馬名": "n_0",
        "馬主": "ow_0",
        "騎手": "j_0",
        "厩舎": "tr_0",
    }
    for source_key, session_key in text_fields.items():
        value = _normalize_text(parsed.get(source_key, ""))
        if value:
            draft[session_key] = value

    sex = _sex_from_sex_age(parsed.get("性齢", ""))
    if sex in {"牡", "牝", "セ"}:
        draft["s_0"] = sex

    p_dist = _first_number(parsed.get("前走距離", ""))
    if p_dist is not None:
        draft["pd_0"] = p_dist

    odds = _first_number(parsed.get("単勝オッズ", ""), as_float=True)
    if odds is not None:
        draft["o_0"] = odds

    place_odds = _first_number(parsed.get("複勝オッズ", ""), as_float=True)
    if place_odds is not None:
        draft["f_0"] = place_odds

    rank = _rank(parsed.get("人気ランク", ""))
    if rank:
        draft["r_0"] = rank

    father = parsed.get("父", "")
    mother_father = parsed.get("母父", "")
    if _contains_kanaloa(father):
        draft["t_0"] = "父カナロア"
    elif _contains_kanaloa(mother_father):
        draft["t_0"] = "母父カナロア"

    if _normalize_text(mother_father):
        draft["mf_0"] = _normalize_text(mother_father)

    growth_text = " ".join(
        _normalize_text(parsed.get(key, ""))
        for key in ["前走馬体重", "負荷", "成長示唆", "攻め解説コメント"]
    )
    if any(word in growth_text for word in ["前走馬体重+10", "+10kg", "過去最高馬体重", "馬体重増", "成長分"]):
        draft["g1_0"] = True
    if any(word in growth_text for word in ["自己ベスト", "ベスト更新", "時計自己ベスト", "坂路自己ベスト", "ベスト級"]):
        draft["g2_0"] = True
    if any(word in growth_text for word in ["成長示唆", "良化", "一歩前進", "躍動感", "集中", "状態面プラス"]):
        draft["g3_0"] = True

    return draft


def build_confirm_memo(parsed: dict) -> str:
    draft = sanitize_draft_for_session(parsed)
    label_by_key = {
        "n_0": "馬名",
        "ow_0": "馬主",
        "t_0": "タイプ",
        "s_0": "性別",
        "pd_0": "前走距離",
        "j_0": "騎手",
        "tr_0": "厩舎",
        "mf_0": "母父(父)",
        "r_0": "人気ランク",
        "o_0": "単勝",
        "f_0": "複勝",
        "g1_0": "成長サイン①",
        "g2_0": "成長サイン②",
        "g3_0": "成長サイン③",
    }
    applied = [f"- {label_by_key.get(key, key)}: {value}" for key, value in draft.items()]
    if not applied:
        applied = ["- 反映できる明示ラベルはまだありません"]

    not_applied = [
        "- テンP、上がりP、映像評価、レース基本情報、軍資金、当日バイアスは反映しません",
        "- AI診断実行、CSV保存、IPAT投票には接続しません",
    ]
    confirm = _normalize_text(parsed.get("要確認項目", "")) or "低 confidence、空欄、原文未確認の項目"

    return "\n".join([
        "反映予定項目:",
        *applied,
        "",
        "未反映項目:",
        *not_applied,
        "",
        f"要確認: {confirm}",
    ])
