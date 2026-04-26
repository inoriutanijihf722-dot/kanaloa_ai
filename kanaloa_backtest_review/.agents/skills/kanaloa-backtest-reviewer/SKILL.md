---
name: kanaloa-backtest-reviewer
description: Use when reviewing past Kanaloa AI horse-racing diagnoses after results are known, creating backtest verification notes, identifying overvalued or missed factors, proposing tag/scoring improvements, and turning lessons into X posts or 4-panel comic ideas without treating the result as prediction performance.
---

# kanaloa-backtest-reviewer

## 目的

カナロアAIの過去レース診断結果を、予想実績ではなく、AIロジック改善・タグ改善・4コマ漫画ネタ・X投稿用検証メモに変換する。

## 使うべき時

- ユーザーが「バックテスト」「過去レース検証」「検証メモ」「過剰評価」「見落とし」「タグ改善」「4コマネタ」と言った時
- 過去レースのA判定を振り返る時
- 結果判明後の検証をする時

## 必ず読むファイル

- docs/backtest_bible.md
- docs/review_rules.md
- docs/tag_improvement_rules.md
- docs/usage_guide.md
- prompts/backtest_review_prompt.md
- prompts/backtest_input_template.md
- prompts/x_post_backtest_template.md
- prompts/comic_seed_from_backtest_prompt.md

## 実行ルール

1. 必ず「結果判明後の検証であり、予想実績ではありません」と明記する
2. 的中自慢にしない
3. 買い煽りにしない
4. どの要素にAIが反応したかを見る
5. A判定が外れたら過剰評価要素を探す
6. B/C判定で好走したら見落とし要素を探す
7. 改善案は仮説として出す
8. 1件だけで強い結論を出さない
9. 4コマ化できる学びを必ず1つ以上出す
10. app.pyや本体コードには触らない
11. 馬場バイアスレポートがある場合は補助材料として参照する

## 出力形式

- 冒頭注記
- 対象レース
- AI判定
- 結果
- 判定分類
- AIが反応した要素
- 良かった判断
- 過剰評価だった可能性
- 見落とした可能性
- タグ改善案
- 加点/減点改善案
- 4コマ漫画化できる学び
- X投稿用短文
- 自分用メモ

## 禁止事項

- 予想実績として見せる
- 後出し的中自慢
- 買い煽り
- 断定的改善
- 本体コードの自動変更
