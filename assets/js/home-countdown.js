(function () {
  "use strict";
  var MATCHES = window.WC_MATCHES || [];
  var TEAMS = window.WC_TEAMS || {};
  var BASE = window.WC_BASE || "";
  var section = document.getElementById("kickoff-section");
  if (!section || !MATCHES.length) return;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function code(name) { var t = TEAMS[name]; return t ? t.code : ""; }

  function to24(t) {
    var m = String(t).match(/(\d+):(\d+)\s*(AM|PM)/i);
    if (!m) return [0, 0];
    var h = parseInt(m[1], 10) % 12;
    if (/PM/i.test(m[3])) h += 12;
    return [h, parseInt(m[2], 10)];
  }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function matchDate(m) {
    var hm = to24(m.time); // June 2026 is EDT (UTC-4)
    return new Date(m.date + "T" + pad(hm[0]) + ":" + pad(hm[1]) + ":00-04:00");
  }
  function etDateStr(d) {
    var parts = new Intl.DateTimeFormat("en-CA", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(d);
    var o = {}; parts.forEach(function (p) { o[p.type] = p.value; });
    return o.year + "-" + o.month + "-" + o.day;
  }
  function prettyDate(iso) {
    var d = new Date(iso + "T12:00:00-04:00");
    return new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", weekday: "long", month: "long", day: "numeric" }).format(d);
  }

  MATCHES.forEach(function (m) { m._dt = matchDate(m); });
  MATCHES.sort(function (a, b) { return a._dt - b._dt; });
  var opener = MATCHES[0]._dt;

  var matchesWrap = section.querySelector(".kickoff-matches");
  function matchRow(m) {
    return '<a class="ko-match" href="' + BASE + '/schedule/">'
      + '<span class="ko-time">' + esc(m.time) + " " + esc(m.tz) + "</span>"
      + '<span class="ko-fixture">'
      +   '<span class="ko-team ko-home"><span class="ko-name">' + esc(m.home) + "</span>"
      +     '<img class="ko-flag" src="https://flagcdn.com/w40/' + esc(code(m.home)) + '.png" alt=""></span>'
      +   '<span class="ko-vs">v</span>'
      +   '<span class="ko-team ko-away"><img class="ko-flag" src="https://flagcdn.com/w40/' + esc(code(m.away)) + '.png" alt="">'
      +     '<span class="ko-name">' + esc(m.away) + "</span></span>"
      + "</span>"
      + '<span class="ko-grp">Grp ' + esc(m.group) + "</span>"
      + "</a>";
  }

  function renderMatches() {
    var now = new Date();
    var today = etDateStr(now);
    var title = document.getElementById("kickoff-matches-title");
    var list = document.getElementById("kickoff-list");
    if (!title || !list) return;
    var todays = MATCHES.filter(function (m) { return m.date === today; });
    var rows, label;
    if (todays.length) {
      label = "Today's Matches";
      rows = todays;
    } else {
      var upcoming = MATCHES.filter(function (m) { return m._dt >= now; });
      if (!upcoming.length) {
        matchesWrap.innerHTML = '<div class="kickoff-done">The group stage is complete. <a href="' + BASE + '/schedule/">See the full schedule &rarr;</a></div>';
        return;
      }
      var nextDate = upcoming[0].date;
      rows = MATCHES.filter(function (m) { return m.date === nextDate; });
      label = "Up Next &middot; " + prettyDate(nextDate);
    }
    title.innerHTML = label;
    list.innerHTML = rows.map(matchRow).join("");
  }

  var cdEl = document.getElementById("kickoff-countdown");
  var timer = null;
  function liveBanner() {
    cdEl.innerHTML = '';
  }
  function renderCountdown() {
    var now = new Date();
    var diff = opener - now;
    if (diff <= 0) {
      liveBanner();
      if (timer) { clearInterval(timer); timer = null; }
      renderMatches();
      return;
    }
    var s = Math.floor(diff / 1000);
    var d = Math.floor(s / 86400); s -= d * 86400;
    var h = Math.floor(s / 3600); s -= h * 3600;
    var mi = Math.floor(s / 60); s -= mi * 60;
    function box(v, l) { return '<div class="ko-cd-box"><span class="ko-cd-num">' + v + '</span><span class="ko-cd-lab">' + l + "</span></div>"; }
    var op = MATCHES[0];
    cdEl.innerHTML = '<div class="ko-cd-title">Kickoff in</div>'
      + '<div class="ko-cd-grid">' + box(d, "days") + box(h, "hrs") + box(mi, "min") + box(s, "sec") + "</div>"
      + '<div class="ko-cd-sub">' + esc(op.home) + " v " + esc(op.away) + " &middot; " + esc(op.time) + " " + esc(op.tz) + " &middot; " + prettyDate(op.date) + "</div>";
  }

  section.hidden = false;
  renderMatches();
  if (opener - new Date() > 0) {
    renderCountdown();
    timer = setInterval(renderCountdown, 1000);
  } else {
    liveBanner();
  }
})();
