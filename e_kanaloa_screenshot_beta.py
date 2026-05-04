"""Experimental helpers for E-rank Kanaloa screenshot input.

This module is intentionally pure and does not run OCR, save files, append to
investment logs, or assign the deep value candidate tag.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from typing import Any


POPULATION_TAG = "【Eカナロア母集団】"
DEEP_VALUE_TAG = "【ディープバリュー候補】"
KANALOA_TYPES = ("父カナロア", "母父カナロア", "その他カナロア血統")
CANDIDATE_COLUMNS = [
    "確認済み",
    "馬名",
    "レース名",
    "場",
    "R",
    "馬番",
    "性齢",
    "人気ランク",
    "単勝オッズ",
    "騎手",
    "厩舎",
    "馬主",
    "生産者",
    "父",
    "母父",
    "母母父",
    "カナロア該当タイプ",
    "備考",
    "候補判定",
    "対象外理由",
    "suggested_tag",
    "deep_value_tag",
]


def normalize_text(text: Any) -> str:
    """Normalize full-width variants and spacing for conservative parsing."""
    normalized = unicodedata.normalize("NFKC", "" if text is None else str(text))
    normalized = normalized.replace("：", ":")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    return normalized.strip()


def _compact(text: Any) -> str:
    return re.sub(r"\s+", "", normalize_text(text))


def _safe_get(record: Mapping[str, Any] | dict[str, Any], key: str) -> str:
    value = record.get(key, "") if isinstance(record, Mapping) else ""
    return normalize_text(value)


def _labeled_values(text: str) -> dict[str, str]:
    labels: dict[str, str] = {}
    for raw_line in normalize_text(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" in line:
            label, value = line.split(":", 1)
        else:
            match = re.match(
                r"^(母母父|母父|父|人気ランク|単勝オッズ|馬名|レース名|レース|場|R|レース番号|馬番|番号|性齢|騎手|厩舎|調教師|馬主|生産者|備考)\s+(.+)$",
                line,
            )
            if not match:
                continue
            label, value = match.groups()
        label = _compact(label)
        value = normalize_text(value)
        if label and value:
            labels[label] = value
    return labels


def _label_value(labels: dict[str, str], *candidates: str) -> str:
    for candidate in candidates:
        value = labels.get(_compact(candidate), "")
        if value:
            return value
    return ""


def _search(pattern: str, text: str) -> str:
    match = re.search(pattern, normalize_text(text), flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        return ""
    return next((group for group in match.groups() if group), "").strip()


def _has_kanaloa(text: Any) -> bool:
    compact = _compact(text)
    return "ロードカナロア" in compact or "カナロア" in compact


def _bloodline_segments(text: Any) -> list[str]:
    normalized = normalize_text(text)
    return [
        _compact(segment)
        for segment in re.split(r"[\n/／,，]+", normalized)
        if _compact(segment)
    ]


def detect_popularity_rank(text: Any) -> str:
    """Detect popularity rank A-E from pasted OCR/manual text."""
    normalized = normalize_text(text)
    labels = _labeled_values(normalized)
    labeled_rank = _label_value(labels, "人気ランク", "ランク")
    rank_source = labeled_rank or _search(r"人気ランク\s*:?\s*([A-EＡ-Ｅ])", normalized)
    if not rank_source:
        rank_source = _search(r"(?:^|[\s,，/])([A-EＡ-Ｅ])(?:\s|$)", normalized)
    rank_source = normalize_text(rank_source).upper()
    match = re.search(r"[A-E]", rank_source)
    return match.group(0) if match else ""


def detect_kanaloa_bloodline(text: Any) -> bool:
    """Detect Kanaloa only in pedigree-like contexts, not owner names alone."""
    normalized = normalize_text(text)
    labels = _labeled_values(normalized)
    if any(
        _has_kanaloa(_label_value(labels, label))
        for label in ("母父", "父", "母母父")
    ):
        return True

    for line in _bloodline_segments(normalized):
        if re.match(r"^(母母父|母父|父).*(ロードカナロア|カナロア)", line):
            return True
        if re.match(r"^(血統|三代血統表).*(ロードカナロア|カナロア)", line):
            return True

    return False


def classify_kanaloa_type(father: Any, damsire: Any, bloodline_text: Any) -> str:
    """Classify the strongest Kanaloa pedigree position."""
    if _has_kanaloa(damsire):
        return "母父カナロア"
    if _has_kanaloa(father):
        return "父カナロア"

    labels = _labeled_values(normalize_text(bloodline_text))
    if _has_kanaloa(_label_value(labels, "母父")):
        return "母父カナロア"
    if _has_kanaloa(_label_value(labels, "父")):
        return "父カナロア"

    for line in _bloodline_segments(bloodline_text):
        if re.match(r"^母父.*(ロードカナロア|カナロア)", line):
            return "母父カナロア"
    for line in _bloodline_segments(bloodline_text):
        if re.match(r"^(?<!母)父.*(ロードカナロア|カナロア)", line):
            return "父カナロア"

    if detect_kanaloa_bloodline(bloodline_text):
        return "その他カナロア血統"
    return ""


def is_e_kanaloa_candidate(record: Mapping[str, Any]) -> bool:
    """Return True only for rank E and Kanaloa sire/damsire/bloodline evidence."""
    rank = normalize_text(record.get("人気ランク", "")).upper()
    kanaloa_type = normalize_text(record.get("カナロア該当タイプ", ""))
    if not kanaloa_type:
        kanaloa_type = classify_kanaloa_type(
            record.get("父", ""), record.get("母父", ""), record.get("備考", "")
        )
    return rank == "E" and bool(kanaloa_type)


def _candidate_reason(record: Mapping[str, Any]) -> str:
    reasons = []
    if normalize_text(record.get("人気ランク", "")).upper() != "E":
        reasons.append("人気ランクがEではない")
    if not normalize_text(record.get("カナロア該当タイプ", "")):
        reasons.append("カナロア血統が確認できない")
    return " / ".join(reasons)


def parse_candidate_text(text: Any) -> dict[str, str]:
    """Parse one pasted OCR/manual block into candidate fields."""
    normalized = normalize_text(text)
    labels = _labeled_values(normalized)
    record = {
        "馬名": _label_value(labels, "馬名"),
        "レース名": _label_value(labels, "レース名", "レース"),
        "場": _label_value(labels, "場"),
        "R": _label_value(labels, "R", "レース番号"),
        "馬番": _label_value(labels, "馬番", "番号"),
        "性齢": _label_value(labels, "性齢"),
        "人気ランク": _label_value(labels, "人気ランク", "ランク") or detect_popularity_rank(normalized),
        "単勝オッズ": _label_value(labels, "単勝オッズ", "単勝"),
        "騎手": _label_value(labels, "騎手"),
        "厩舎": _label_value(labels, "厩舎", "調教師"),
        "馬主": _label_value(labels, "馬主"),
        "生産者": _label_value(labels, "生産者"),
        "父": _label_value(labels, "父"),
        "母父": _label_value(labels, "母父"),
        "母母父": _label_value(labels, "母母父"),
        "備考": _label_value(labels, "備考") or normalized,
    }

    if not record["単勝オッズ"]:
        record["単勝オッズ"] = _search(r"単勝(?:オッズ)?\s*:?\s*([0-9]+(?:\.[0-9]+)?)", normalized)
    if not record["性齢"]:
        record["性齢"] = _search(r"(牡\s*\d+|牝\s*\d+|セ\s*\d+|せん\s*\d+)", normalized).replace(" ", "")
    if not record["馬番"]:
        record["馬番"] = _search(r"(?:馬番|^|\s)(\d{1,2})(?:\s+|番)", normalized)
    if not record["R"]:
        record["R"] = _search(r"([0-9]{1,2}R)", normalized)
    if not record["場"]:
        record["場"] = _search(r"(東京|中山|京都|阪神|中京|小倉|福島|新潟|札幌|函館)", normalized)

    return {key: normalize_text(value) for key, value in record.items()}


def build_candidate_record(parsed_fields: Mapping[str, Any]) -> dict[str, Any]:
    """Build one editable confirmation-table row."""
    record = {column: "" for column in CANDIDATE_COLUMNS}
    for key in CANDIDATE_COLUMNS:
        if key in parsed_fields:
            record[key] = parsed_fields[key]

    bloodline_text = " / ".join(
        normalize_text(parsed_fields.get(key, ""))
        for key in ("父", "母父", "母母父", "備考", "bloodline_text")
    )
    record["人気ランク"] = normalize_text(record["人気ランク"]).upper()
    record["カナロア該当タイプ"] = classify_kanaloa_type(
        record["父"], record["母父"], bloodline_text
    )
    is_candidate = is_e_kanaloa_candidate(record)
    record["候補判定"] = "✅ 【Eカナロア母集団】候補" if is_candidate else "対象外"
    record["対象外理由"] = "" if is_candidate else _candidate_reason(record)
    record["suggested_tag"] = POPULATION_TAG if is_candidate else ""
    record["deep_value_tag"] = ""
    record["確認済み"] = bool(record.get("確認済み", False))
    return record


def build_candidate_records_from_text(text: Any) -> list[dict[str, Any]]:
    """Build records from one or more pasted blocks separated by ---."""
    normalized = normalize_text(text)
    if not normalized:
        return [build_candidate_record({})]
    blocks = [block.strip() for block in re.split(r"\n?\s*---+\s*\n?", normalized) if block.strip()]
    return [build_candidate_record(parse_candidate_text(block)) for block in blocks]


def _diagnosis_type(kanaloa_type: Any) -> str:
    normalized = normalize_text(kanaloa_type)
    if normalized in {"父カナロア", "母父カナロア"}:
        return normalized
    if normalized:
        return "次世代評価"
    return ""


def _sex_from_age(value: Any) -> str:
    normalized = normalize_text(value)
    if normalized.startswith("牡"):
        return "牡"
    if normalized.startswith("牝"):
        return "牝"
    if normalized.startswith("セ") or normalized.startswith("せん"):
        return "セ"
    return ""


def build_diagnosis_input_summary(record: Mapping[str, Any]) -> dict[str, str]:
    """Build a read-only summary for manual Kanaloa AI diagnosis input."""
    father = _safe_get(record, "父")
    damsire = _safe_get(record, "母父")
    rank = _safe_get(record, "人気ランク").upper()
    win_odds = _safe_get(record, "単勝オッズ")
    kanaloa_type = _safe_get(record, "カナロア該当タイプ")
    population_note = "【Eカナロア母集団】候補" if is_e_kanaloa_candidate(record) else "対象外"
    bloodline_note = " / ".join(
        part
        for part in [
            f"父:{father}" if father else "",
            f"母父:{damsire}" if damsire else "",
            f"タイプ:{kanaloa_type}" if kanaloa_type else "",
            f"人気:{rank}" if rank else "",
            f"単勝:{win_odds}" if win_odds else "",
        ]
        if part
    )
    note = population_note
    if bloodline_note:
        note = f"{note} {bloodline_note}"

    return {
        "馬名": _safe_get(record, "馬名"),
        "馬主": _safe_get(record, "馬主"),
        "タイプ": _diagnosis_type(kanaloa_type),
        "性別": _sex_from_age(record.get("性齢", "")),
        "騎手": _safe_get(record, "騎手"),
        "厩舎": _safe_get(record, "厩舎"),
        "母父(父)": damsire or father,
        "人気": rank,
        "単勝": win_odds,
        "備考": note,
    }


def format_diagnosis_input_summary(record: Mapping[str, Any]) -> str:
    """Format one diagnosis input summary as copy-friendly text."""
    summary = build_diagnosis_input_summary(record)
    return "\n".join(f"{key}: {value}" for key, value in summary.items())


def _safe_float(value: Any) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def build_first_horse_draft(record: Mapping[str, Any]) -> dict[str, Any]:
    """Build safe session_state draft values for the first diagnosis horse only."""
    summary = build_diagnosis_input_summary(record)
    draft: dict[str, Any] = {}
    text_fields = {
        "馬名": "n_0",
        "馬主": "ow_0",
        "騎手": "j_0",
        "厩舎": "tr_0",
        "母父(父)": "mf_0",
    }
    for source_key, session_key in text_fields.items():
        value = normalize_text(summary.get(source_key, ""))
        if value:
            draft[session_key] = value

    option_fields = {
        "タイプ": ("t_0", {"父カナロア", "母父カナロア", "次世代評価"}),
        "性別": ("s_0", {"牡", "牝", "セ"}),
        "人気": ("r_0", {"A", "B", "C", "D", "E"}),
    }
    for source_key, (session_key, allowed) in option_fields.items():
        value = normalize_text(summary.get(source_key, ""))
        if value in allowed:
            draft[session_key] = value

    win_odds = _safe_float(summary.get("単勝", ""))
    if win_odds is not None:
        draft["o_0"] = win_odds

    return draft
