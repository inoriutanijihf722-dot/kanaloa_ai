# 画像生成AI用プロンプトテンプレート

以下の台本をもとに、X投稿用の縦型4コマ漫画画像を生成してください。

## 作品仕様

- 縦型4コマ漫画
- SNS投稿向け
- かわいいデフォルメ漫画風
- 完成した漫画イラスト風
- 日本語セリフあり
- 文字は大きく読みやすく
- スマホで見ても意味が伝わる構図
- コマごとに感情差を大きくする

## 禁止事項

- 棒人間風は禁止
- 図解風は禁止
- スライド資料風は禁止
- ラフな下書き風は禁止
- 文字を小さくしない
- セリフを吹き出しからはみ出させない
- ギャンブルを過度に煽る表現にしない

## 固定キャラクター

### カナロア君

参考画像のAI馬キャラを元にした、かわいい馬AIマスコット。

見た目：

- 栗毛
- 丸顔
- 大きな青緑の目
- 顔に白い流星
- 黒〜濃茶のふわっとしたたてがみ
- 青いスカーフ、または青いマント風の布
- 顔にシアン系の発光ライン、回路模様
- 胸元にAIメダリオン
- タブレットを持っている
- 知的で冷静、でもかわいい

役割：

- 3コマ目で冷静な正論を言う
- 4コマ目で教訓を締める

### 慎重な分析者

見た目：

- メガネの若い男性
- 青系または落ち着いた服
- 真面目
- 少し気弱
- 困り顔、冷や汗、慌て顔が似合う

役割：

- AI診断を読み上げる
- 先輩に振り回される
- 読者目線でツッコむ

### 大胆な先輩

見た目：

- 派手な服の若い男性
- 表情豊か
- 夢見るギャンブラー
- テンションが高い
- 大げさなポーズが似合う

役割：

- 2コマ目で感情のまま暴走する
- 3コマ目でカナロア君に止められる
- 4コマ目で少し学ぶ

## 台本入力欄

```text
タイトル：
サブタイトル：

1コマ目：
状況：
セリフ：

2コマ目：
状況：
セリフ：

3コマ目：
状況：
セリフ：

4コマ目：
状況：
セリフ：
```

## 完成プロンプト形式

```text
Create a polished vertical Japanese 4-panel manga comic for SNS posting.

Canvas:
- Portrait 1080x1920
- Four stacked horizontal panels
- Clean black manga panel borders
- Large readable Japanese speech balloons
- Cute, colorful, finished manga/anime illustration style
- Not stick figures, not diagram style, not slide style

Title:
「{タイトル}」

Subtitle:
「{サブタイトル}」

Characters:
- Kanaloa-kun: cute chestnut horse AI mascot based on the reference image, big blue-green eyes, white blaze, dark fluffy mane, blue scarf, cyan glowing circuit lines on cheek, AI medallion, holding a tablet, calm and intelligent.
- Cautious analyst: young man with glasses, blue-toned modest outfit, serious, timid, expressive worried face.
- Bold senpai: flashy young dream-gambler, colorful clothes, very expressive, comedic, easily overexcited.

Panel 1:
{1コマ目の状況}
Speech balloons:
{1コマ目のセリフ}

Panel 2:
{2コマ目の状況}
Speech balloons:
{2コマ目のセリフ}

Panel 3:
{3コマ目の状況}
Speech balloons:
{3コマ目のセリフ}

Panel 4:
{4コマ目の状況}
Speech balloons:
{4コマ目のセリフ}

Quality requirements:
- Japanese text must be large, clean, and readable.
- Keep all text inside speech balloons.
- Make the emotional contrast clear: expectation, runaway excitement, calm logic, realistic punchline.
- Kanaloa-kun should look close to the reference horse AI mascot.
- The comic should feel cute, funny, and rational.
- No watermark.
```

## 修正指示を作るときの型

```text
前回画像は方向性は近いですが、以下を修正してください。

- カナロア君を参考画像にもっと近づける
- 文字を大きくして吹き出し内に収める
- 2コマ目の先輩をもっと大げさに暴走させる
- 3コマ目はカナロア君を主役にして冷静な正論感を強める
- 4コマ目はかわいいオチとして、先輩のしょんぼり感とカナロア君の優しさを出す
- 棒人間風、図解風、スライド風にしない
```

