from __future__ import annotations

from e_kanaloa_screenshot_beta import (
    build_candidate_record,
    build_candidate_records_from_text,
    build_candidate_records_from_ocr_and_manual,
    build_debug_records,
    build_diagnosis_input_summary,
    build_first_horse_draft,
    classify_kanaloa_type,
    detect_popularity_rank,
    format_diagnosis_input_summary,
    is_e_kanaloa_candidate,
)


def test_rank_e_damsire_lord_kanaloa_is_candidate() -> None:
    record = build_candidate_record({"人気ランク": "E", "母父": "ロードカナロア"})

    assert is_e_kanaloa_candidate(record) is True
    assert record["カナロア該当タイプ"] == "母父カナロア"
    assert record["suggested_tag"] == "【Eカナロア母集団】"


def test_rank_e_sire_lord_kanaloa_is_candidate() -> None:
    record = build_candidate_record({"人気ランク": "E", "父": "ロードカナロア"})

    assert is_e_kanaloa_candidate(record) is True
    assert record["カナロア該当タイプ"] == "父カナロア"


def test_rank_d_damsire_lord_kanaloa_is_not_candidate() -> None:
    record = build_candidate_record({"人気ランク": "D", "母父": "ロードカナロア"})

    assert is_e_kanaloa_candidate(record) is False
    assert "人気ランクがEではない" in record["対象外理由"]


def test_rank_e_without_kanaloa_is_not_candidate() -> None:
    record = build_candidate_record({"人気ランク": "E", "父": "ノーブルミッション"})

    assert is_e_kanaloa_candidate(record) is False
    assert "カナロア血統が確認できない" in record["対象外理由"]


def test_text_with_noble_mission_and_damsire_kanaloa_detects_damsire_type() -> None:
    kanaloa_type = classify_kanaloa_type(
        "",
        "",
        "ノーブルミッション / 母父ロードカナロア",
    )

    assert kanaloa_type == "母父カナロア"


def test_full_width_half_width_spacing_variations() -> None:
    text = "人気ランク：Ｅ\n母父 ： ロードカナロア\n単勝オッズ：２３４．５"
    records = build_candidate_records_from_text(text)

    assert records[0]["人気ランク"] == "E"
    assert records[0]["単勝オッズ"] == "234.5"
    assert records[0]["カナロア該当タイプ"] == "母父カナロア"
    assert is_e_kanaloa_candidate(records[0]) is True


def test_road_hc_only_does_not_match() -> None:
    record = build_candidate_record({"人気ランク": "E", "馬主": "ロードHC", "備考": "ロードHC"})

    assert is_e_kanaloa_candidate(record) is False


def test_gd_mew_style_sample_is_candidate_without_deep_value_tag() -> None:
    record = build_candidate_record(
        {
            "馬名": "ジーディーミュウ",
            "人気ランク": "E",
            "単勝オッズ": "234.5",
            "性齢": "牝3",
            "父": "ノーブルミッション",
            "母父": "ロードカナロア",
            "騎手": "上里直汰",
            "厩舎": "柄崎将寿",
        }
    )

    assert is_e_kanaloa_candidate(record) is True
    assert record["カナロア該当タイプ"] == "母父カナロア"
    assert record["deep_value_tag"] == ""


def test_detect_popularity_rank_from_labeled_text() -> None:
    assert detect_popularity_rank("人気ランク: e") == "E"


def test_no_colon_father_noble_mission_damsire_lord_kanaloa() -> None:
    records = build_candidate_records_from_text("父 ノーブルミッション\n母父 ロードカナロア")

    assert records[0]["父"] == "ノーブルミッション"
    assert records[0]["母父"] == "ロードカナロア"
    assert records[0]["カナロア該当タイプ"] == "母父カナロア"


def test_colon_father_noble_mission_damsire_lord_kanaloa() -> None:
    records = build_candidate_records_from_text("父: ノーブルミッション\n母父: ロードカナロア")

    assert records[0]["カナロア該当タイプ"] == "母父カナロア"


def test_full_width_colon_father_noble_mission_damsire_lord_kanaloa() -> None:
    records = build_candidate_records_from_text("父：ノーブルミッション\n母父：ロードカナロア")

    assert records[0]["カナロア該当タイプ"] == "母父カナロア"


def test_no_colon_sire_lord_kanaloa_is_sire_type() -> None:
    records = build_candidate_records_from_text("父 ロードカナロア\n母父 ディープインパクト")

    assert records[0]["父"] == "ロードカナロア"
    assert records[0]["母父"] == "ディープインパクト"
    assert records[0]["カナロア該当タイプ"] == "父カナロア"


def test_rank_d_damsire_lord_kanaloa_has_damsire_type_but_not_candidate() -> None:
    records = build_candidate_records_from_text(
        "馬名 テストホース\n人気ランク D\n父 ノーブルミッション\n母父 ロードカナロア"
    )

    assert records[0]["カナロア該当タイプ"] == "母父カナロア"
    assert is_e_kanaloa_candidate(records[0]) is False
    assert "人気ランクがEではない" in records[0]["対象外理由"]


def test_owner_road_hc_only_no_colon_is_not_kanaloa_bloodline() -> None:
    records = build_candidate_records_from_text(
        "馬名 ロードクラブホース\n人気ランク E\n馬主 ロードHC\n父 キズナ\n母父 ディープインパクト"
    )

    assert records[0]["カナロア該当タイプ"] == ""
    assert is_e_kanaloa_candidate(records[0]) is False
    assert "カナロア血統が確認できない" in records[0]["対象外理由"]


def test_gd_mew_diagnosis_input_summary() -> None:
    record = build_candidate_record(
        {
            "馬名": "ジーディーミュウ",
            "馬主": "田畑 利彦",
            "人気ランク": "E",
            "単勝オッズ": "234.5",
            "性齢": "牝3",
            "父": "ノーブルミッション",
            "母父": "ロードカナロア",
            "騎手": "上里直汰",
            "厩舎": "柄崎将寿",
        }
    )
    summary = build_diagnosis_input_summary(record)

    assert summary["馬名"] == "ジーディーミュウ"
    assert summary["馬主"] == "田畑 利彦"
    assert summary["タイプ"] == "母父カナロア"
    assert summary["性別"] == "牝"
    assert summary["騎手"] == "上里直汰"
    assert summary["厩舎"] == "柄崎将寿"
    assert summary["母父(父)"] == "ノーブルミッション"
    assert summary["人気"] == "E"
    assert summary["単勝"] == "234.5"
    assert "【Eカナロア母集団】候補" in summary["備考"]
    assert record["deep_value_tag"] == ""


def test_sire_kanaloa_diagnosis_input_summary_type() -> None:
    record = build_candidate_record(
        {"人気ランク": "E", "性齢": "牡3", "父": "ロードカナロア", "母父": "Tapit"}
    )
    summary = build_diagnosis_input_summary(record)

    assert summary["タイプ"] == "父カナロア"
    assert summary["性別"] == "牡"
    assert summary["母父(父)"] == "Tapit"


def test_diagnosis_input_summary_handles_missing_sex_age() -> None:
    record = build_candidate_record({"人気ランク": "E", "母父": "ロードカナロア"})
    summary = build_diagnosis_input_summary(record)

    assert summary["性別"] == ""
    assert summary["タイプ"] == "母父カナロア"


def test_format_diagnosis_input_summary_is_copy_friendly() -> None:
    record = build_candidate_record({"馬名": "テストカナロア", "人気ランク": "E", "父": "ロードカナロア"})
    text = format_diagnosis_input_summary(record)

    assert "馬名: テストカナロア" in text
    assert "タイプ: 父カナロア" in text
    assert "備考: 【Eカナロア母集団】候補" in text


def test_gd_mew_first_horse_draft_maps_safe_keys() -> None:
    record = build_candidate_record(
        {
            "馬名": "ジーディーミュウ",
            "馬主": "田畑 利彦",
            "人気ランク": "E",
            "単勝オッズ": "234.5",
            "性齢": "牝3",
            "父": "ノーブルミッション",
            "母父": "ロードカナロア",
            "騎手": "上里直汰",
            "厩舎": "柄崎将寿",
        }
    )
    draft = build_first_horse_draft(record)

    assert draft == {
        "n_0": "ジーディーミュウ",
        "ow_0": "田畑 利彦",
        "j_0": "上里直汰",
        "tr_0": "柄崎将寿",
        "mf_0": "ノーブルミッション",
        "t_0": "母父カナロア",
        "s_0": "牝",
        "r_0": "E",
        "o_0": 234.5,
    }


def test_first_horse_draft_omits_blank_values() -> None:
    record = build_candidate_record({"人気ランク": "E", "母父": "ロードカナロア"})
    draft = build_first_horse_draft(record)

    assert "n_0" not in draft
    assert "ow_0" not in draft
    assert "o_0" not in draft
    assert draft["t_0"] == "母父カナロア"
    assert draft["r_0"] == "E"


def test_manual_override_takes_precedence_for_damsire_kanaloa() -> None:
    records = build_candidate_records_from_ocr_and_manual(
        "馬名 エナジーアユ\n人気ランク E\n父 モズアスコット\n母父 ディープインパクト\n単勝オッズ 105.8",
        "母父: ロードカナロア\nタイプ: 母父カナロア",
    )
    record = records[0]
    summary = build_diagnosis_input_summary(record)
    draft = build_first_horse_draft(record)

    assert record["母父"] == "ロードカナロア"
    assert record["dam_sire_name"] == "ロードカナロア"
    assert record["カナロア該当タイプ"] == "母父カナロア"
    assert record["form_bloodline_name"] == "モズアスコット"
    assert is_e_kanaloa_candidate(record) is True
    assert summary["母父(父)"] == "モズアスコット"
    assert draft["mf_0"] == "モズアスコット"


def test_water_bubinga_damsire_kanaloa_uses_sire_for_form_bloodline() -> None:
    records = build_candidate_records_from_ocr_and_manual(
        "馬名 ウォーターブビンガ\n人気 E\n単勝 79.7\n父 ダノンキングリー",
        "母父: ロードカナロア\nタイプ: 母父カナロア",
    )
    record = records[0]

    assert record["人気ランク"] == "E"
    assert record["カナロア該当タイプ"] == "母父カナロア"
    assert record["form_bloodline_name"] == "ダノンキングリー"
    assert is_e_kanaloa_candidate(record) is True
    assert build_first_horse_draft(record)["mf_0"] == "ダノンキングリー"


def test_debug_records_show_merged_candidate_and_reason() -> None:
    debug_rows = build_debug_records(
        "馬名 エナジーアユ\n人気ランク E\n父 モズアスコット",
        "母父: ロードカナロア\nタイプ: 母父カナロア",
    )

    merged = debug_rows[0]["merged candidate dict"]
    reason = debug_rows[0]["is_kanaloa_candidate の判定理由"]
    assert merged["dam_sire_name"] == "ロードカナロア"
    assert merged["kanaloa_type"] == "母父カナロア"
    assert reason["is_kanaloa_candidate"] is True
    assert reason["form_bloodline_name"] == "モズアスコット"
