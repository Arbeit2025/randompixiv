"""ランダムpixiv（randompixiv）

ボタンを押すと、pixiv のイラストをランダムで1件表示するツール。
randomwikipedia の pixiv 版。pixiv には公開のランダムAPIがないため、
有志の公開API「Lolicon API」(api.lolicon.app) 経由でランダムな作品を
取得する（pixiv 公式のAPIではない）。表示は全年齢向けのみに限定し、
R-18 フラグや R-18 タグが付いた作品は引き直す。単一ファイル Flask。
"""
import json
import os
import urllib.parse
import urllib.request

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

API_URL = "https://api.lolicon.app/setu/v2"
USER_AGENT = "randompixiv/1.0 (personal hobby tool; Flask)"
FETCH_TIMEOUT = 15
MAX_DRAWS = 5


def _fetch_one():
    """Lolicon API からランダムな作品を1件取得して dict で返す。"""
    query = urllib.parse.urlencode({"r18": 0, "num": 1, "size": "regular"})
    req = urllib.request.Request(
        API_URL + "?" + query,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as res:
        data = json.loads(res.read().decode("utf-8"))
    items = data.get("data") or []
    if not items:
        raise ValueError("empty API response")
    item = items[0]
    pid = item.get("pid")
    title = (item.get("title") or "").strip()
    if not pid or not title:
        raise ValueError("unexpected API response")
    urls = item.get("urls") or {}
    image = urls.get("regular") or urls.get("original") or ""
    return {
        "pid": pid,
        "title": title,
        "author": (item.get("author") or "").strip(),
        "tags": [t for t in (item.get("tags") or []) if t],
        "r18": bool(item.get("r18")),
        "image": image,
        "url": "https://www.pixiv.net/artworks/%s" % pid,
    }


def _is_safe(work):
    if work.get("r18"):
        return False
    return "R-18" not in (work.get("tags") or [])


def fetch_random_work():
    """全年齢向けの作品が引けるまで最大 MAX_DRAWS 回引き直す。"""
    last = None
    for _ in range(MAX_DRAWS):
        work = _fetch_one()
        last = work
        if _is_safe(work):
            return work
    raise ValueError("no safe work drawn: %s" % (last or {}).get("pid"))


PAGE = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ランダムpixiv</title>
<style>
body{font-family:sans-serif;max-width:680px;margin:2em auto;padding:0 1em;color:#222}
h1{font-size:1.5em}
.bigbtn{display:inline-block;font-size:1.15em;padding:.7em 1.6em;margin:.6em 0;
background:#0096fa;color:#fff;border:none;border-radius:8px;cursor:pointer}
.bigbtn:hover{background:#0077cc}
.card{border:1px solid #ccc;border-radius:10px;padding:1em 1.2em;margin-top:1em}
.card img{display:block;max-width:100%;max-height:460px;margin:0 auto .8em;border-radius:6px}
.author{color:#555;font-size:.95em;margin:.2em 0}
.tags{color:#777;font-size:.85em;line-height:1.6}
.error{border:1px solid #d66;background:#fff3f3;border-radius:10px;padding:1em 1.2em;margin-top:1em}
a.read{font-weight:bold}
footer{margin-top:2em;color:#777;font-size:.85em}
</style>
</head><body>
<h1>🎨 ランダムpixiv</h1>
<p>ボタンを押すと、pixiv のイラストをランダムで1件表示します（全年齢向けのみ）。思いがけない作品との出会いをどうぞ。</p>
<form method="get" action="/random">
  <button type="submit" class="bigbtn">🎲 ランダムで作品を表示</button>
</form>
{% if work %}
<div class="card">
  {% if work.image %}<img src="{{ work.image }}" alt="{{ work.title }}">{% endif %}
  <h2>{{ work.title }}</h2>
  {% if work.author %}<p class="author">作者：{{ work.author }}</p>{% endif %}
  {% if work.tags %}<p class="tags">{{ work.tags|join(' / ') }}</p>{% endif %}
  <p><a class="read" href="{{ work.url }}" target="_blank" rel="noopener">pixivで作品を見る →</a></p>
</div>
{% elif error %}
<div class="error">
  <p>⚠️ {{ error }}</p>
  <p>通信がうまくいかなかったようです。もう一度ボタンを押してみてください。</p>
</div>
{% endif %}
<footer>作品データ：<a href="https://www.pixiv.net/" target="_blank" rel="noopener">pixiv</a> の作品を <a href="https://api.lolicon.app/" target="_blank" rel="noopener">Lolicon API</a> 経由で取得（pixiv公式APIではありません）。表示は全年齢向けのみです。</footer>
</body></html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE, work=None, error=None)


@app.route("/random")
def random_work():
    try:
        work = fetch_random_work()
    except Exception:
        return render_template_string(
            PAGE, work=None, error="作品を取得できませんでした。"
        )
    return render_template_string(PAGE, work=work, error=None)


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
