# レトロRPG成績動画スキル

参考動画のような、ドット絵キャラクター・ステータス画面・黄色い点数・EXPゲージを使った縦型動画を作成します。自己ベスト更新は日本語で大きく強調し、最後に塾名を表示します。

## Codexでの使い方

このリポジトリでは `.agents/skills/retro-rpg-results-video/` に配置済みです。スキルが読み込まれる新しいタスクで、次のように依頼してください。

> $retro-rpg-results-video を使って、次の成績データで動画を作って。塾名はクスタニ塾。自己ベスト更新は目立つように表示して。
> ①柏中3年生、1学期期末テスト、5教科493点、自己ベスト更新
> ②柏中3年生、1学期期末テスト、5教科459点

ほかのリポジトリでは、同じフォルダーをそのリポジトリの `.agents/skills/` 以下に置いてください。ZIPからは `retro-rpg-results-video` フォルダーごと展開します。この保存はスキルファイルの配置であり、ChatGPT全体への自動登録ではありません。

## 内容

- `SKILL.md`：制作手順、デザイン、入力の扱い、検証、受け渡し方
- `scripts/render.py`：動画生成プログラム
- `scripts/requirements.txt`：Pythonの依存関係
- `examples/kusutani-16.json`：今回の16例

## 直接実行する場合

Python 3.10以降、FFmpeg、日本語フォントが必要です。Linuxでの手順は `SKILL.md` を参照してください。WindowsでダウンロードしたZIPを開くだけでは動画は生成されません。

```bash
python -m pip install -r .agents/skills/retro-rpg-results-video/scripts/requirements.txt
python .agents/skills/retro-rpg-results-video/scripts/render.py \
  --data .agents/skills/retro-rpg-results-video/examples/kusutani-16.json \
  --output-dir /workspace/outputs/quest-new
```

塾名・成績・自己ベストの有無・表示時間はJSONで変更できます。既定の出力は1080×1920・30fps・MP4、オリジナルのゲーム風BGM付きです。
