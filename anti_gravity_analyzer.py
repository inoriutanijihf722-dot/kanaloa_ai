import pandas as pd
import os
import re

def run_tag_analysis():
    print("\n" + "="*50)
    print("🧬 カナロアAI：タグ別組み合わせ分析（神タグ抽出）を開始...")
    print("="*50 + "\n")

    file_name = 'kanaloa_investment_log.csv'

    if not os.path.exists(file_name):
        print(f"❌ エラー: {file_name} が見つかりません。")
        return

    try:
        df = pd.read_csv(file_name, encoding='utf-8-sig')
        
        # 着順が出ているデータのみに絞る
        df['着順_num'] = pd.to_numeric(df['着順'], errors='coerce')
        df = df.dropna(subset=['着順_num']).copy()
        
        if df.empty:
            print("検証対象のデータがありません。")
            return

        df['複勝払戻'] = pd.to_numeric(df['複勝払戻'], errors='coerce').fillna(0)

        # 1. 備考欄からタグを抽出してリスト化する関数
        def extract_tags(text):
            if pd.isna(text):
                return []
            return re.findall(r'【(.*?)】', str(text))

        # タグのリストを作成
        df['タグリスト'] = df['備考'].apply(extract_tags)

        # 2. データをタグごとにバラバラに展開（Explode）
        df_exploded = df.explode('タグリスト')
        
        # タグがない行は除外
        df_exploded = df_exploded.dropna(subset=['タグリスト'])
        
        # 3. タグごとに集計（df_tagの作成）
        # 各タグの出現回数（件数）と、複勝払戻の合計を計算
        df_tag = df_exploded.groupby('タグリスト').agg(
            件数=('着順_num', 'count'),
            複勝払戻合計=('複勝払戻', 'sum')
        ).reset_index()

        # 列名を分かりやすく変更
        df_tag = df_tag.rename(columns={'タグリスト': 'タグ'})

        # 複勝回収率の計算（全頭100円買った場合）
        df_tag['投資総額'] = df_tag['件数'] * 100
        df_tag['複回収'] = (df_tag['複勝払戻合計'] / df_tag['投資総額']) * 100

        # 見やすくするために小数点以下1桁に丸める
        df_tag['複回収'] = df_tag['複回収'].round(1)

        # --- ご提案いただいた「神タグ抽出」スニペットの実装 ---
        print("🏆 【神タグ（複回収150%以上）】")
        
        # ※サンプルが少ないうちは「1件でも当たれば150%超え」になりやすいですが、
        # まずはすべて抽出します。後々「件数 >= 5」などの条件を足すと精度が上がります。
        strong_tags = df_tag[df_tag['複回収'] >= 150].sort_values(by='複回収', ascending=False)

        if not strong_tags.empty:
            # 必要な列だけを表示
            print(strong_tags[['タグ', '件数', '複回収']].to_string(index=False))
        else:
            print("該当なし")
            
        print("\n" + "="*50)

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    run_tag_analysis()