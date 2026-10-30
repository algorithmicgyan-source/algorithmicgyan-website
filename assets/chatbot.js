/* Algorithmic Gyan FAQ chatbot — pure HTML/CSS/JS, no backend, no API key.
   Needs assets/chatbot-kb.js loaded before it (var AG_CHAT_KB).
   Works on every root-level page; all markup uses #ag-chat-* ids so it
   cannot clash with page styles, and everything is position:fixed so it
   never changes page layout. */
(function () {
  "use strict";

  /* Roman Hindi / English words -> Devanagari keywords, so users can type
     in Roman Hindi (phone-first users) and still match the Hindi KB. */
  var ROMAN_MAP = {
    chand: "चाँद", moon: "चाँद", suraj: "सूरज", sun: "सूरज",
    prithvi: "पृथ्वी", earth: "पृथ्वी", dharti: "पृथ्वी",
    shahad: "शहद", honey: "शहद", pahad: "पहाड़", mountain: "पहाड़",
    manjhi: "मांझी", arunima: "अरुणिमा", everest: "एवरेस्ट",
    motivational: "मोटिवेशनल", story: "कहानी", kahani: "कहानी",
    prerana: "प्रेरणा", fact: "फैक्ट", facts: "फैक्ट", tathya: "तथ्य",
    rochak: "रोचक", current: "करंट", affairs: "अफेयर्स",
    pariksha: "परीक्षा", exam: "परीक्षा", news: "न्यूज़", khabar: "खबर",
    samachar: "समाचार", mp: "एमपी", madhya: "मध्य", pradesh: "प्रदेश",
    bhopal: "भोपाल", indore: "इंदौर", video: "वीडियो", youtube: "यूट्यूब",
    channel: "चैनल", search: "खोज", khoj: "खोज", dhoondh: "ढूंढ",
    blog: "ब्लॉग", blogger: "ब्लॉग", website: "वेबसाइट", site: "साइट",
    aaj: "आज", latest: "ताज़ा", taaza: "ताज़ा", naya: "नया",
    kya: "क्या", kaun: "कौन", kahan: "कहाँ", kaise: "कैसे",
    kab: "कब", kyon: "क्यों", namaste: "नमस्ते", hello: "हैलो",
    hi: "हाय", subscribe: "सब्सक्राइब", jud: "जुड़", roj: "रोज़",
    daily: "रोज़", purana: "पुराना", tarikh: "तारीख़", calendar: "कैलेंडर",
    gaurav: "गौरव", malik: "मालिक", about: "अबाउट", sampark: "संपर्क"
  };

  function normalize(s) {
    return String(s == null ? "" : s).toLowerCase()
      .replace(/ँ/g, "ं")            /* चाँद / चांद एक ही */
      .replace(/़/g, "")             /* nukta hatayein: ज़ -> ज */
      .replace(/[^a-z\u0900-\u097f0-9 ]/g, " ")
      .replace(/\s+/g, " ").trim();
  }

  /* Roman tokens ko Devanagari me badal kar query ko ameer banayein. */
  function expandRoman(normQuery) {
    var out = normQuery;
    normQuery.split(" ").forEach(function (tok) {
      if (ROMAN_MAP[tok]) out += " " + ROMAN_MAP[tok];
    });
    return out;
  }

  function tokenizeDev(text) {
    var m = String(text || "").match(/[\u0900-\u097F]+/g);
    return m || [];
  }

  var STOP = { "और": 1, "है": 1, "हैं": 1, "का": 1, "की": 1, "के": 1,
    "से": 1, "में": 1, "ने": 1, "को": 1, "पर": 1, "एक": 1, "भी": 1,
    "तो": 1, "ही": 1, "यह": 1, "वह": 1, "जो": 1, "कि": 1, "था": 1,
    "थी": 1, "थे": 1, "क्या": 1, "कैसे": 1, "कहाँ": 1, "कब": 1,
    "क्यों": 1, "कौन": 1, "हुआ": 1, "हुई": 1, "हुए": 1, "गया": 1,
    "गई": 1, "गए": 1, "कर": 1, "रहा": 1, "रही": 1, "रहे": 1 };

  function titleKeywords(title, extra) {
    var out = [];
    tokenizeDev(title).forEach(function (tok) {
      if (tok.length >= 2 && !STOP[tok] && out.indexOf(tok) === -1) out.push(tok);
    });
    (extra || []).forEach(function (e) { if (out.indexOf(e) === -1) out.push(e); });
    return out;
  }

  function stripHtml(html) {
    return String(html || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
  }

  function short(text, n) {
    text = stripHtml(text);
    return text.length > n ? text.slice(0, n) + "…" : text;
  }

  /* Keyword scoring: poora keyword mile to +2, hissa mile to +1. */
  function findAnswer(query, kb) {
    var q = normalize(expandRoman(normalize(query)));
    if (!q) return null;
    var best = null, bestScore = 0;
    (kb || []).forEach(function (entry) {
      var score = 0;
      (entry.k || []).forEach(function (kw) {
        var nk = normalize(kw);
        if (!nk) return;
        if (q.indexOf(nk) !== -1) score += 2;
        else if (nk.length >= 3) {
          var hit = q.split(" ").some(function (t) {
            return t.length >= 3 && (t.indexOf(nk) !== -1 || nk.indexOf(t) !== -1);
          });
          if (hit) score += 1;
        }
      });
      if (score > bestScore) { bestScore = score; best = entry; }
    });
    return bestScore >= 2 ? best : null;
  }

  var FALLBACK = "माफ़ कीजिए, इसका जवाब मेरे पास अभी नहीं है। 🙏 आप "
    + '<a href="search.html">Search पेज</a> पर खोज सकते हैं, या '
    + '<a href="posts.html">सभी पोस्ट</a> और <a href="news.html">MP न्यूज़</a> देख सकते हैं।';

  /* Live refresh: data/*.json se "latest" entries taaza karein, taaki KB
     roz ke naye fact/story/CA/news se kabhi purana na pade. Fail ho to
     snapshot KB hi kaam karta rahega. */
  function refreshFromData(posts, news, kb) {
    function byId(id) { for (var i = 0; i < kb.length; i++) if (kb[i].id === id) return kb[i]; return null; }
    function postLink(p) { return "post.html?slug=" + p.slug; }
    var sorted = (posts || []).slice().sort(function (a, b) {
      return String(b.date || "") < String(a.date || "") ? -1 : 1;
    });
    function first(cat) { for (var i = 0; i < sorted.length; i++) if (sorted[i].category === cat) return sorted[i]; return null; }
    var f = first("facts"), m = first("motivational"), c = first("current-affairs");
    var e;
    if (f && (e = byId("latest-fact"))) {
      e.k = titleKeywords(f.title, ["आज", "ताज़ा", "नया", "फैक्ट", "तथ्य", "रोचक"]);
      e.a = "🧠 आज का फैक्ट: " + f.title + " — " + short(f.excerpt || f.content, 220)
        + ' <a href="' + postLink(f) + '">👉 पढ़ें</a>';
    }
    if (m && (e = byId("latest-motivation"))) {
      e.k = titleKeywords(m.title, ["आज", "ताज़ा", "नया", "मोटिवेशनल", "कहानी", "स्टोरी", "प्रेरणा"]);
      e.a = "🔥 मोटिवेशनल स्टोरी: " + m.title + " — " + short(m.excerpt || m.content, 220)
        + ' <a href="' + postLink(m) + '">👉 पढ़ें</a>';
    }
    if (c && (e = byId("latest-ca"))) {
      e.k = titleKeywords(c.title, ["आज", "ताज़ा", "नया", "करंट", "अफेयर्स", "परीक्षा", "एग्जाम"]);
      e.a = "📰 " + c.title + " — " + short(c.excerpt || "", 220)
        + ' <a href="' + postLink(c) + '">👉 पढ़ें</a>';
    }
    if (news && news.length && (e = byId("latest-news"))) {
      var lines = news.slice(0, 3).map(function (n) {
        return "• " + n.title + ' <a href="' + (n.article || "news.html") + '">👉 पढ़ें</a>';
      }).join("<br>");
      e.a = "🏛️ ताज़ा MP न्यूज़:<br>" + lines + '<br><a href="news.html">📰 सभी MP न्यूज़ देखें</a>';
    }
  }

  function loadLiveData(kb) {
    if (typeof fetch === "undefined") return;
    var postsP = fetch("data/posts.json").then(function (r) { return r.json(); })
      .then(function (d) { return d.posts || d; }).catch(function () { return null; });
    var newsP = fetch("data/news.json").then(function (r) { return r.json(); })
      .then(function (d) { return d.items || d.news || d; }).catch(function () { return null; });
    Promise.all([postsP, newsP]).then(function (res) {
      if (res[0] || res[1]) refreshFromData(res[0] || [], res[1] || [], kb);
    });
  }

  /* ---------- widget (browser only) ---------- */
  function escapeHTML(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function initWidget() {
    if (typeof document === "undefined" || !document.body) return;
    if (document.getElementById("ag-chat-btn")) return; /* dobara na lage */
    var kb = (typeof AG_CHAT_KB !== "undefined") ? AG_CHAT_KB : [];
    loadLiveData(kb);

    var css = "#ag-chat-btn{position:fixed;right:16px;bottom:16px;z-index:9999;width:auto;height:56px;padding:0 18px;border-radius:999px;border:2px solid #00d4ff;background:linear-gradient(135deg,#0a0a2e,#16213e);color:#fff;font-size:24px;font-weight:700;cursor:pointer;box-shadow:0 6px 24px rgba(0,212,255,.35);display:flex;align-items:center;gap:6px;line-height:1}"
      + "#ag-chat-panel{display:none;position:fixed;right:12px;bottom:84px;z-index:9999;width:min(360px,calc(100vw - 24px));height:min(520px,calc(100vh - 110px));background:#070B14;border:1px solid rgba(0,212,255,.4);border-radius:16px;overflow:hidden;flex-direction:column;box-shadow:0 12px 40px rgba(0,0,0,.6);font-family:system-ui,'Hind',sans-serif}"
      + "#ag-chat-panel.ag-open{display:flex}"
      + "#ag-chat-head{background:linear-gradient(90deg,#0a0a2e,#16213e);color:#fff;padding:12px 14px;font-weight:700;display:flex;justify-content:space-between;align-items:center}"
      + "#ag-chat-head small{display:block;font-weight:400;color:#9AA7BD;font-size:.75rem}"
      + "#ag-chat-close{background:none;border:none;color:#fff;font-size:20px;cursor:pointer;padding:0 2px}"
      + "#ag-chat-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:10px}"
      + "#ag-chat-msgs .ag-msg{max-width:88%;padding:10px 12px;border-radius:12px;font-size:.92rem;line-height:1.6;color:#fff}"
      + "#ag-chat-msgs .ag-bot{background:#16213e;align-self:flex-start;border-bottom-left-radius:4px}"
      + "#ag-chat-msgs .ag-user{background:#0a4a5e;align-self:flex-end;border-bottom-right-radius:4px}"
      + "#ag-chat-msgs .ag-msg a{color:#00d4ff;font-weight:600}"
      + "#ag-chat-chips{display:flex;flex-wrap:wrap;gap:6px;padding:0 12px 10px}"
      + "#ag-chat-chips button{background:#16213e;color:#fff;border:1px solid rgba(0,212,255,.4);border-radius:999px;padding:6px 12px;font-size:.82rem;cursor:pointer}"
      + "#ag-chat-form{display:flex;gap:8px;padding:10px;border-top:1px solid rgba(255,255,255,.1)}"
      + "#ag-chat-input{flex:1;min-width:0;background:#0a0a0a;color:#fff;border:1px solid rgba(255,255,255,.2);border-radius:999px;padding:10px 14px;font-size:.92rem;outline:none}"
      + "#ag-chat-send{background:#00d4ff;color:#04121A;border:none;border-radius:999px;padding:10px 16px;font-weight:700;cursor:pointer}"
      + "@media (max-width:480px){#ag-chat-panel{left:12px;right:12px;width:auto}}";

    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    var BTN_HTML = "🤖<span style=\"font-size:16px;font-weight:800;letter-spacing:.5px\">AI</span>";
    var btn = document.createElement("button");
    btn.id = "ag-chat-btn";
    btn.type = "button";
    btn.setAttribute("aria-label", "AI सहायक चैट खोलें");
    btn.innerHTML = BTN_HTML;
    document.body.appendChild(btn);

    var panel = document.createElement("div");
    panel.id = "ag-chat-panel";
    panel.innerHTML = '<div id="ag-chat-head"><div>💬 Algorithmic Gyan सहायक<small>फैक्ट • स्टोरी • करंट अफेयर्स • MP न्यूज़</small></div>'
      + '<button id="ag-chat-close" type="button" aria-label="बंद करें">✕</button></div>'
      + '<div id="ag-chat-msgs"></div>'
      + '<div id="ag-chat-chips">'
      + '<button type="button">आज का फैक्ट</button><button type="button">मोटिवेशनल स्टोरी</button>'
      + '<button type="button">करंट अफेयर्स</button><button type="button">MP न्यूज़</button></div>'
      + '<form id="ag-chat-form"><input id="ag-chat-input" type="text" placeholder="अपना सवाल लिखें…" autocomplete="off">'
      + '<button id="ag-chat-send" type="submit">भेजें</button></form>';
    document.body.appendChild(panel);

    var msgs = panel.querySelector("#ag-chat-msgs");
    var input = panel.querySelector("#ag-chat-input");
    var greeted = false;

    function addMsg(html, who) {
      var d = document.createElement("div");
      d.className = "ag-msg " + who;
      d.innerHTML = html;
      msgs.appendChild(d);
      msgs.scrollTop = msgs.scrollHeight;
    }

    function answer(q) {
      addMsg(escapeHTML(q), "ag-user");
      var hit = findAnswer(q, kb);
      addMsg(hit ? hit.a : FALLBACK, "ag-bot");
    }

    function open() {
      panel.classList.add("ag-open");
      btn.textContent = "✕";
      if (!greeted) {
        greeted = true;
        addMsg("नमस्ते! 🙏 मैं Algorithmic Gyan का सहायक हूँ। नीचे दिए बटन दबाएँ या अपना सवाल लिखें — फैक्ट, स्टोरी, करंट अफेयर्स या MP न्यूज़ के बारे में पूछ सकते हैं।", "ag-bot");
      }
      setTimeout(function () { input.focus(); }, 50);
    }
    function close() { panel.classList.remove("ag-open"); btn.innerHTML = BTN_HTML; }

    btn.addEventListener("click", function () {
      if (panel.classList.contains("ag-open")) close(); else open();
    });
    panel.querySelector("#ag-chat-close").addEventListener("click", close);
    panel.querySelector("#ag-chat-form").addEventListener("submit", function (ev) {
      ev.preventDefault();
      var q = input.value.trim();
      if (!q) return;
      input.value = "";
      answer(q);
    });
    var chips = panel.querySelectorAll("#ag-chat-chips button");
    chips.forEach(function (c) {
      c.addEventListener("click", function () { answer(c.textContent); });
    });
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initWidget);
    } else {
      initWidget();
    }
  }

  /* Node test harness ke liye. */
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { findAnswer: findAnswer, normalize: normalize,
      expandRoman: expandRoman, refreshFromData: refreshFromData,
      titleKeywords: titleKeywords, FALLBACK: FALLBACK };
  }
})();
