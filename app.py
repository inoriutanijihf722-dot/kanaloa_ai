import streamlit as st
import pandas as pd
import re
import os
import math
import numpy as np
from datetime import datetime

# ======================================================
# 🚀 1. ページ構成・UI設定
# ======================================================
st.set_page_config(page_title="Kanaloa AI Pro Ver13.5", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { border-radius: 8px; font-weight: bold; background-color: #28a745; color: white; height: 3em; }
    .stTabs [aria-selected="true"] { background-color: #007bff !important; color: white !important; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏇 Kanaloa AI Pro Ver13.5")
st.caption(f"システム稼働時刻: {datetime.now().strftime('%Y/%m/%d %H:%M')} | 物理条件・前後バイアス完成版")

# ======================================================
# ⚙️ 2. 設定・データヒーリング機能
# ======================================================
HISTORY_FILE = 'kanaloa_investment_log.csv'

REQUIRED_COLUMNS = [
    '日付', '場', 'レース名', '馬名', '馬主', '投資判定', '予想期待値', '複勝期待値',
    '推奨額', '適用要素', '人気ランク', '単勝オッズ', '複勝オッズ',
    '厩舎', '騎手', '着順', '単勝払戻', '複勝払戻', '備考'
]

base_weights = {
    "父カナロア": 20, "母父カナロア": 15, "黄金A(ディープ)": 35,
    "黄金B(クロフネ)": 30, "黄金C(ダイワメジャー)": 5,
    "梅田智之": 15, "安田翔伍": 15, "本田優": 15, "手塚貴久": 15,
    "西村淳也": 20, "岩田望来": 20, "横山和生": 15, "松若風馬": 15,
    "テンP15": 20, "テンP30": 8, "上がりP15": 15, "内枠ボーナス": 8, "短縮ショック": 15
}

NICK_SCORES = {
    ("キタサンブラック", "芝"): 40,
    ("オルフェーヴル", "芝"): 35,
    ("ミッキーアイル", "ダート"): 45,
    ("ジャスタウェイ", "ダート"): 50,
    ("リアルスティール", "ダート"): -50
}

def load_history():
    if os.path.exists(HISTORY_FILE) and os.path.getsize(HISTORY_FILE) > 0:
        try:
            df = pd.read_csv(HISTORY_FILE)
        except Exception:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)

        modified = False
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                if col in ['馬主', '人気ランク', '厩舎', '騎手', '備考']:
                    df[col] = "未設定"
                elif any(x in col for x in ['期待値', '推奨額', '払戻', 'オッズ']):
                    df[col] = 0.0
                else:
                    df[col] = ""
                modified = True

        if modified:
            try:
                df.to_csv(HISTORY_FILE, index=False, encoding='utf-8-sig')
            except Exception:
                pass
        return df

    return pd.DataFrame(columns=REQUIRED_COLUMNS)

def save_history(df):
    try:
        df.to_csv(HISTORY_FILE, index=False, encoding='utf-8-sig')
    except Exception:
        st.error("⚠️ 保存失敗: CSVが別のアプリで開かれている可能性があります。")

def get_adaptive_weights():
    weights = base_weights.copy()
    df_h = load_history()
    if df_h.empty:
        return weights

    try:
        df_h['着順_num'] = pd.to_numeric(df_h['着順'], errors='coerce')
        for f in weights.keys():
            pat = f"(?<!母){re.escape(f)}" if f == "父カナロア" else re.escape(f)
            rel = df_h[df_h['適用要素'].astype(str).str.contains(pat, na=False, regex=True)].dropna(subset=['着順_num'])
            if len(rel) >= 5:
                hit_rate = (rel['着順_num'] <= 3).mean()
                adj = max(0.4, min(1.6, hit_rate / 0.25))
                weights[f] = int(round(weights[f] * adj))
    except Exception:
        pass

    return weights

# ======================================================
# 🎥 3. 映像評価ロジック
# ======================================================
def get_movie_score(h, r_track, r_dist):
    score = 0
    factors = []

    bad_list = h.get('映像不利', [])
    movie_judge = h.get('映像判定', '標準')
    movie_good = h.get('映像好走', False)

    # 1. 加点ロジック
    if movie_good:
        score += 20
        factors.append("不利なし好走(+20)")

    if movie_judge == "度外視可能":
        score += 10
        factors.append("度外視可能(+10)")
    elif movie_judge == "次走狙い":
        score += 20
        factors.append("次走狙い(+20)")
    elif movie_judge == "低評価激走":
        score += 15
        factors.append("低評価激走(+15)")

    if movie_good and movie_judge == "次走狙い":
        score += 10
        factors.append("映像シナジー(+10)")

    # 2. 保存用タグ
    for tag in ["前壁", "外回し", "砂被り", "馬群嫌がる", "出遅れ", "前走展開不利"]:
        if tag in bad_list:
            factors.append(tag)

    # 3. 再現リスク減点
    if "外回し" in bad_list and r_track == "芝" and r_dist >= 1800:
        score -= 10
        factors.append("外回し継続リスク(-10)")

    if "砂被り" in bad_list and r_track == "ダート":
        score -= 8
        factors.append("砂被り適性不安(-8)")

    if "馬群嫌がる" in bad_list:
        score -= 10
        factors.append("馬群耐性不安(-10)")

    return score, factors

# ======================================================
# 💰 4. 投資計算エンジン
# ======================================================
def calculate_investment(ai_score, popular_rank, odds, f_odds, top_odds, bankroll, head_count):
    if head_count <= 10 or odds <= 0.0:
        return 0.0, 0.0, 0.0, 0

    if top_odds >= 4.0:
        d_rate = {"A": 0.22, "B": 0.13, "C": 0.10, "D": 0.07, "E": 0.04}
    elif top_odds <= 2.2:
        d_rate = {"A": 0.38, "B": 0.15, "C": 0.06, "D": 0.02, "E": 0.01}
    else:
        d_rate = {"A": 0.31, "B": 0.18, "C": 0.10, "D": 0.05, "E": 0.02}

    final_prob = min(d_rate.get(popular_rank, 0.02) * (ai_score / 100.0), 0.50)
    true_ev = (final_prob * odds) * 100

    multiplier = 2.9 if head_count >= 16 else 2.5
    place_prob = min(final_prob * multiplier, 0.92)
    place_ev = (place_prob * f_odds) * 100 if f_odds > 0 else 0

    edge = (final_prob * odds) - 1.0
    if edge > 0 and odds > 1.0:
        bet = int(min(bankroll * (edge / (odds - 1.0)) * 0.5, bankroll * 0.05) // 100) * 100
    else:
        bet = 0

    return final_prob, true_ev, place_ev, bet

# ======================================================
# 💻 5. メインUI
# ======================================================
with st.sidebar:
    st.header("📋 レース基本情報")
    r_date = st.date_input("日付").strftime('%Y/%m/%d')
    r_place = st.selectbox("場", ["中山", "東京", "京都", "阪神", "中京", "新潟", "福島", "小倉", "札幌", "函館"])
    r_num = st.text_input("レース名", "11R")
    r_track = st.radio("トラック", ["芝", "ダート"])
    r_dist = st.number_input("距離", value=1600, step=100)
    r_heads = st.number_input("頭数", value=16, min_value=1)
    bank_total = st.number_input("軍資金", value=100000)
    st.divider()
    top_odds = st.number_input("1番人気オッズ", value=3.5, step=0.1)
    t15_c = st.number_input("テンP15頭数", 0, 10, 0)
    t30_c = st.number_input("テンP30頭数", 0, 10, 0)

    # ------------------------------------------------------
    # 🚩 当日バイアス
    # ------------------------------------------------------
    st.divider()
    st.subheader("🏁 当日バイアス")
    r_speed = st.selectbox("馬場速度", ["超高速", "高速", "標準", "タフ", "極悪"], index=2)
    bias_inout = st.select_slider("内外バイアス", options=["内有利", "やや内", "フラット", "やや外", "外有利"], value="フラット")
    bias_front = st.select_slider("前後バイアス", options=["前有利", "やや前", "フラット", "やや差", "差有利"], value="フラット")

is_small_race = r_heads <= 10
pace_val = (t15_c * 2) + t30_c
p_adj, p_lbl = ((-25, "🔥 ハイ") if pace_val >= 7 else (20, "💤 スロー") if pace_val <= 2 else (0, "☁️ 平均"))

tab1, tab2, tab3 = st.tabs(["🏇 AI診断・入力", "✅ 結果入力", "📈 資産・詳細分析"])

# ======================================================
# --- Tab 1: AI診断 ---
# ======================================================
with tab1:
    if is_small_race:
        st.warning("⚠️ 10頭以下のレースは自動的にC判定（除外）となります")

    st.info(f"展開判定: {p_lbl} (補正: {p_adj}pt)")

    if 'h_count' not in st.session_state:
        st.session_state.h_count = 1

    user_inputs = []

    for i in range(st.session_state.h_count):
        with st.expander(f"🐴 馬 {i+1}", expanded=True):
            c1, c2, c3, c4, c5 = st.columns(5)
            name = c1.text_input("馬名", key=f"n_{i}")
            owner = c2.text_input("馬主", key=f"ow_{i}")
            typ = c3.selectbox("タイプ", ["父カナロア", "母父カナロア", "次世代評価"], key=f"t_{i}")
            sex = c4.selectbox("性別", ["牡", "牝", "セ"], key=f"s_{i}")
            p_dist = c5.number_input("前走距離", value=1600, key=f"pd_{i}")

            c6, c7, c8, c9 = st.columns(4)
            waku = c6.number_input("枠", 1, 8, key=f"w_{i}")
            jock = c7.text_input("騎手", key=f"j_{i}")
            trai = c8.text_input("厩舎", key=f"tr_{i}")
            msire = c9.text_input("母父(父)", key=f"mf_{i}")

            c10, c11, c12, c13, c14 = st.columns(5)
            rank = c10.selectbox("人気", ["A", "B", "C", "D", "E"], index=2, key=f"r_{i}")
            odds = c11.number_input("単勝", value=10.0, key=f"o_{i}")
            f_odds = c12.number_input("複勝", value=3.0, key=f"f_{i}")
            tp = c13.selectbox("テンP", ["なし", "15", "30", "50"], key=f"tp_{i}")
            up = c14.selectbox("上がりP", ["なし", "15", "30"], key=f"up_{i}")

            st.markdown("##### 📈 成長サイン")
            c15, c16, c17 = st.columns(3)
            g1 = c15.checkbox("①馬体重+10kg or 過去最高", key=f"g1_{i}")
            g2 = c16.checkbox("②時計自己ベスト更新", key=f"g2_{i}")
            g3 = c17.checkbox("③厩舎コメント成長示唆", key=f"g3_{i}")

            st.markdown("##### 🎥 映像評価")
            c18, c19, c20 = st.columns(3)
            movie_good = c18.checkbox("不利なし好走", key=f"mv_good_{i}")
            movie_bad = c19.multiselect(
                "不利内容",
                ["前壁", "外回し", "砂被り", "馬群嫌がる", "出遅れ", "前走展開不利"],
                key=f"mv_bad_{i}"
            )
            movie_judge = c20.selectbox(
                "総合判定",
                ["標準", "度外視可能", "次走狙い", "低評価激走"],
                key=f"mv_judge_{i}"
            )

            if name:
                user_inputs.append({
                    '名前': name,
                    '馬主': owner,
                    'タイプ': typ,
                    '性別': sex,
                    '前走距離': p_dist,
                    '枠': waku,
                    '騎手': jock,
                    '厩舎': trai,
                    '母父': msire,
                    '人気': rank,
                    '単勝': odds,
                    '複勝': f_odds,
                    'tp': tp,
                    'up': up,
                    'g1': g1,
                    'g2': g2,
                    'g3': g3,
                    '映像好走': movie_good,
                    '映像不利': movie_bad,
                    '映像判定': movie_judge
                })

    st.button("➕ 馬を追加", on_click=lambda: st.session_state.update({"h_count": st.session_state.h_count + 1}))

    if st.button("🚀 AI診断実行", type="primary", use_container_width=True):
        if not user_inputs:
            st.warning("データを入力してください")
        else:
            weights = get_adaptive_weights()
            new_recs = []

            for h in user_inputs:
                score = 80
                factors = [h['タイプ']]

                # 血統・特注ロジック
                is_road = "ロード" in str(h['馬主'])
                is_kanaloa_blood = ("カナロア" in str(h['タイプ'])) or ("カナロア" in str(h['母父']))

                if is_road and r_track == "ダート" and is_kanaloa_blood:
                    if h['性別'] in ["牡", "セ"]:
                        score += 20
                        factors.append("ロード×カナロア(牡/セ)ダート(+20)")
                    elif h['性別'] == "牝":
                        score += 10
                        factors.append("ロード×カナロア(牝)ダート(+10)")

                for (sire, track), bonus in NICK_SCORES.items():
                    if sire in str(h['母父']) and track in r_track:
                        score += bonus
                        factors.append(f"血統特注({bonus})")

                if h['前走距離'] > r_dist:
                    score += weights.get("短縮ショック", 15)
                    factors.append("短縮ショック")

                # 展開・脚質
                if h['tp'] == "15":
                    score += weights.get("テンP15", 20) + p_adj
                    factors.append("テンP15")
                    if h['枠'] <= 3:
                        score += weights.get("内枠ボーナス", 8)
                        factors.append("内枠ボーナス")
                    if p_adj > 0:
                        factors.append(f"逃げ有利(+{p_adj}pt)")
                    elif p_adj < 0:
                        factors.append(f"逃げ不利({p_adj}pt)")
                    else:
                        factors.append("逃げ(展開平均)")

                elif h['tp'] == "30":
                    score += weights.get("テンP30", 8) + int(p_adj / 2)
                    factors.append("テンP30")
                    if p_adj > 0:
                        factors.append(f"先行有利(+{int(p_adj/2)}pt)")
                    elif p_adj < 0:
                        factors.append(f"先行不利({int(p_adj/2)}pt)")
                    else:
                        factors.append("先行(展開平均)")

                elif h['tp'] == "50":
                    if p_adj < 0:
                        score += int(abs(p_adj) / 2)
                        factors.append(f"差し有利(+{int(abs(p_adj)/2)}pt)")

                if r_track == "芝" and h['up'] == '15':
                    score += weights.get("上がりP15", 15)
                    factors.append("上がりP15")
                    if p_adj < 0:
                        score += int(abs(p_adj) / 2)
                        factors.append(f"豪脚有利(+{int(abs(p_adj)/2)}pt)")
                    else:
                        factors.append("豪脚(通常)")

                # 黄金血統
                if "ディープ" in str(h['母父']) and r_track == "芝":
                    score += weights.get("黄金A(ディープ)", 35)
                    factors.append("黄金A(ディープ)")
                if "クロフネ" in str(h['母父']) and r_track == "ダート":
                    score += weights.get("黄金B(クロフネ)", 30)
                    factors.append("黄金B(クロフネ)")
                if "ダイワメジャー" in str(h['母父']):
                    score += weights.get("黄金C(ダイワメジャー)", 5)
                    factors.append("黄金C(ダイワメジャー)")

                # 騎手・厩舎
                for k in weights.keys():
                    if k in str(h['騎手']) or k in str(h['厩舎']):
                        score += weights[k]
                        factors.append(k)

                # 特殊減点
                if "カナロア" in str(h['タイプ']) and h['性別'] == "牝" and r_track == "ダート" and r_dist >= 1700:
                    score -= 25
                    factors.append("カナ牝ダ中距離(-25)")

                # ------------------------------------------------------
                # 🚩 物理条件・前後バイアス補正（完成版）
                # ------------------------------------------------------
                bias_penalty = 0

                is_high_speed = r_speed in ["超高速", "高速"]
                is_inner_fav = bias_inout in ["内有利", "やや内"]
                is_outer_fav = bias_inout in ["外有利", "やや外"]
                is_front_fav = bias_front in ["前有利", "やや前"]
                is_closer_fav = bias_front in ["差有利", "やや差"]

                # ① 高速馬場 × 内有利 → 外枠不利
                if is_high_speed and is_inner_fav:
                    if h['枠'] >= 7:
                        bias_penalty -= 5
                        factors.append("高速・内有利×外枠(-5)")
                    elif h['枠'] <= 3:
                        bias_penalty += 3
                        factors.append("高速・内有利×内枠(+3)")

                # ② 高速馬場 × 外有利 → 内枠やや不利
                if is_high_speed and is_outer_fav:
                    if h['枠'] <= 3:
                        bias_penalty -= 3
                        factors.append("高速・外有利×内枠(-3)")
                    elif h['枠'] >= 7:
                        bias_penalty += 3
                        factors.append("高速・外有利×外枠(+3)")

                # ③ 前後バイアス × 脚質補正
                # tp: 15=逃げ, 30=先行, 50=差し
                if is_front_fav:
                    if h['tp'] == "15":
                        bias_penalty += 5
                        factors.append("前有利×逃げ(+5)")
                    elif h['tp'] == "30":
                        bias_penalty += 3
                        factors.append("前有利×先行(+3)")
                    elif h['tp'] == "50":
                        bias_penalty -= 5
                        factors.append("前有利×差し(-5)")

                if is_closer_fav:
                    if h['tp'] == "15":
                        bias_penalty -= 5
                        factors.append("差し有利×逃げ(-5)")
                    elif h['tp'] == "30":
                        bias_penalty -= 3
                        factors.append("差し有利×先行(-3)")
                    elif h['tp'] == "50":
                        bias_penalty += 5
                        factors.append("差し有利×差し(+5)")

                # ④ 映像不利とのシナジー
                movie_bad_list = h.get('映像不利', [])

                if is_high_speed and is_inner_fav and "外回し" in movie_bad_list:
                    bias_penalty -= 10
                    factors.append("高速・内有利×外回し(-10)")

                if is_front_fav and "前走展開不利" in movie_bad_list and h['tp'] == "15":
                    bias_penalty += 5
                    factors.append("前有利馬場で前走展開不利見直し(+5)")

                if is_closer_fav and "前走展開不利" in movie_bad_list and h['tp'] == "50":
                    bias_penalty += 5
                    factors.append("差し有利馬場で前走展開不利見直し(+5)")

                # ⑤ 暴走防止
                bias_penalty = max(-15, min(10, bias_penalty))

                score += bias_penalty

                # バイアス情報も因子として保存
                factors.append(f"速度:{r_speed}")
                factors.append(f"内外:{bias_inout}")
                factors.append(f"前後:{bias_front}")

                # 映像評価ブロック
                movie_score, movie_factors = get_movie_score(h, r_track, r_dist)
                score += movie_score
                factors.extend(movie_factors)

                # 成長・人気ブースト
                multiplier = 1.0
                growth_count = sum([h['g1'], h['g2'], h['g3']])

                if growth_count >= 2:
                    multiplier *= 1.10
                    factors.append("成長ブースト")
                elif growth_count == 1:
                    multiplier *= 1.03
                    factors.append("成長気配")

                if h['人気'] in ["C", "D", "E"]:
                    multiplier *= 1.10
                    factors.append("穴馬ブースト")

                if "不利なし好走(+20)" in movie_factors and growth_count >= 2:
                    multiplier *= 1.08
                    factors.append("映像×成長シナジー")

                multiplier = min(multiplier, 1.45)
                final_score = int(80 + ((score - 80) * multiplier))

                prob, w_ev, p_ev, bet = calculate_investment(
                    final_score, h['人気'], h['単勝'], h['複勝'], top_odds, bank_total, r_heads
                )

                if is_small_race:
                    judge = "C (少頭数除外)"
                else:
                    judge = "A" if p_ev >= 115 and w_ev >= 125 else "B" if w_ev >= 110 else "C"

                st.write(f"### {h['名前']} [{judge}] 期待値: 単{w_ev:.1f}% / 複{p_ev:.1f}%")
                st.caption(
                    f"馬主: {h['馬主']} | "
                    f"スコア詳細: 基礎80 + 補正{score-80} × 乗算{multiplier:.2f}倍 = 最終 {final_score}pt | "
                    f"適用要素: {', '.join(factors)}"
                )

                if bet > 0:
                    st.success(f"推奨投資額: ¥{bet:,} (単複各 ¥{bet//2:,} を推奨)")

                new_recs.append({
                    '日付': r_date,
                    '場': r_place,
                    'レース名': r_num,
                    '馬名': h['名前'],
                    '馬主': h['馬主'],
                    '投資判定': judge,
                    '予想期待値': w_ev,
                    '複勝期待値': p_ev,
                    '推奨額': bet,
                    '適用要素': "|".join(factors),
                    '人気ランク': h['人気'],
                    '単勝オッズ': h['単勝'],
                    '複勝オッズ': h['複勝'],
                    '厩舎': h['厩舎'],
                    '騎手': h['騎手'],
                    '着順': "",
                    '単勝払戻': 0,
                    '複勝払戻': 0,
                    '備考': f"【速度:{r_speed}】【内外:{bias_inout}】【前後:{bias_front}】"
                })

            df_old = load_history()
            save_history(
                pd.concat([df_old, pd.DataFrame(new_recs)], ignore_index=True)
                .drop_duplicates(subset=['日付', '馬名'], keep='last')
            )
            st.success("ログ保存完了。分析タブで確認してください。")

# ======================================================
# --- Tab 2: 結果入力 ---
# ======================================================
with tab2:
    df_res = load_history()

    if df_res.empty:
        st.info("データがありません")
    else:
        pending = df_res[df_res['着順'].astype(str).str.strip().isin(["", "未設定", "nan"])].copy()

        if pending.empty:
            st.success("全結果入力済みです")
        else:
            sel = st.selectbox("結果を入力する馬を選択", pending['馬名'].unique())
            idx = df_res[df_res['馬名'] == sel].index[-1]

            with st.form("res_input"):
                c1, c2, c3 = st.columns(3)
                r_f = c1.number_input("確定着順", 1, 18, 1)
                w_f = c2.number_input("単勝払戻金", 0, 100000, 0)
                f_f = c3.number_input("複勝払戻金", 0, 10000, 0)
                new_note = st.text_area("備考（度外視、好内容など）", value=str(df_res.at[idx, '備考']).replace('nan', ''))

                if st.form_submit_button("結果を保存する"):
                    df_res.at[idx, '着順'] = str(r_f)
                    df_res.at[idx, '単勝払戻'] = w_f
                    df_res.at[idx, '複勝払戻'] = f_f
                    df_res.at[idx, '備考'] = new_note
                    save_history(df_res)
                    st.success(f"{sel} の結果を保存しました")
                    st.rerun()

# ======================================================
# --- Tab 3: 資産・詳細分析 ---
# ======================================================
with tab3:
    df_anl = load_history()

    if not df_anl.empty:
        df_anl['着順_num'] = pd.to_numeric(df_anl['着順'], errors='coerce')
        df_ok = df_anl.dropna(subset=['着順_num']).copy()

        if not df_ok.empty:
            st.header("📈 資産運用ステータス")
            df_ok['投資'] = pd.to_numeric(df_ok['推奨額'], errors='coerce').fillna(0)
            df_ok['単勝払戻'] = pd.to_numeric(df_ok['単勝払戻'], errors='coerce').fillna(0)
            df_ok['複勝払戻'] = pd.to_numeric(df_ok['複勝払戻'], errors='coerce').fillna(0)
            df_ok['回収'] = (df_ok['単勝払戻'] * (df_ok['投資'] / 200) + df_ok['複勝払戻'] * (df_ok['投資'] / 200))

            invest_total = df_ok['投資'].sum()
            return_total = df_ok['回収'].sum()

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("トータル損益", f"¥{int(return_total - invest_total):,}")
            total_recovery_str = f"{(return_total / invest_total * 100):.1f}%" if invest_total > 0 else "0.0%"
            col_b.metric("累計回収率", total_recovery_str)
            col_c.metric("勝負馬数", f"{len(df_ok)} 頭")

        st.divider()

        st.subheader("🔍 個別データ・エクスプローラー")
        col_s1, col_s2 = st.columns(2)
        search_name = col_s1.text_input("馬名または馬主で検索 (空欄で全表示)")
        filter_grade = col_s2.multiselect("判定で絞り込み", ["A", "B", "C", "C (少頭数除外)"], default=["A", "B", "C", "C (少頭数除外)"])

        display_df = df_anl.copy()

        if search_name:
            s_word = search_name.strip()
            display_df = display_df[
                display_df['馬名'].astype(str).str.contains(s_word, na=False) |
                display_df['馬主'].astype(str).str.contains(s_word, na=False)
            ]

        if filter_grade:
            display_df = display_df[display_df['投資判定'].astype(str).isin(filter_grade)]

        safe_cols = [c for c in REQUIRED_COLUMNS if c in display_df.columns]
        st.dataframe(display_df[safe_cols].sort_values('日付', ascending=False), use_container_width=True)

        if not df_ok.empty:
            st.divider()
            st.subheader("📊 判定別 実績")
            grade_stats = []

            for g in ["A", "B", "C"]:
                sub = df_ok[df_ok['投資判定'].astype(str).str.startswith(g)]
                if len(sub) > 0:
                    inv = sub['投資'].sum()
                    rec = sub['回収'].sum()
                    grade_stats.append({
                        '判定': g,
                        '件数': len(sub),
                        '複勝率': f"{(sub['着順_num'] <= 3).mean() * 100:.1f}%",
                        '回収率': f"{(rec / inv * 100):.1f}%" if inv > 0 else "0.0%"
                    })

            if grade_stats:
                st.table(pd.DataFrame(grade_stats))

            st.subheader("💡 因子別複勝パフォーマンス")
            f_res = []

            def extract_core_factor(factor_str):
                cleaned = re.sub(r'\([+-]?\d+pt\)', '', str(factor_str))
                cleaned = re.sub(r'\([+-]?\d+\)', '', cleaned)
                return cleaned.strip()

            df_ok['コア要素リスト'] = df_ok['適用要素'].astype(str).apply(
                lambda x: [extract_core_factor(f) for f in x.split("|") if f.strip() and f.strip() != "nan"]
            )

            all_core_factors = set(df_ok['コア要素リスト'].explode().dropna())
            invalid_factors = ['逃げ展開', '先行展開']

            for core_f in sorted(all_core_factors):
                if core_f in invalid_factors:
                    continue

                sub = df_ok[df_ok['コア要素リスト'].apply(lambda x: core_f in x)]

                if len(sub) >= 1:
                    f_inv = len(sub) * 100
                    f_rec = sub['複勝払戻'].sum()
                    f_rec_rate = f"{(f_rec / f_inv * 100):.1f}%" if f_inv > 0 else "0.0%"
                    f_res.append({
                        '因子': core_f,
                        '出走': len(sub),
                        '複勝率': f"{(sub['着順_num'] <= 3).mean() * 100:.1f}%",
                        '複回収': f_rec_rate
                    })

            if f_res:
                df_f_res = pd.DataFrame(f_res)
                df_f_res['sort_val'] = df_f_res['複回収'].str.replace('%', '').astype(float)
                st.table(df_f_res.sort_values('sort_val', ascending=False).drop(columns=['sort_val']).head(20))

    else:
        st.info("データがありません。診断を実行してください。")