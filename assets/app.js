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

function cardHTML(p) {
  var cm = catMeta(p.category);
  var badge = '<span class="badge"><span class="dot" style="background:' + cm.color + '"></span> '
    + escapeHTML(cm.label) + "</span>";
  var date = p.date ? '<span class="date">📅 ' + escapeHTML(p.date) + "</span>" : "";
  var desc = p.description ? '<p class="desc">' + escapeHTML(p.description) + "</p>" : "";
  var vid = getVideoId(p.youtube_url);

  if (vid) {
    return '<a class="card" href="' + escapeHTML(p.youtube_url) + '" target="_blank" rel="noopener">'
      + '<div class="thumb">' + badge
      + '<img src="https://i.ytimg.com/vi/' + vid + '/hqdefault.jpg" alt="" loading="lazy" onerror="this.style.display=\'none\'">'
      + '<span class="play">▶</span></div>'
      + '<div class="card-body"><h3>' + escapeHTML(p.title) + "</h3>" + desc
      + '<div class="meta">' + date + "</div></div></a>";
  }
  return '<article class="card text-card">'
    + '<div class="thumb">' + badge + '<span>' + cm.icon + "</span></div>"
    + '<div class="card-body"><h3>' + escapeHTML(p.title) + "</h3>" + desc
    + '<div class="meta">' + date + "</div></div></article>";
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
      + '<a class="share-btn wa" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(v.title + " " + yurl) + '">📲 Share</a>'
      + '<a class="share-btn fb" target="_blank" rel="noopener" href="https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(yurl) + '">👍 Share</a>'
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
_vss.textContent = ".share-row{display:flex;gap:6px;padding:0 12px 12px}.share-btn{flex:1;text-align:center;padding:8px;border-radius:8px;font-size:.85rem;font-weight:700;cursor:pointer;border:none;color:#fff;text-decoration:none}.share-btn.wa{background:#25D366}.share-btn.fb{background:#1877F2}";
document.head.appendChild(_vss);
