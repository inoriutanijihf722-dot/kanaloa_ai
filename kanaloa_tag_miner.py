import pandas as pd
import os
import re
import itertools

def run_tag_miner():
    print("\n" + "="*50)
    print("⛏️ カナロアAI：神タグ＆神コンボ 採掘（マイニング）開始...")
    print("="*50 + "\n")

    file_name = 'kanaloa_investment_log.csv'

    if not os.path.exists(file_name):
        print(f"❌ エラー: {file_name} が見つかりません。")
        return

    try:
        df = pd.read_csv(file_name, encoding='utf-8-sig')
        
        # --- 前処理 ---
        df['着順_num'] = pd.to_numeric(df['着順'], errors='coerce')
        df = df.dropna(subset=['着順_num']).copy()
        df['複勝払戻'] = pd.to_numeric(df['複勝払戻'], errors='coerce').fillna(0)

        if df.empty:
            print("検証対象のデータがありません。")
            return

        def extract_tags(text):
            if pd.isna(text):
                return []
            return sorted(list(set(re.findall(r'【(.*?)】', str(text)))))

        df['タグリスト'] = df['備考'].apply(extract_tags)

        # ==========================================
        # 1. 単体タグの集計（先ほど成功した機能）
        # ==========================================
        df_single = df.explode('タグリスト').dropna(subset=['タグリスト'])
        df_single_stats = df_single.groupby('タグリスト').agg(
            件数=('着順_num', 'count'),
            複勝払戻合計=('複勝払戻', 'sum')
        ).reset_index()
        
        df_single_stats['投資総額'] = df_single_stats['件数'] * 100
        df_single_stats['複回収'] = (df_single_stats['複勝払戻合計'] / df_single_stats['投資総額']) * 100
        df_single_stats['複回収'] = df_single_stats['複回収'].round(1)

        print("💎 【神タグ（単体：複回収150%以上）】")
        # 単体タグは「件数2以上」になったら本物感が出ますが、今は全て出します
        strong_single = df_single_stats[df_single_stats['複回収'] >= 150].sort_values(by='複回収', ascending=False)
        if not strong_single.empty:
            print(strong_single[['タグリスト', '件数', '複回収']].rename(columns={'タグリスト': 'タグ'}).to_string(index=False))
        else:
            print("該当なし")
        print("\n" + "-"*50)

        # ==========================================
        # 2. 組み合わせ（2タグ）の集計
        # ==========================================
        def get_combinations(tags):
            if len(tags) >= 2:
                return list(itertools.combinations(tags, 2))
            return []

        df['タグコンボ'] = df['タグリスト'].apply(get_combinations)
        df_combo = df.explode('タグコンボ').dropna(subset=['タグコンボ'])
        
        print("\n🏆 【神コンボ（2タグ：複回収150%以上 & 5件以上）】")
        if not df_combo.empty:
            df_combo[['タグ1', 'タグ2']] = pd.DataFrame(df_combo['タグコンボ'].tolist(), index=df_combo.index)
            df_combo_stats = df_combo.groupby(['タグ1', 'タグ2']).agg(
                件数=('着順_num', 'count'),
                複勝払戻合計=('複勝払戻', 'sum')
            ).reset_index()

            df_combo_stats['投資総額'] = df_combo_stats['件数'] * 100
            df_combo_stats['複回収'] = (df_combo_stats['複勝払戻合計'] / df_combo_stats['投資総額']) * 100
            df_combo_stats['複回収'] = df_combo_stats['複回収'].round(1)

            # 神コンボ抽出（件数5以上 ＆ 複回収150%以上）
            strong_combo = df_combo_stats[
                (df_combo_stats['複回収'] >= 150) & (df_combo_stats['件数'] >= 5)
            ].sort_values(by='複回収', ascending=False)

            if not strong_combo.empty:
                print(strong_combo[['タグ1', 'タグ2', '件数', '複回収']].head(10).to_string(index=False))
            else:
                print("該当なし (※現在データ蓄積中。5件以上の組み合わせ待ちです)")
        else:
            print("該当なし (タグが2つ以上あるデータがありません)")

        print("\n" + "="*50)

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    run_tag_miner()