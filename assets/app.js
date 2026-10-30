var CATS = {
  "news":           { label: "News",               icon: "📰", color: "#FF4D5E" },
  "facts":          { label: "Facts",              icon: "🧠", color: "#22D3EE" },
  "current-affairs":{ label: "Current Affairs",    icon: "📰", color: "#FBBF24" },
  "motivational":   { label: "Motivational Story", icon: "🔥", color: "#34D399" }
};

function escapeHTML(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function getVideoId(url) {
  if (!url) return null;
  url = String(url).trim();
  var m = url.match(/[?&]v=([^&#]+)/);
  if (m) return m[1];
  m = url.match(/youtu\.be\/([^?&#/]+)/);
  if (m) return m[1];
  m = url.match(/youtube\.com\/(shorts|embed|live)\/([^?&#/]+)/);
  if (m) return m[2];
  return null;
}

function catMeta(cat) {
  return CATS[cat] || { label: cat, icon: "📌", color: "#9AA7BD" };
}

var SITE_URL = "https://algorithmicgyan-source.github.io/algorithmicgyan-website/";
function agCopy(u, b) {
  navigator.clipboard.writeText(u).then(function () {
    b.textContent = "✅ Copied!"; setTimeout(function () { b.textContent = "🔗 Copy"; }, 2000);
  });
}
function shareRowHTML(title, url, slug) {
  var dl = slug ? '<button class="share-btn dl" onclick="agDownload(\'' + slug + '\',this)">⬇️ Download</button>' : '';
  return '<div class="share-row">'
    + '<a class="share-btn wa" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(title + "\n\n👉 पढ़ें: " + url) + '">📲 WhatsApp</a>'
    + '<a class="share-btn wb" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(title + "\n\n👉 पढ़ें: " + url) + '">💼 WhatsApp Business</a>'
    + '<a class="share-btn fb" target="_blank" rel="noopener" href="https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(url) + '">👍 Facebook</a>'
    + '<a class="share-btn tw" target="_blank" rel="noopener" href="https://twitter.com/intent/tweet?text=' + encodeURIComponent(title) + '&url=' + encodeURIComponent(url) + '">𝕏 X</a>'
    + '<a class="share-btn tg" target="_blank" rel="noopener" href="https://t.me/share/url?url=' + encodeURIComponent(url) + '&text=' + encodeURIComponent(title) + '">✈️ Telegram</a>'
    + '<button class="share-btn cp" onclick="agCopy(\'' + url + '\',this)">🔗 Copy</button>'
    + dl
    + '</div>';
}

function agDownload(slug, btn) {
  fetch("data/posts.json").then(function (r) { return r.json(); }).then(function (d) {
    var p = (d.posts || []).filter(function (x) { return x.slug === slug; })[0];
    if (!p) return;
    var div = document.createElement("div");
    div.innerHTML = p.content || "";
    var body = div.textContent || div.innerText || "";
    var txt = p.title + "\n" + (p.date || "") + " | " + (p.category || "") + "\n\n" + body
      + "\n\n— Algorithmic Gyan\n" + SITE_URL + "post.html?slug=" + encodeURIComponent(slug);
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([txt], { type: "text/plain;charset=utf-8" }));
    a.download = slug + ".txt";
    document.body.appendChild(a); a.click(); a.remove();
    if (btn) { var old = btn.textContent; btn.textContent = "✅ Downloaded!"; setTimeout(function () { btn.textContent = old; }, 2000); }
  }).catch(function () {});
}

function cardHTML(p) {
  var cm = catMeta(p.category);
  var badge = '<span class="badge"><span class="dot" style="background:' + cm.color + '"></span> '
    + escapeHTML(cm.label) + "</span>";
  var date = p.date ? '<span class="date"> ' + escapeHTML(p.date) + "</span>" : "";
  var desc = p.description ? '<p class="desc">' + escapeHTML(p.description) + "</p>" : "";
  var vid = getVideoId(p.youtube_url);

  if (vid) {
    return '<a class="card" href="' + escapeHTML(p.youtube_url) + '" target="_blank" rel="noopener">'
      + '<div class="thumb">' + badge
      + '<img src="https://i.ytimg.com/vi/' + vid + '/hqdefault.jpg" alt="" loading="lazy" onerror="this.style.display=\'none\'">'
      + '<span class="play">▶</span></div>'
      + '<div class="card-body"><h3>' + escapeHTML(p.title) + "</h3>" + desc
      + '<div class="meta">' + date + "</div></div></a>"
      + shareRowHTML(p.title, p.youtube_url);
  }
  var dateBadge = "";
  if (p.date) {
    var dp = p.date.split("-");
    var months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
    var day = dp[2] || "";
    var mon = months[parseInt(dp[1]||"1")-1] || "";
    dateBadge = '<div class="date-badge"><span class="db-mon">' + mon + '</span><span class="db-day">' + day + '</span></div>';
  } else {
    dateBadge = '<span>' + cm.icon + "</span>";
  }
  var postUrl = "post.html?slug=" + encodeURIComponent(p.slug);
  var thumbImg = p.image
    ? '<img src="' + escapeHTML(p.image) + '" alt="" loading="lazy">'
    : '<img class="post-logo" src="assets/logo.png" alt="Algorithmic Gyan logo" loading="lazy">';
  return '<a href="' + postUrl + '" style="text-decoration:none;color:inherit;display:block"><article class="card text-card">'
    + '<div class="thumb">' + badge + thumbImg + dateBadge + "</div>"
    + '<div class="card-body"><h3>' + escapeHTML(p.title) + "</h3>" + desc
    + '<div class="meta">' + date + "</div></div></article></a>"
    + shareRowHTML(p.title, SITE_URL + postUrl, p.slug);
}

function emptyHTML() {
  return '<div class="empty"><div class="big">📭</div>'
    + "<p><strong>Abhi koi post nahi hai.</strong></p>"
    + "<p>Nayi posts jald aa rahi hain — tab tak YouTube channel par videos dekho!</p></div>";
}

function sortPosts(posts) {
  return posts.slice().sort(function (a, b) {
    if (!a.date) return 1;
    if (!b.date) return -1;
    return b.date < a.date ? -1 : (b.date > a.date ? 1 : 0);
  });
}

function fetchPosts() {
  return fetch("data/posts.json").then(function (r) { return r.json(); })
    .then(function (d) { return sortPosts(d.posts || []); })
    .catch(function () { return []; });
}

function loadHome() {
  fetchPosts().then(function (posts) {
    var grid = document.getElementById("latestGrid");
    if (!posts.length) { grid.innerHTML = emptyHTML(); return; }
    grid.innerHTML = posts.slice(0, 6).map(cardHTML).join("");
  });
  // Latest videos on homepage
  fetch("data/videos.json").then(function (r) { return r.json(); }).then(function (videos) {
    var grid = document.getElementById("latestVideos");
    if (!grid) return;
    grid.innerHTML = videos.slice(0, 6).map(function (v) {
      var yurl = "https://www.youtube.com/watch?v=" + v.id;
      return '<a class="card" href="' + yurl + '" target="_blank" rel="noopener">'
        + '<div class="thumb"><span class="badge">🎬 Video</span>'
        + '<img src="https://i.ytimg.com/vi/' + v.id + '/hqdefault.jpg" alt="" loading="lazy" onerror="this.style.display=\'none\'">'
        + '<span class="play">▶</span></div>'
        + '<div class="card-body"><h3>' + escapeHTML(v.title) + "</h3></div></a>"
      + '<div class="share-row">'
      + '<a class="share-btn wa" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(v.title + " " + yurl) + '">📲 WhatsApp</a>'
      + '<a class="share-btn wb" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(v.title + " " + yurl) + '">💼 WhatsApp Business</a>'
      + '<a class="share-btn fb" target="_blank" rel="noopener" href="https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(yurl) + '">👍 Facebook</a>'
      + '<a class="share-btn tw" target="_blank" rel="noopener" href="https://twitter.com/intent/tweet?text=' + encodeURIComponent(v.title) + '&url=' + encodeURIComponent(yurl) + '">𝕏 X</a>'
      + '<a class="share-btn tg" target="_blank" rel="noopener" href="https://t.me/share/url?url=' + encodeURIComponent(yurl) + '&text=' + encodeURIComponent(v.title) + '">✈️ Telegram</a>'
      + '<button class="share-btn cp" onclick="agCopy(\'' + yurl + '\',this)">🔗 Copy</button>'
      + "</div>";
    }).join("");
  }).catch(function () {});
}

function loadPosts() {
  var params = new URLSearchParams(window.location.search);
  var startCat = params.get("cat") || "all";

  var chips = document.querySelectorAll("#chips .chip");
  function setActive(cat) {
    chips.forEach(function (c) { c.classList.toggle("active", c.dataset.cat === cat); });
  }
  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      setActive(c.dataset.cat);
      render(c.dataset.cat);
    });
  });

  var all = [];
  function render(cat) {
    var grid = document.getElementById("postsGrid");
    var list = cat === "all" ? all : all.filter(function (p) { return p.category === cat; });
    grid.innerHTML = list.length ? list.map(cardHTML).join("") : emptyHTML();
  }

  fetchPosts().then(function (posts) {
    all = posts;
    setActive(startCat);
    render(startCat);
  });
}

var _vss = document.createElement("style");
_vss.textContent = ".share-row{display:flex;flex-wrap:wrap;gap:6px;padding:0 12px 12px}.share-btn{flex:1 1 90px;text-align:center;padding:8px;border-radius:8px;font-size:.85rem;font-weight:700;cursor:pointer;border:none;color:#fff !important;text-decoration:none}.share-btn.wa{background:#25D366}.share-btn.wb{background:#075E54}.share-btn.fb{background:#1877F2}.share-btn.tw{background:#000}.share-btn.tg{background:#229ED9}.share-btn.cp{background:#555}.share-btn.dl{background:#7C3AED}.text-card .thumb img{position:absolute;inset:0}.text-card .thumb img.post-logo{object-fit:contain;padding:10px;box-sizing:border-box}.text-card .thumb .date-badge{position:absolute;right:10px;bottom:10px;z-index:2}";
document.head.appendChild(_vss);

var _dbCss = document.createElement("style");
_dbCss.textContent = ".date-badge{display:flex;flex-direction:column;align-items:center;background:#fff;border-radius:12px;padding:8px 16px;box-shadow:0 2px 8px rgba(0,0,0,.2)}.db-mon{background:#e53935;color:#fff;font-size:.7rem;font-weight:800;padding:2px 10px;border-radius:6px 6px 0 0;letter-spacing:1px}.db-day{font-size:1.8rem;font-weight:800;color:#222;line-height:1.2}";
document.head.appendChild(_dbCss);
