# episode_registry.csv 使い方ガイド

## 目的

`episode_registry.csv` は、カナロアAI 4コマ漫画の各話を管理するための台帳です。

テーマ、先輩の誤解、学び、使った演出、再利用を避けたい要素を記録し、過去回との重複を防ぎます。

## 運用ルール

- 新しい台本を作る前に、必ず直近3話を確認する
- 同じテーマ、同じオチ、同じ演出を短期間で繰り返さない
- 台本作成後に `status` を更新する
- 画像生成後に `image_file` を追記する
- X投稿後に `x_post_url` を追記する
- 人間が手動で公開する前提のため、自動投稿はしない

既存の `episode_registry.csv` がある場合は上書きしません。バックアップを作ってから、不足分だけ追記します。

## 列定義

| 列名 | 説明 |
| --- | --- |
| episode_no | 第何話か |
| status | `idea` / `scripted` / `image_done` / `posted` / `skipped` |
| phase | Phase 1〜5 |
| theme | テーマ |
| title | タイトル |
| subtitle | サブタイトル |
| senpai_misunderstanding | 先輩が何を勘違いしたか |
| lesson | その回の学び |
| kanaloa_final_line | カナロア君の締めセリフ |
| used_motif | 使った演出。例：ロケット馬券、祝勝会、チェックリスト |
| forbidden_reuse | 次回以降すぐ再利用しない要素 |
| script_file | 台本ファイル |
| image_file | 画像ファイル |
| post_text_file | 投稿文ファイル |
| x_post_url | 投稿後のURL |
| notes | メモ |

## status の目安

- `idea`：テーマだけ決まっている
- `scripted`：4コマ台本ができている
- `image_done`：画像が生成済み
- `posted`：Xへ手動投稿済み
- `skipped`：欠番、または制作見送り

## 初期データ

初期データとして、以下の5話を登録します。

1. A判定の誤読
   - title: A判定の破壊力
   - lesson: A判定は全力投資の許可証ではない
   - phase: Phase 1
2. 度外視可能のワナ
   - title: 度外視可能のワナ
   - lesson: 見直すことと買うことは別
   - phase: Phase 1
3. 次走狙いの早とちり
   - title: 次走狙いの早とちり
   - lesson: 狙い馬ほど見送りも大事
   - phase: Phase 1
4. オッズを見ない病
   - title: オッズを見ない病
   - lesson: 良い馬でも安すぎれば見送り
   - phase: Phase 1
5. 見送りは敗北じゃない
   - title: 見送りは敗北じゃない
   - lesson: 買わないことで守る日もある
   - phase: Phase 1

## 追記時のチェック

新しい行を追加する前に、次を確認します。

- `episode_no` が重複していないか
- `theme` が直近3話と近すぎないか
- `used_motif` が直近3話と同じになっていないか
- `kanaloa_final_line` が過去の締めと同じすぎないか
- 先輩の理解度が phase に合っているか
