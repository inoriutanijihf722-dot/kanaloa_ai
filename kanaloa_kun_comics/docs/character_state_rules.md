# キャラクター状態管理ルール

## 目的

毎回の台本作成時に、先輩の成長段階、過去回から引き継ぐ理解、3人の役割を確認するためのルールです。

## 先輩の状態管理

- `episode_no` に応じて `phase` を自動判断する
- `phase` に応じて、先輩の理解度・暴走度・成長度を変える
- 初期ほど暴走が強い
- 中盤ほど迷いながら学ぶ
- 終盤ほど自分で判断し始める
- ただし先輩のボケ要素は消さない

## phase 判定

- episode 1〜8：Phase 1 誤解期
- episode 9〜16：Phase 2 条件確認期
- episode 17〜24：Phase 3 期待値理解期
- episode 25〜32：Phase 4 資金管理期
- episode 33以降：Phase 5 投資家思考定着期

## 先輩パラメータ

- `gambler_energy`：ギャンブラー的な暴走度 0〜100
- `investor_mind`：投資家思考 0〜100
- `self_control`：自制心 0〜100
- `learning_level`：学習度 0〜100

## 初期値

episode 1:

- gambler_energy 95
- investor_mind 5
- self_control 5
- learning_level 0

## phase ごとの目安

### Phase 1

- gambler_energy 85〜100
- investor_mind 0〜20
- self_control 0〜25
- learning_level 0〜20

### Phase 2

- gambler_energy 70〜90
- investor_mind 20〜40
- self_control 20〜45
- learning_level 20〜45

### Phase 3

- gambler_energy 55〜80
- investor_mind 40〜60
- self_control 35〜60
- learning_level 45〜65

### Phase 4

- gambler_energy 35〜65
- investor_mind 60〜80
- self_control 55〜80
- learning_level 65〜85

### Phase 5

- gambler_energy 25〜55
- investor_mind 80〜95
- self_control 75〜95
- learning_level 85〜100

## カナロア君の役割

- 毎回、最後の学びを短くまとめる
- 説教臭くしすぎない
- やさしく、冷静に、少しユーモアを入れる
- 先輩の成長を否定せず、修正する

## 分析者の役割

- 読者目線
- AI診断や状況を説明する
- 先輩にツッコむ
- カナロア君の説明を補足する
- 中盤以降は先輩の成長に気づく役も担う

## エピソードごとの成長記録

毎回の台本作成後に、以下を必ず記録します。

- その回で先輩が何を誤解したか
- 何を学んだか
- 次回以降にどの理解を引き継ぐか

記録先は `data/episode_registry.csv` と `data/character_state.json` です。
