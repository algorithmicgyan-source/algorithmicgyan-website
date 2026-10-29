#!/usr/bin/env python3
"""Generate assets/chatbot-kb.js from real site content.

Reads data/posts.json (facts, motivational stories, current affairs)
and data/news.json (MP news headlines) and writes a compact keyword ->
answer knowledge base for the FAQ chatbot widget. Re-run whenever the
site content changes a lot; the widget itself also refreshes its
"latest" entries live from data/*.json at page load.
"""
import json
import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://algorithmicgyan-source.github.io/algorithmicgyan-website/"
BLOG = "https://algorithmicgyanyoutube.blogspot.com"
YT = "https://www.youtube.com/@algorithmicgyan"

STOP = set("""और है हैं का की के से में ने को पर एक भी तो ही यह वह जो कि था थी थे होगा
होता होते अपनी अपने इस उस तक लिए बाद पहले जब तब अगर या सभी कुछ क्या कैसे कहाँ कब क्यों कौन
हुआ हुई हुए गया गई गए कर करता करती करते रहा रही रहे वाला वाली वाले""".split())

DEV_RE = re.compile(r"[\u0900-\u097F]+")


def keywords(title, extra=()):
    out = []
    for tok in DEV_RE.findall(title or ""):
        tok = tok.strip("।,;:!?\"'()[]{}")
        if len(tok) >= 2 and tok not in STOP and tok not in out:
            out.append(tok)
    for e in extra:
        if e not in out:
            out.append(e)
    return out


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def main():
    posts = json.load(open(os.path.join(ROOT, "data", "posts.json")))["posts"]
    news = json.load(open(os.path.join(ROOT, "data", "news.json")))
    posts_sorted = sorted(posts, key=lambda p: p.get("date", ""), reverse=True)
    facts = [p for p in posts_sorted if p["category"] == "facts"]
    mots = [p for p in posts_sorted if p["category"] == "motivational"]
    cas = [p for p in posts_sorted if p["category"] == "current-affairs"]

    def post_link(p):
        return "post.html?slug=" + p["slug"]

    def short(text, n=220):
        text = re.sub(r"<[^>]+>", " ", text or "")
        text = re.sub(r"\s+", " ", text).strip()
        return text[:n] + ("…" if len(text) > n else "")

    entries = []

    def add(eid, kws, ans):
        entries.append({"id": eid, "k": kws, "a": ans})

    # --- greeting ---
    add("greeting", ["नमस्ते", "हाय", "हैलो", "सत", "श्री"],
        "नमस्ते! 🙏 मैं Algorithmic Gyan का सहायक हूँ। आप मुझसे फैक्ट, "
        "मोटिवेशनल स्टोरी, करंट अफेयर्स या MP न्यूज़ के बारे में पूछ सकते हैं।")

    # --- latest entries (refreshed live by the widget from data/*.json) ---
    if facts:
        p = facts[0]
        add("latest-fact",
            keywords(p["title"], ["आज", "ताज़ा", "नया", "फैक्ट", "तथ्य", "रोचक"]),
            "🧠 आज का फैक्ट: " + p["title"] + " — " + short(p.get("excerpt") or p.get("content")) +
            ' <a href="' + post_link(p) + '">👉 पढ़ें</a>')
    if mots:
        p = mots[0]
        add("latest-motivation",
            keywords(p["title"], ["आज", "ताज़ा", "नया", "मोटिवेशनल", "कहानी", "स्टोरी", "प्रेरणा"]),
            "🔥 मोटिवेशनल स्टोरी: " + p["title"] + " — " + short(p.get("excerpt") or p.get("content")) +
            ' <a href="' + post_link(p) + '">👉 पढ़ें</a>')
    if cas:
        p = cas[0]
        add("latest-ca",
            keywords(p["title"], ["आज", "ताज़ा", "नया", "करंट", "अफेयर्स", "परीक्षा", "एग्जाम"]),
            "📰 " + p["title"] + " — " + short(p.get("excerpt") or "") +
            ' <a href="' + post_link(p) + '">👉 पढ़ें</a>')
    if news:
        top = news[:3]
        lines = "🏛️ ताज़ा MP न्यूज़:<br>" + "<br>".join(
            "• " + n["title"] + ' <a href="' + (n.get("article") or "news.html") + '">👉 पढ़ें</a>'
            for n in top)
        add("latest-news",
            ["एमपी", "मध्य", "प्रदेश", "न्यूज़", "खबर", "ताज़ा", "आज", "नया"],
            lines + '<br><a href="news.html">📰 सभी MP न्यूज़ देखें</a>')

    # --- site / navigation entries ---
    add("site",
        ["साइट", "वेबसाइट", "चैनल", "ग्यान", "बारे", "किस"],
        "Algorithmic Gyan एक Hindi education वेबसाइट और YouTube चैनल है — यहाँ "
        "science, history और education के रोचक फैक्ट, मोटिवेशनल स्टोरी और करंट "
        "अफेयर्स मिलते हैं। <a href=\"about.html\">About पेज</a> • "
        "<a href=\"" + YT + "\" target=\"_blank\" rel=\"noopener\">▶️ YouTube चैनल</a> • "
        "<a href=\"" + BLOG + "\" target=\"_blank\" rel=\"noopener\">📝 Blogger ब्लॉग</a>")
    add("nav-facts",
        ["फैक्ट", "तथ्य", "रोचक", "अजब", "गजब"],
        "रोज़ एक नया रोचक फैक्ट <a href=\"posts.html\">सभी पोस्ट</a> पर मिलता है। "
        "पुराने फैक्ट खोजने के लिए <a href=\"search.html\">Search पेज</a> इस्तेमाल करें।")
    add("nav-motivation",
        ["मोटिवेशनल", "कहानी", "स्टोरी", "प्रेरणा", "प्रेरणादायक"],
        "सच्ची मोटिवेशनल स्टोरी <a href=\"posts.html\">सभी पोस्ट</a> पर मिलती हैं। "
        "कोई खास स्टोरी खोजनी हो तो <a href=\"search.html\">Search पेज</a> पर नाम लिखें।")
    add("nav-ca",
        ["करंट", "अफेयर्स", "परीक्षा", "एग्जाम", "जीके"],
        "रोज़ का करंट अफेयर्स (MP Special + National + International + exam tip) "
        "<a href=\"current-affairs.html\">Current Affairs पेज</a> पर मिलता है।")
    add("nav-news",
        ["न्यूज़", "खबर", "समाचार"],
        "MP Special न्यूज़ <a href=\"news.html\">News पेज</a> पर मिलती है — किसी तारीख़ "
        "की न्यूज़ देखने के लिए उसी पेज पर कैलेंडर से तारीख़ चुनें।")
    add("nav-videos",
        ["वीडियो", "यूट्यूब", "चैनल", "वाच", "देख"],
        "चैनल के वीडियो <a href=\"videos.html\">Videos पेज</a> पर हैं, और सीधे "
        "<a href=\"" + YT + "\" target=\"_blank\" rel=\"noopener\">YouTube चैनल @algorithmicgyan</a> पर भी देख सकते हैं।")
    add("nav-search",
        ["खोज", "खोजें", "सर्च", "ढूंढ", "पुराना", "पुरानी", "तारीख़", "कैलेंडर", "आर्काइव"],
        "पुरानी न्यूज़ या पोस्ट खोजने के लिए <a href=\"search.html\">Search पेज</a> "
        "इस्तेमाल करें — वह पूरा आर्काइव खोजता है। News पेज पर कैलेंडर से किसी भी "
        "तारीख़ की न्यूज़ खोल सकते हैं।")
    add("nav-blog",
        ["ब्लॉग", "blogger"],
        "हमारा Blogger ब्लॉग यहाँ है: <a href=\"" + BLOG + "\" target=\"_blank\" "
        "rel=\"noopener\">algorithmicgyanyoutube.blogspot.com</a> — वहाँ फैक्ट, "
        "मोटिवेशनल स्टोरी और करंट अफेयर्स भी मिलते हैं।")
    add("nav-about",
        ["कौन", "मालिक", "गौरव", "अबाउट", "संपर्क", "बनाया"],
        "Algorithmic Gyan चैनल Gaurav Bavnkar चलाते हैं। ज़्यादा जानकारी "
        "<a href=\"about.html\">About पेज</a> पर है।")
    add("nav-daily",
        ["रोज़", "डेली", "नया", "अपडेट", "कब"],
        "साइट पर रोज़ नया कंटेंट आता है — रोज़ एक फैक्ट, एक मोटिवेशनल स्टोरी और "
        "करंट अफेयर्स। <a href=\"posts.html\">आज की पोस्ट देखें</a>।")
    add("nav-subscribe",
        ["सब्सक्राइब", "जुड़", "फॉलो", "सदस्य"],
        "चैनल से जुड़े रहने के लिए <a href=\"" + YT + "\" target=\"_blank\" "
        "rel=\"noopener\">YouTube पर @algorithmicgyan को सब्सक्राइब</a> करें।")

    # --- specific posts (latest 6 facts + 6 motivational + 2 CA) ---
    for p in facts[:6]:
        add("post-" + p["slug"],
            keywords(p["title"], ["फैक्ट", "तथ्य"]),
            "🧠 " + p["title"] + " — " + short(p.get("excerpt") or p.get("content")) +
            ' <a href="' + post_link(p) + '">👉 पूरी पोस्ट पढ़ें</a>')
    for p in mots[:6]:
        add("post-" + p["slug"],
            keywords(p["title"], ["मोटिवेशनल", "कहानी", "स्टोरी"]),
            "🔥 " + p["title"] + " — " + short(p.get("excerpt") or p.get("content")) +
            ' <a href="' + post_link(p) + '">👉 पूरी पोस्ट पढ़ें</a>')
    for p in cas[:2]:
        add("post-" + p["slug"],
            keywords(p["title"], ["करंट", "अफेयर्स"]),
            "📰 " + p["title"] + " — " + short(p.get("excerpt") or "") +
            ' <a href="' + post_link(p) + '">👉 पूरी पोस्ट पढ़ें</a>')

    # --- specific MP news (latest 12) ---
    for i, n in enumerate(news[:12]):
        link = n.get("article") or "news.html"
        add("news-" + str(i),
            keywords(n["title"], ["न्यूज़", "खबर", "एमपी"]),
            "🏛️ " + n["title"] + " (" + n.get("date", "") + ")" +
            ' <a href="' + link + '">👉 पढ़ें</a>')

    out = ("/* Generated by scripts/gen-chatbot-kb.py from data/posts.json + "
           "data/news.json — do not edit by hand. */\n"
           "var AG_CHAT_KB = " + json.dumps(entries, ensure_ascii=False, indent=1) + ";\n"
           "if (typeof module !== 'undefined' && module.exports) { module.exports = AG_CHAT_KB; }\n")
    dest = os.path.join(ROOT, "assets", "chatbot-kb.js")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(out)
    print("wrote", dest, "entries:", len(entries))


if __name__ == "__main__":
    main()
