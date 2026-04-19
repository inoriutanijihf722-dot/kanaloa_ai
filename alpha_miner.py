import pandas as pd
import os
import re
import itertools
from datetime import datetime

def run_alpha_mining():
    print("\n" + "="*70)
    print("🧬 Kanaloa Alpha Miner：未知の金脈（神コンボ）探索を起動")
    print("="*70 + "\n")

    file_name = 'kanaloa_investment_log.csv'
    output_dir = 'alpha_reports' # 分析結果を保存するフォルダ

    if not os.path.exists(file_name):
        print(f"❌ エラー: {file_name} が見つかりません。本番AIでデータを蓄積してください。")
        return

    try:
        # 1. データの読み込みとクレンジング
        df = pd.read_csv(file_name, encoding='utf-8-sig')
        
        # 💡【改善1】必須列の存在チェック（早期リターンによる安全装置）
        if '備考' not in df.columns:
            print("⚠️ '備考' 列が見つかりません。本番AIのCSV構造を確認してください。")
            return
        if '着順' not in df.columns:
            print("⚠️ '着順' 列が見つかりません。本番AIのCSV構造を確認してください。")
            return

        df['着順_num'] = pd.to_numeric(df['着順'], errors='coerce')
        df = df.dropna(subset=['着順_num']).copy()
        
        if df.empty:
            print("⚠️ 検証対象のレース結果データがありません。")
            return

        df['単勝払戻'] = pd.to_numeric(df.get('単勝払戻', 0), errors='coerce').fillna(0)
        df['複勝払戻'] = pd.to_numeric(df.get('複勝払戻', 0), errors='coerce').fillna(0)

        # 2. 備考欄からすべてのコアタグ（【】で囲まれた文字）を抽出
        def extract_tags(text):
            if pd.isna(text): return []
            # 文字列順（文字コード順）にソートして、(A,B)と(B,A)のズレを防ぐ
            return sorted(list(set(re.findall(r'【(.*?)】', str(text)))))

        df['タグリスト'] = df['備考'].apply(extract_tags)

        # 💡【改善3】分析対象となる「タグ付きレース」の可視化
        tagged_count = (df['タグリスト'].apply(len) > 0).sum()
        print(f"📊 分析対象データ: 全 {len(df)} レース中、タグ付き {tagged_count} レース")
        print("-" * 70)

        if tagged_count == 0:
            print("⚠️ タグ（【】で囲まれた文字）が入力されたレースがありません。")
            print("本番AIのCSVの「備考」欄にコアタグを入力してください。")
            return

        # 3. 評価関数の定義（元データを汚さない安全設計）
        def evaluate_combinations(combo_size, min_count, min_roi):
            df_copy = df.copy()
            df_copy['コンボ'] = df_copy['タグリスト'].apply(
                lambda tags: list(itertools.combinations(tags, combo_size)) if len(tags) >= combo_size else []
            )
            df_combo = df_copy.explode('コンボ').dropna(subset=['コンボ'])
            
            if df_combo.empty: return pd.DataFrame()
            
            stats = df_combo.groupby('コンボ').agg(
                出走数=('着順_num', 'count'),
                勝数=('着順_num', lambda x: (x == 1).sum()),
                複勝数=('着順_num', lambda x: (x <= 3).sum()),
                単勝払戻合計=('単勝払戻', 'sum'),
                複勝払戻合計=('複勝払戻', 'sum')
            ).reset_index()
            
            stats['勝率'] = (stats['勝数'] / stats['出走数'] * 100).round(1)
            stats['複勝率'] = (stats['複勝数'] / stats['出走数'] * 100).round(1)
            stats['単回収'] = (stats['単勝払戻合計'] / (stats['出走数'] * 100) * 100).round(0).astype(int)
            stats['複回収'] = (stats['複勝払戻合計'] / (stats['出走数'] * 100) * 100).round(0).astype(int)
            
            # 【厳格な足切り】指定された件数と「複勝回収率」をクリアした本物だけを残す
            strong_stats = stats[(stats['出走数'] >= min_count) & (stats['複回収'] >= min_roi)].sort_values(by='複回収', ascending=False)
            return strong_stats

        # ==========================================
        # 🔍 階層別・アルファ探索の実行 ＆ CSV保存
        # ==========================================
        os.makedirs(output_dir, exist_ok=True)
        # 💡【改善2】タイムスタンプに秒数を追加し、連続実行時の上書きを防止
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # ① 単体タグ
        print("🎯 【Tier 1】単体タグ（ベース適性） >>> 条件: 3件以上 & 複回110%超")
        single_tags = evaluate_combinations(1, 3, 110)
        if not single_tags.empty:
            single_tags['コンボ'] = single_tags['コンボ'].apply(lambda x: f"【{x[0]}】") 
            print(single_tags[['コンボ', '出走数', '勝率', '複勝率', '単回収', '複回収']].head(10).to_string(index=False))
            single_tags.to_csv(f"{output_dir}/tier1_single_{timestamp}.csv", index=False, encoding='utf-8-sig')
        else: print("  該当なし（データ蓄積待ち）")
        print("-" * 70)

        # ② ダブルコンボ
        print("⚔️ 【Tier 2】ダブルコンボ（相性爆発） >>> 条件: 3件以上 & 複回130%超")
        double_combo = evaluate_combinations(2, 3, 130)
        if not double_combo.empty:
            double_combo['コンボ'] = double_combo['コンボ'].apply(lambda x: f"【{x[0]}】×【{x[1]}】")
            print(double_combo[['コンボ', '出走数', '勝率', '複勝率', '単回収', '複回収']].head(5).to_string(index=False))
            double_combo.to_csv(f"{output_dir}/tier2_double_{timestamp}.csv", index=False, encoding='utf-8-sig')
        else: print("  該当なし（データ蓄積待ち）")
        print("-" * 70)

        # ③ トリプルコンボ
        print("👑 【Tier 3】トリプルコンボ（神の領域） >>> 条件: 3件以上 & 複回150%超")
        triple_combo = evaluate_combinations(3, 3, 150)
        if not triple_combo.empty:
            triple_combo['コンボ'] = triple_combo['コンボ'].apply(lambda x: f"【{x[0]}】×【{x[1]}】×【{x[2]}】")
            print(triple_combo[['コンボ', '出走数', '勝率', '複勝率', '単回収', '複回収']].head(5).to_string(index=False))
            triple_combo.to_csv(f"{output_dir}/tier3_triple_{timestamp}.csv", index=False, encoding='utf-8-sig')
        else: print("  該当なし（データ蓄積待ち）")

        print("\n" + "="*70)
        print(f"📁 抽出されたレポートは '{output_dir}' フォルダに保存されました。")
        print("💡 [CEOへの進言] データが50件を超えるまでは、結果を眺めるだけに留めてください。")
        print("="*70 + "\n")

    except Exception as e:
        print(f"❌ 解析エラーが発生しました: {e}")

if __name__ == "__main__":
    run_alpha_mining()