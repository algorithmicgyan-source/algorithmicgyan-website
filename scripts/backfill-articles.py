"""One-time / manual backfill: rebuild ALL news articles with full body + share bar.

- Fills missing `body` for direct-link items (via article_lib.fetch_body).
- Rebuilds every article page in data/news.json with article_lib.build_article_html.
- Injects a share bar into OLD article files that are no longer in news.json.
- Writes the updated data/news.json back.

Run from the repo root:  python3 scripts/backfill-articles.py
The 3-hourly GitHub workflow uses the same article_lib, so output matches.
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import article_lib as al

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def norm_title(t):
    t = re.sub(r"\s*[-–—|]\s*[^–—|]{0,40}$", "", t or "")
    return re.sub(r"\W+", "", t.lower())


def main():
    news_path = "data/news.json"
    all_news = json.load(open(news_path, encoding="utf-8"))

    # 0. NDTV link upgrade: Google redirect -> feedburner direct (title match),
    #    taaki inke bhi full body fetch ho sakein
    try:
        import urllib.request
        import xml.etree.ElementTree as ET
        req = urllib.request.Request(
            "https://feeds.feedburner.com/ndtvkhabar-latest",
            headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=30).read()
        fb = {}
        for it in ET.fromstring(data).find("channel").findall("item"):
            te = it.find("title")
            le = it.find("link")
            if te is not None and le is not None:
                fb[norm_title(te.text)] = le.text.strip()
        n_up = 0
        for n in all_news:
            if n.get("source") == "NDTV Khabar" and "google.com" in n.get("link", ""):
                dl = fb.get(norm_title(n.get("title", "")))
                if dl:
                    n["link"] = dl
                    n_up += 1
        print(f"NDTV links upgraded: {n_up}")
    except Exception as e:
        print(f"NDTV upgrade skipped: {e}")
    # Link-dedup (swap ke baad same story do baar na rahe)
    _seen_links, _deduped = set(), []
    for n in all_news:
        if n.get("link", "") not in _seen_links:
            _seen_links.add(n.get("link", ""))
            _deduped.append(n)
    all_news = _deduped

    # 1. Fill missing bodies (direct links only)
    n_fetched = 0
    for n in all_news:
        if not n.get("body") and "google.com" not in n.get("link", ""):
            n["body"] = al.fetch_body(n["link"])
            n_fetched += 1
            print(f"body: {n['source']} {len(n['body'])} chars — {n['title'][:50]}")
    print(f"Fetched bodies: {n_fetched}")

    # 2. Article paths + rebuild ALL articles in news.json
    for n in all_news:
        n["article"] = al.article_filename(n)
    n_built = 0
    for n in all_news:
        open(n["article"], "w").write(al.build_article_html(n, all_news))
        n_built += 1
    print(f"Rebuilt articles: {n_built}")

    # 3. Orphaned files (not in news.json anymore): inject share bar only
    known = {os.path.basename(n["article"]) for n in all_news}
    n_injected = 0
    for path in glob.glob("news/article/*.html"):
        if os.path.basename(path) not in known:
            if al.inject_share_into_file(path):
                n_injected += 1
    print(f"Injected share into orphaned articles: {n_injected}")

    # 4. Save news.json (with bodies)
    with open(news_path, "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=1)
    print("Saved data/news.json")


if __name__ == "__main__":
    main()
