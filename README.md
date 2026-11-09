# ランダムpixiv（randompixiv）

ボタンを押すと、pixiv のイラストをランダムで1件表示する小さなツールです。randomwikipedia の pixiv 版です。

## 使い方

- **🎲 ランダムで作品を表示**：pixiv の作品をランダムに1件取得し、画像・タイトル・作者・タグを表示します（全年齢向けのみ）。
- **pixivで作品を見る**：その作品の pixiv ページを新しいタブで開きます。
- もう一度ボタンを押すと、別の作品が表示されます。

作品の取得はサーバー側で行います。pixiv には公開のランダムAPIがないため、有志の公開API「Lolicon API」（`https://api.lolicon.app/setu/v2`）を使います（pixiv 公式のAPIではありません）。`r18=0` で取得し、さらに R-18 フラグや R-18 タグが付いた作品は引き直して表示しません。通信に失敗した場合はエラーメッセージと再試行ボタンが表示されます。

## ローカル実行

```bash
pip install -r requirements.txt
python app.py
# http://localhost:5000
```

## テスト

```bash
python -m unittest discover -s tests
```

※ テストでは外部通信を行わず、取得処理をモックに差し替えて検証します。

## Render へのデプロイ

`render.yaml` 同梱。無料プラン（free）の Web Service としてデプロイできます（healthCheckPath: `/healthz`）。
