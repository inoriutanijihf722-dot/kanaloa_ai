# kanaloa-4koma-serial

## 目的

カナロアAI 4コマ漫画の連載台本、画像生成プロンプト、投稿文、episode_registry更新案、character_state更新案を作る。

## このスキルを使うべき時

- ユーザーが「4コマ」「漫画」「カナロア君」「先輩」「次の話」「シリーズ」「ストーリー性」「量産」と言った時
- 4コマ台本を作る時
- 画像生成AI用プロンプトを作る時
- 先輩の成長段階を反映したい時
- 過去回との重複を避けたい時

## 必ず読むファイル

- `docs/serial_bible.md`
- `docs/senpai_growth_arc.md`
- `docs/character_state_rules.md`
- `docs/episode_registry_guide.md`
- `data/episode_registry.csv`
- `data/character_state.json`
- `prompts/serial_4koma_prompt_template.md`

## 実行ルール

1. まず `episode_registry.csv` を確認する
2. 次に `character_state.json` を確認する
3. `episode_no` から先輩の phase を判断する
4. 過去3話とテーマ・オチ・演出が被らないようにする
5. 先輩に毎回1つだけ学ばせる
6. 先輩を急に完璧にしない
7. カナロア君は最後に短く本質を言う
8. 分析者は読者目線でツッコミ・補足をする
9. ギャンブル煽りを避け、期待値・資金管理・検証の思想に着地する
10. 出力は必ず以下の形式にする

## 出力形式

- タイトル
- サブタイトル
- episode metadata
- 先輩の現在phase
- 先輩の今回の誤解
- 今回の学び
- 4コマ台本
- 画像生成AI用プロンプト
- X投稿文3案
- episode_registry.csv 追記用
- character_state.json 更新案
- 前作流用チェック

## 禁止事項

- 過去作のタイトル・セリフ・構図をそのまま流用しない
- 同じテーマを短期間で繰り返さない
- 「絶対勝てる」「必ず儲かる」と書かない
- 予想販売や買い煽りに寄せない
- 先輩を毎回リセットしない
- 先輩を急に完成された投資家にしない
- `app.py` や競馬AI本体に触らない
