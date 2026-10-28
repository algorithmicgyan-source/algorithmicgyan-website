"""News pipeline for the Algorithmic Gyan website — FIELD RESET 28 Oct 2026.

User decision (28 Oct 2026, permanent): general news does NOT match the
channel's field, so the visible news section is MP SPECIAL ONLY.
- MP feeds (direct, photo + full body): IBC24 + Bansal News
  -> data/news.json + data/news-archive.json + news/article/ pages.
- General direct feeds (ABP / NDTV / AajTak) are fetched ONLY to build the
  daily Current Affairs post (exam content). They are NEVER saved as news
  items and never appear on the news page.
- Facts + real motivational stories are written by a separate daily job and
  appended to data/posts.json — this script NEVER deletes non-CA posts.
- PERMANENT SAVE (user instruction): archive items and non-CA posts are
  append-only. Only today's Current Affairs slug is replaced each day.
  Old general-news article HTML files stay on disk (unlinked, harmless).

Used by BOTH:
  - .github/workflows/update-news.yml (3-hourly auto update)
  - manual runs:  python3 scripts/fetch_news.py   (from repo root)

Shares article_lib.py with scripts/backfill-articles.py.
"""
import html
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import article_lib as al

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

DESKTOP_UA = al.DESKTOP_UA

# (source label, feed url, per-run limit)
MP_FEEDS = [
    ("MP News", "https://www.ibc24.in/rss", 12),
    ("MP News", "https://bansalnews.com/feed", 12),
]
# Sirf Current Affairs post ke liye (news me SAVE NAHI honge)
CA_FEEDS = [
    ("ABP News", "https://www.abplive.com/news/india/feed", 5),
    ("NDTV Khabar", "https://feeds.feedburner.com/ndtvkhabar-latest", 5),
    ("AajTak", "https://www.aajtak.in/rss", 8),
]

BAD_TITLES = ["prati ghanta", "news on air", "hourly news"]

# MP Special filter: sirf MP se judi khabrein news page par jayengi.
# (IBC24/Bansal ke feed me national + CG khabrein bhi aati hain.)
MP_KEYWORDS = [
    'मध्य प्रदेश', 'मध्यप्रदेश', 'मप्र', 'एमपी', 'mp ',
    'भोपाल', 'इंदौर', 'ग्वालियर', 'जबलपुर', 'उज्जैन', 'रतलाम', 'रीवा',
    'सागर', 'सतना', 'देवास', 'छिंदवाड़ा', 'मंदसौर', 'नीमच', 'खंडवा',
    'बुरहानपुर', 'विदिशा', 'सीहोर', 'नर्मदापुरम', 'होशंगाबाद', 'बैतूल',
    'धार', 'झाबुआ', 'अलीराजपुर', 'बड़वानी', 'खरगोन', 'दमोह', 'छतरपुर',
    'टीकमगढ़', 'पन्ना', 'दतिया', 'भिंड', 'मुरैना', 'श्योपुर', 'गुना',
    'अशोकनगर', 'शिवपुरी', 'राजगढ़', 'शाजापुर', 'आगर', 'सिंगरौली',
    'सीधी', 'शहडोल', 'उमरिया', 'कटनी', 'नरसिंहपुर', 'बालाघाट', 'सिवनी',
    'मंडला', 'डिंडौरी', 'अनूपपुर', 'मोहन यादव', 'madhya pradesh',
    'bhopal', 'indore', 'gwalior', 'jabalpur', 'ujjain', 'mohan yadav',
]


def mp_relevant(n):
    text = (n.get("title", "") + " " + n.get("desc", "")).lower()
    return any(k in text for k in MP_KEYWORDS)


def keep_mp(n):
    """MP item rakhne layak? Google MP-feed items MP-by-construction hain;
    direct IBC24/Bansal items sirf tab jab MP keyword mile."""
    if n.get("source") != "MP News":
        return False
    if "google.com" in n.get("link", ""):
        return True
    return mp_relevant(n)


def fmt_date(pub):
    try:
        dt = parsedate_to_datetime(pub)
        ist = dt.astimezone(timezone(timedelta(hours=5, minutes=30)))
        return ist.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return (pub or "")[:11]


def clean(s):
    if not s:
        return ""
    s = html.unescape(s)
    s = re.sub(r"<[^>]+>", "", s)
    return s.strip()


def is_hindi(s):
    return any("ऀ" <= c <= "ॿ" for c in (s or ""))


def norm_title(t):
    t = re.sub(r"\s*[-–—|]\s*[^–—|]{0,40}$", "", t or "")
    return re.sub(r"\W+", "", t.lower())


def _el_text(item, tag):
    el = item.find(tag)
    return (el.text or "").strip() if el is not None else ""


def _feed_media(item):
    """Feed se photo: media:content / media:thumbnail / enclosure."""
    for el in item.iter():
        tag = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if tag in ("content", "thumbnail", "enclosure") and "url" in el.attrib:
            u = el.attrib["url"]
            if (".jpg" in u or ".png" in u or ".jpeg" in u
                    or "ndtvimg" in u or "abplive" in u) \
                    and "gstatic" not in u and "googleusercontent" not in u:
                return u
    return ""


def _regex_items(xml_text):
    """Malformed XML ke liye fallback: <item> blocks regex se nikalo."""
    out = []
    for blk in re.findall(r"<item>(.*?)</item>", xml_text, re.S):
        def _f(tag):
            m = re.search(r"<%s>(.*?)</%s>" % (tag, tag), blk, re.S)
            if not m:
                return ""
            return re.sub(r"<!\[CDATA\[|\]\]>", "", m.group(1)).strip()
        out.append({
            "title": _f("title"), "link": _f("link"),
            "pubDate": _f("pubDate"), "description": _f("description"),
            "media": "",
        })
    return out


def parse_feed(xml_text):
    """Feed items nikalo: pehle ET (saare <item> kahin bhi hon), phir regex."""
    try:
        root = ET.fromstring(xml_text)
        items = []
        for it in root.iter("item"):
            items.append({
                "title": _el_text(it, "title"),
                "link": _el_text(it, "link"),
                "pubDate": _el_text(it, "pubDate"),
                "description": _el_text(it, "description"),
                "media": _feed_media(it),
            })
        if items:
            return items
    except Exception:
        pass
    return _regex_items(xml_text)


def fetch_feed_items(name, url, limit):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": DESKTOP_UA})
        data = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
        raw = parse_feed(data)
        out = []
        for r in raw[:limit]:
            title = clean(r["title"])
            link = r["link"]
            if not title or not link:
                continue
            if any(b in title.lower() for b in BAD_TITLES):
                continue
            if not is_hindi(title):
                continue
            out.append({
                "source": name, "title": title, "link": link,
                "date": fmt_date(r["pubDate"]),
                "desc": clean(r["description"]),
                "image": r["media"],
            })
        print(f"{name}: {len(out)} fresh OK")
        return out
    except Exception as e:
        print(f"{name}: FAILED - {e}")
        return []


def body_excerpt(body, limit=800):
    """Card ke liye lamba description: poore paragraphs, ~800 chars tak."""
    out, total = [], 0
    for p in body.split("\n\n"):
        p = p.strip()
        if not p:
            continue
        if total + len(p) > limit and out:
            break
        out.append(p)
        total += len(p)
    return " ".join(out)


def enrich_mp(items):
    """MP items: direct link se poori body + photo lao."""
    for n in items:
        if "google.com" in n["link"]:
            continue
        body, img = al.fetch_article(n["link"])
        if body:
            n["body"] = body
            n["desc"] = body_excerpt(body)
        if img:
            n["image"] = img
        print(f"  enrich: {n['source']} body={len(n.get('body', ''))} "
              f"img={'Y' if n.get('image') else 'N'} — {n['title'][:45]}")
    return items


def dkey(n):
    try:
        return datetime.strptime(n.get("date", "")[:11], "%d %b %Y")
    except Exception:
        return datetime.min


def build_ca_post(today_items):
    """Aaj ka Current Affairs post (MP + National + International)."""
    IST = timezone(timedelta(hours=5, minutes=30))
    today_ca = datetime.now(IST).strftime("%d %b %Y")
    today_slug = datetime.now(IST).strftime("%Y-%m-%d")
    items = [n for n in today_items if n.get("date", "").startswith(today_ca)]
    if not items:
        print("CA post: aaj ki koi khabar nahi, skip")
        return
    mp_keys = ['madhya pradesh', 'madhya+pradesh', 'mohan yadav', 'bhopal',
               'indore', 'gwalior', 'jabalpur', 'ujjain', 'ratlam', 'rewa',
               'sagar', 'satna', 'मध्य प्रदेश', 'मध्यप्रदेश', 'मोहन यादव',
               'भोपाल', 'इंदौर', 'ग्वालियर', 'जबलपुर', 'उज्जैन', 'रतलाम',
               'रीवा', 'सागर', 'सतना', 'एमपी']
    mp_html = "<h2 id=\"mp-special\">🏛️ MP Special</h2>"
    nat_html = "<h2 id=\"national\">🇮🇳 National</h2>"
    intl_html = "<h2 id=\"international\">🌍 International</h2>"
    for n in items:
        text = (n['title'] + ' ' + n.get('desc', '')).lower()
        is_mp = n.get('source') == 'MP News' or any(k in text for k in mp_keys)
        is_intl = any(k in text for k in ['america', 'trump', 'china', 'japan',
                                          'israel', 'pakistan', 'sri lanka', 'un '])
        img2 = (f"<br><img src='{n.get('image', '')}' "
                f"style='width:100%;border-radius:12px;margin:12px 0' loading='lazy'>"
                if n.get('image') else "")
        h = (f"<h3>{n['title']}</h3>{img2}<p><strong>Date:</strong> {n['date']} "
             f"| 📰 {n['source']}</p><p>{n.get('desc', '')}</p>"
             f"<p><strong>📝 परीक्षा टिप:</strong> तथ्य नोट करें!</p><hr>")
        if is_mp:
            mp_html += h
        elif is_intl:
            intl_html += h
        else:
            nat_html += h
    date_hdr = (f"<div style='background:#1a73e8;color:#fff;padding:12px;"
                f"border-radius:12px;text-align:center;font-weight:700;"
                f"margin-bottom:16px'>{today_ca}</div>")
    full = date_hdr + mp_html + "<hr>" + nat_html + "<hr>" + intl_html
    pd = json.load(open("data/posts.json", encoding="utf-8"))
    pd["posts"] = [p for p in pd["posts"]
                   if p.get("slug") != f"current-affairs-{today_slug}"]
    post = {"title": f"Current Affairs: {today_ca} — परीक्षा के लिए महत्वपूर्ण",
            "slug": f"current-affairs-{today_slug}",
            "category": "current-affairs", "date": today_slug,
            "excerpt": f"{today_ca} की {len(items)} महत्वपूर्ण खबरें",
            "content": full, "image": ""}
    pd["posts"].insert(0, post)
    json.dump(pd, open("data/posts.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"Current Affairs post: {today_ca} ({len(items)} items)")


def main():
    # 1. Fresh MP news (direct feeds) + enrich (body + photo)
    fresh_mp = []
    for name, url, limit in MP_FEEDS:
        fresh_mp.extend(fetch_feed_items(name, url, limit))
    enrich_mp(fresh_mp)

    # 2. Fresh general items — SIRF CA post ke liye (news me save nahi)
    fresh_ca = []
    for name, url, limit in CA_FEEDS:
        fresh_ca.extend(fetch_feed_items(name, url, limit))
    for n in fresh_ca:
        if "google.com" not in n["link"]:
            body, img = al.fetch_article(n["link"])
            if body:
                n["body"] = body
                n["desc"] = body_excerpt(body)
            if img:
                n["image"] = img

    # 3. news.json: sirf MP items (purani general news HATAO) + fresh MP
    # Fresh me se sirf MP se judi khabrein (national/CG feed items nahi)
    fresh_mp_news = [n for n in fresh_mp if mp_relevant(n)]
    print(f"MP Special filter: {len(fresh_mp)} fresh -> "
          f"{len(fresh_mp_news)} MP-relevant")
    old = []
    if os.path.exists("data/news.json"):
        try:
            old = json.load(open("data/news.json", encoding="utf-8"))
        except Exception:
            old = []
    old_mp = [n for n in old if keep_mp(n) and is_hindi(n.get("title", ""))]
    # Title-match upgrade: purani Google-link MP khabar direct feed se mili to
    # uska link/body/photo upgrade karo
    direct_by_title = {norm_title(n["title"]): n for n in fresh_mp}
    for n in old_mp:
        if (not n.get("body") or not n.get("image")) \
                and "google.com" in n.get("link", ""):
            d = direct_by_title.get(norm_title(n["title"]))
            if d:
                n["link"] = d["link"]
                if d.get("body"):
                    n["body"] = d["body"]
                    n["desc"] = d["desc"]
                if d.get("image"):
                    n["image"] = d["image"]
                print(f"  upgraded old MP item: {n['title'][:45]}")
    seen_links = set(n.get("link", "") for n in fresh_mp_news)
    seen_titles = set(norm_title(n.get("title", "")) for n in fresh_mp_news)
    all_news = list(fresh_mp_news)
    for n in old_mp:
        if n.get("link", "") not in seen_links \
                and norm_title(n.get("title", "")) not in seen_titles:
            all_news.append(n)
            seen_links.add(n.get("link", ""))
            seen_titles.add(norm_title(n.get("title", "")))
    all_news.sort(key=dkey, reverse=True)
    all_news = all_news[:100]

    # 4. Article pages rebuild (body/photo upgrade dikhe)
    for n in all_news:
        n["article"] = al.article_filename(n)
    for n in all_news:
        open(n["article"], "w").write(al.build_article_html(n, all_news))
    missing = [n["title"][:40] for n in all_news
               if n.get("article") and not os.path.exists(n["article"])]
    if missing:
        raise SystemExit(f"Article generation failed: {missing}")
    print(f"Articles ready: all {len(all_news)} verified")
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, ensure_ascii=False, indent=1)

    # 5. Archive: sirf MP items, hamesha (lightweight, body ke bina)
    arch = []
    if os.path.exists("data/news-archive.json"):
        try:
            arch = json.load(open("data/news-archive.json", encoding="utf-8"))
        except Exception:
            arch = []
    arch = [a for a in arch if keep_mp(a)]
    seen_a = set(a.get("link", "") for a in arch)
    seen_at = set(norm_title(a.get("title", "")) for a in arch)
    for n in all_news:
        if n.get("link", "") not in seen_a \
                and norm_title(n.get("title", "")) not in seen_at:
            arch.append({k: n.get(k, "") for k in
                         ("source", "title", "link", "date", "desc", "image", "article")})
            seen_a.add(n.get("link", ""))
            seen_at.add(norm_title(n.get("title", "")))
    arch.sort(key=dkey, reverse=True)
    with open("data/news-archive.json", "w", encoding="utf-8") as f:
        json.dump(arch, f, ensure_ascii=False, indent=1)
    print(f"Archive total (MP only): {len(arch)} items")

    # 6. Daily Current Affairs post (general + MP, aaj ki khabrein)
    build_ca_post(fresh_ca + fresh_mp)

    n_body = sum(1 for n in all_news if n.get("body"))
    n_img = sum(1 for n in all_news if n.get("image"))
    print(f"news.json: {len(all_news)} MP items, body={n_body}, image={n_img}")


if __name__ == "__main__":
    main()
