"""Shared article helpers for the Algorithmic Gyan website.

Used by BOTH:
  - .github/workflows/update-news.yml (3-hourly auto news)
  - scripts/backfill-articles.py (one-time / manual rebuild)

Single source of truth so the workflow and manual rebuilds produce
byte-identical article HTML. Do NOT duplicate this template elsewhere.
"""
import html
import os
import re
from urllib.parse import quote as _quote

SITE = "https://algorithmicgyan-source.github.io/algorithmicgyan-website/"


DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
MOBILE_UA = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/126.0 Mobile Safari/537.36"

# Body cap — LONG description (user: "lambi jaankari honi chahiye").
# Pehle 4000 chars / 8 paras tha, isliye khabar aadhi dikhti thi.
BODY_MAX_CHARS = 12000
BODY_MAX_PARAS = 25


def fetch_html(url):
    """Article HTML lao: desktop UA, 403 mile to mobile UA se retry.

    Kuch publishers (NDTV) desktop UA ko 403 dete hain, mobile UA se khul jaate hain.
    Returns "" on any failure.
    """
    import urllib.request as _ur
    import urllib.error as _ue
    for _ua in (DESKTOP_UA, MOBILE_UA):
        try:
            _req = _ur.Request(url, headers={
                "User-Agent": _ua, "Accept-Language": "hi-IN,hi;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml"})
            with _ur.urlopen(_req, timeout=25) as _r:
                return _r.read().decode("utf-8", "ignore")
        except _ue.HTTPError as _e:
            if _e.code != 403:
                return ""
            continue
        except Exception:
            return ""
    return ""


def extract_image(page_html):
    """Article page se photo: og:image -> twitter:image. Google ki generic image kabhi nahi."""
    if not page_html:
        return ""
    _m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', page_html)
    if not _m:
        _m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', page_html)
    if not _m:
        _m = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)', page_html)
    _u = _m.group(1).strip() if _m else ""
    if not _u or "googleusercontent" in _u or "gstatic" in _u:
        return ""
    return html.unescape(_u)


def fetch_article(url):
    """Ek article page se (full body, photo) — ek hi fetch me dono.

    Google News redirect links (news.google.com) server-side nahi khulte
    (sirf JS shell milta hai, na body na asli photo), isliye caller unhe
    skip kare aur direct source feed ke link hi bhej.
    Returns (body, image); dono "" ho sakte hain on failure.
    """
    _html = fetch_html(url)
    if not _html:
        return "", ""
    _img = extract_image(_html)
    try:
        from trafilatura import extract as _extract
        _txt = _extract(_html, include_comments=False, include_tables=False, no_fallback=False)
    except Exception:
        _txt = ""
    if not _txt:
        return "", _img
    _paras = [p.strip() for p in _txt.split("\n") if len(p.strip()) > 60]
    _bad = ("subscribe", "advertisement", "also read", "read also", "follow us",
            "download", "copyright", "all rights reserved", "sign up",
            "newsletter", "click here")
    _paras = [p for p in _paras if not any(b in p.lower() for b in _bad)]
    _out, _total = [], 0
    for p in _paras:
        if _total + len(p) > BODY_MAX_CHARS:
            break
        _out.append(p)
        _total += len(p)
        if len(_out) >= BODY_MAX_PARAS:
            break
    return "\n\n".join(_out), _img


def fetch_body(url):
    """Back-compat wrapper: sirf body (photo nahi). Naya code fetch_article use kare."""
    _body, _img = fetch_article(url)
    return _body


def share_bar(title, url):
    """Share bar HTML (WhatsApp / Facebook / X / Telegram / Copy link).

    Fully inline — no external JS/CSS dependency, works on standalone
    article pages. `url` must be the full canonical page URL.
    """
    _t = _quote(title + "\n\n👉 पूरी खबर पढ़ें: " + url)
    _u = _quote(url)
    _tt = _quote(title)
    return (
        '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:20px;padding-top:16px;border-top:1px solid #eee">'
        '<span style="font-weight:700;padding:8px 0">📤 शेयर करें:</span>'
        f'<a href="https://wa.me/?text={_t}" target="_blank" rel="noopener" style="background:#25D366;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-weight:700;font-size:.85rem">📲 WhatsApp</a>'
        f'<a href="https://www.facebook.com/sharer/sharer.php?u={_u}" target="_blank" rel="noopener" style="background:#1877F2;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-weight:700;font-size:.85rem">👍 Facebook</a>'
        f'<a href="https://twitter.com/intent/tweet?text={_tt}&url={_u}" target="_blank" rel="noopener" style="background:#000;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-weight:700;font-size:.85rem">𝕏 X</a>'
        f'<a href="https://t.me/share/url?url={_u}&text={_tt}" target="_blank" rel="noopener" style="background:#229ED9;color:#fff;padding:8px 14px;border-radius:8px;text-decoration:none;font-weight:700;font-size:.85rem">✈️ Telegram</a>'
        f'<button onclick="agCopy(\'{url}\',this)" style="background:#555;color:#fff;padding:8px 14px;border-radius:8px;border:none;cursor:pointer;font-weight:700;font-size:.85rem">🔗 Copy Link</button></div>'
        '<script>function agCopy(u,b){navigator.clipboard.writeText(u).then(function(){b.textContent="✅ Copied!";setTimeout(function(){b.textContent="🔗 Copy Link";},2000);});}</script>'
    )


def article_filename(n):
    """Deterministic article path from title + date (same as before)."""
    _words = re.findall(r'[a-z0-9]+', n["title"].lower())
    _slug = '-'.join(_words[:8])[:60].strip('-')
    if not _slug or len(_slug) < 5:
        import hashlib as _hl
        _slug = "news-" + _hl.md5(n["title"].encode()).hexdigest()[:8]
    _dp = n["date"][:11].replace(" ", "-")
    return f"news/article/{_dp}-{_slug}.html"


def build_article_html(n, all_news):
    """Full article page: image + full body (or RSS desc) + share + related links."""
    _fn = n["article"]
    _body = n.get("body") or n.get("desc", "")
    _paras = "".join(
        f"<p style='line-height:1.8;color:#333'>{html.escape(p)}</p>"
        for p in _body.split("\n\n") if p.strip())
    _img = ""
    if n.get("image"):
        _img = (f"<img src='{html.escape(n['image'], quote=True)}' "
                f"style='width:100%;border-radius:12px;margin:12px 0' loading='lazy'>")
    _rel = [m for m in all_news
            if m.get("source") == n.get("source") and m.get("link") != n.get("link")][:4]
    _rel_html = ""
    if _rel:
        _rel_html = ("<h3>📰 इसी तरह की और खबरें</h3><ul>" + "".join(
            f"<li><a href='{m['article'].split('/')[-1]}'>{html.escape(m['title'])}</a></li>"
            for m in _rel if m.get("article")) + "</ul>")
    _url = SITE + _fn
    _meta = html.escape((n.get("desc") or n["title"])[:160], quote=True)
    _title = html.escape(n["title"])
    _src = html.escape(n["source"])
    _date = html.escape(n["date"])
    return (
        f"<!DOCTYPE html><html lang=\"hi\"><head><meta charset=\"UTF-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1.0\">"
        f"<title>{_title} | Algorithmic Gyan</title>"
        f"<meta name=\"description\" content=\"{_meta}\"></head>"
        f"<body style=\"font-family:system-ui;max-width:700px;margin:0 auto;padding:20px;background:#f5f5f5\">"
        f"<a href=\"../../news.html\" style=\"color:#0066cc;text-decoration:none\">← सभी खबरें</a>"
        f"<article style=\"background:#fff;padding:24px;border-radius:12px;margin-top:12px\">"
        f"<div style=\"margin-bottom:12px\"><span style=\"background:#e3f2fd;color:#1565c0;padding:4px 12px;border-radius:20px;font-size:.85rem\">{_src}</span> "
        f"<span style=\"color:#888;font-size:.85rem\">{_date}</span></div>"
        f"<h1 style=\"font-size:1.4rem;margin:12px 0\">{_title}</h1>"
        f"{_img}{_paras}"
        f"<p style=\"color:#888;font-size:.85rem;margin-top:16px\">स्रोत: {_src}</p>"
        f"{share_bar(n['title'], _url)}{_rel_html}"
        f"</article>"
        f"<div style=\"text-align:center;margin-top:20px;color:#888;font-size:.85rem\">© 2026 Algorithmic Gyan</div>"
        f"</body></html>"
    )


def inject_share_into_file(path):
    """One-time upgrade for OLD article files not in news.json anymore:
    insert the share bar (no body fetch — title taken from <title>).
    Returns True if the file was changed."""
    try:
        content = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return False
    if "agCopy" in content or "wa.me/?text=" in content:
        return False  # already has share
    m = re.search(r"<title>(.*?)</title>", content, re.S)
    title = (m.group(1).rsplit(" | Algorithmic Gyan", 1)[0].strip()
             if m else "Algorithmic Gyan")
    title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip() or "Algorithmic Gyan"
    url = SITE + "news/article/" + os.path.basename(path)
    bar = share_bar(title, url)
    if "</article>" in content:
        content = content.replace("</article>", bar + "</article>", 1)
    elif "</body>" in content:
        content = content.replace("</body>", bar + "</body>", 1)
    else:
        return False
    open(path, "w", encoding="utf-8").write(content)
    return True
