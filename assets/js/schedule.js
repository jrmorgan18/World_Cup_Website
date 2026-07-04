(function () {
  "use strict";
  var TEAMS = window.WC_TEAMS || {};
  var BASE = window.WC_BASE || "";
  var MATCHES = window.WC_MATCHES || [];
  var GROUPS = window.WC_GROUPS || {};
  var GROUP_ORDER = window.WC_GROUP_ORDER || [];

  var groupView = document.getElementById("view-group");
  var dateView = document.getElementById("view-date");
  var teamView = document.getElementById("view-team");
  var standingsView = document.getElementById("view-standings");
  var knockoutView = document.getElementById("view-knockout");
  var standingsBuilt = false;

  function setView(view) {
    groupView.hidden = view !== "group";
    dateView.hidden = view !== "date";
    if (standingsView) standingsView.hidden = view !== "standings";
    if (knockoutView) knockoutView.hidden = view !== "knockout";
    if (view === "standings" && !standingsBuilt) { buildStandings(); standingsBuilt = true; }
  }

  /* ---- View toggle ---- */
  var toggle = document.querySelector(".view-toggle");
  if (toggle) {
    toggle.addEventListener("click", function (e) {
      var btn = e.target.closest(".view-btn");
      if (!btn) return;
      clearTeam();
      var view = btn.getAttribute("data-view");
      toggle.querySelectorAll(".view-btn").forEach(function (b) {
        var active = b === btn;
        b.classList.toggle("active", active);
        b.setAttribute("aria-selected", active ? "true" : "false");
      });
      setView(view);
    });
  }

  /* ---- Team search ---- */
  var TEAM_NAMES = Object.keys(TEAMS).sort(function (a, b) { return a.localeCompare(b); });
  var searchInput = document.getElementById("team-search-input");
  var clearBtn = document.getElementById("team-clear");
  var teamHeader = document.getElementById("team-sched-header");
  var teamList = document.getElementById("team-sched-list");
  var datalist = document.getElementById("team-list");
  if (datalist) {
    datalist.innerHTML = TEAM_NAMES.map(function (n) {
      return '<option value="' + n.replace(/"/g, "&quot;") + '"></option>';
    }).join("");
  }

  var ALIASES = {
    "usa": "United States", "us": "United States", "u.s.": "United States",
    "u.s.a.": "United States", "united states of america": "United States", "america": "United States",
    "holland": "Netherlands", "ned": "Netherlands",
    "korea": "South Korea", "korea republic": "South Korea",
    "turkey": "Türkiye", "turkiye": "Türkiye",
    "czech republic": "Czechia", "czech": "Czechia",
    "cote d'ivoire": "Ivory Coast", "cote divoire": "Ivory Coast", "côte d'ivoire": "Ivory Coast",
    "cabo verde": "Cape Verde",
    "congo": "DR Congo", "drc": "DR Congo", "congo dr": "DR Congo",
    "bosnia": "Bosnia and Herzegovina"
  };

  function resolveTeam(q) {
    if (!q) return null;
    q = q.trim().toLowerCase();
    if (!q) return null;
    var i;
    if (ALIASES[q] && TEAMS[ALIASES[q]]) return ALIASES[q];
    for (i = 0; i < TEAM_NAMES.length; i++) if (TEAM_NAMES[i].toLowerCase() === q) return TEAM_NAMES[i];
    for (i = 0; i < TEAM_NAMES.length; i++) if (TEAM_NAMES[i].toLowerCase().indexOf(q) === 0) return TEAM_NAMES[i];
    for (i = 0; i < TEAM_NAMES.length; i++) if (TEAM_NAMES[i].toLowerCase().indexOf(q) !== -1) return TEAM_NAMES[i];
    var alias;
    for (alias in ALIASES) if (alias.indexOf(q) === 0 && TEAMS[ALIASES[alias]]) return ALIASES[alias];
    return null;
  }

  function showTeam(name) {
    var t = TEAMS[name];
    if (!t || !teamView) return;
    var meta = ["Group " + esc(t.group)];
    if (t.fifa_rank) meta.push("FIFA #" + esc(t.fifa_rank));
    if (t.formation) meta.push(esc(t.formation));
    if (t.style) meta.push(esc(t.style));
    var hh = '<img class="tsh-flag" src="https://flagcdn.com/w160/' + esc(t.code) + '.png" alt="">';
    hh += '<div class="tsh-info"><h2>' + esc(t.name) + "</h2>";
    hh += '<p class="tsh-meta">' + meta.join(" &middot; ") + "</p>";
    if (t.url) hh += '<a class="mt-link" href="' + esc(BASE + t.url) + '">Full capsule &rarr;</a>';
    teamHeader.innerHTML = hh + "</div>";
    teamList.innerHTML = "";
    var n = 0;
    groupView.querySelectorAll(".match-card").forEach(function (c) {
      if (c.getAttribute("data-home") === name || c.getAttribute("data-away") === name) {
        teamList.appendChild(c.cloneNode(true));
        n++;
      }
    });
    if (!n) teamList.innerHTML = '<p class="empty-state">No fixtures found.</p>';
    groupView.hidden = true;
    dateView.hidden = true;
    if (standingsView) standingsView.hidden = true;
    if (knockoutView) knockoutView.hidden = true;
    teamView.hidden = false;
    clearBtn.hidden = false;
  }

  function clearTeam() {
    if (!teamView || teamView.hidden) return;
    teamView.hidden = true;
    clearBtn.hidden = true;
    if (searchInput) searchInput.value = "";
    var active = document.querySelector(".view-btn.active");
    var v = active ? active.getAttribute("data-view") : "group";
    setView(v);
  }

  function trySearch() {
    var name = resolveTeam(searchInput.value);
    if (name) { searchInput.value = name; showTeam(name); }
  }
  if (searchInput) {
    searchInput.addEventListener("change", trySearch);
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); trySearch(); }
    });
    searchInput.addEventListener("search", function () {
      if (!searchInput.value) clearTeam();
    });
  }
  if (clearBtn) clearBtn.addEventListener("click", clearTeam);

  /* ---- Modal ---- */
  var modal = document.getElementById("match-modal");
  var mmGroup = document.getElementById("mm-group");
  var mmDateTime = document.getElementById("mm-datetime");
  var mmVenue = document.getElementById("mm-venue");
  var mmHome = document.getElementById("mm-home");
  var mmAway = document.getElementById("mm-away");
  var mmTitle = document.getElementById("mm-title");
  var lastFocus = null;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function teamPanel(name) {
    var t = TEAMS[name];
    if (!t) return '<div class="modal-team-inner"><h3>' + esc(name) + "</h3></div>";
    var html = '<div class="modal-team-inner">';
    html += '<img class="mt-flag" src="https://flagcdn.com/w160/' + esc(t.code) + '.png" alt="">';
    html += "<h3>" + esc(t.name) + "</h3>";
    var meta = [];
    meta.push("Group " + esc(t.group));
    if (t.fifa_rank) meta.push("FIFA #" + esc(t.fifa_rank));
    if (t.rank) meta.push("Countdown #" + esc(t.rank));
    html += '<p class="mt-meta">' + meta.join(" &middot; ") + "</p>";
    if (t.formation || t.style) {
      html += '<div class="mt-tactics">';
      if (t.formation) html += '<div class="mt-tac"><span class="mt-tac-label">Formation</span><span class="mt-tac-val">' + esc(t.formation) + "</span></div>";
      if (t.style) html += '<div class="mt-tac"><span class="mt-tac-label">Style of play</span><span class="mt-tac-val">' + esc(t.style) + "</span></div>";
      html += "</div>";
    }
    if (t.blurb) html += '<p class="mt-blurb">' + esc(t.blurb) + "</p>";
    if (t.players && t.players.length) {
      html += '<ul class="mt-players">';
      t.players.forEach(function (p) {
        var sub = [p.pos, p.club].filter(Boolean).join(" · ");
        html += "<li><strong>" + esc(p.name) + "</strong>" + (sub ? '<span>' + esc(sub) + "</span>" : "") + "</li>";
      });
      html += "</ul>";
    }
    if (t.odds_cup) html += '<p class="mt-odds">Odds to win Cup: <strong>' + esc(t.odds_cup) + "</strong></p>";
    if (t.url) {
      html += '<a class="mt-link" href="' + esc(BASE + t.url) + '">Full capsule &rarr;</a>';
    } else {
      html += '<p class="mt-soon">Full capsule coming soon</p>';
    }
    html += "</div>";
    return html;
  }

  function openMatch(card) {
    var home = card.getAttribute("data-home");
    var away = card.getAttribute("data-away");
    var round = card.getAttribute("data-round");
    mmGroup.textContent = round ? round : "Group " + card.getAttribute("data-group");
    mmGroup.hidden = false;
    mmDateTime.textContent = card.getAttribute("data-date") + " · " + card.getAttribute("data-time");
    mmVenue.textContent = card.getAttribute("data-venue");
    mmHome.innerHTML = teamPanel(home);
    mmAway.innerHTML = teamPanel(away);
    document.querySelector(".modal-vs").hidden = false;
    mmTitle.textContent = home + " versus " + away;
    show();
  }

  function openTeam(name) {
    var t = TEAMS[name];
    mmGroup.textContent = t ? "Group " + t.group : "";
    mmGroup.hidden = !t;
    mmDateTime.textContent = "";
    mmVenue.textContent = "";
    mmHome.innerHTML = teamPanel(name);
    mmAway.innerHTML = "";
    document.querySelector(".modal-vs").hidden = true;
    mmTitle.textContent = name + " preview";
    show();
  }

  function show() {
    lastFocus = document.activeElement;
    modal.hidden = false;
    document.body.classList.add("modal-open");
    var closeBtn = modal.querySelector(".modal-close");
    if (closeBtn) closeBtn.focus();
  }

  function close() {
    modal.hidden = true;
    document.body.classList.remove("modal-open");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  document.addEventListener("click", function (e) {
    var card = e.target.closest(".match-card");
    if (card) { if (card.getAttribute("data-home")) openMatch(card); return; }
    var tt = e.target.closest(".team-trigger");
    if (tt) { openTeam(tt.getAttribute("data-team")); return; }
    if (e.target.closest("[data-close]")) { close(); return; }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) close();
  });

  /* ---- Standings ---- */
  function isFinal(m) {
    return typeof m.home_score === "number" && typeof m.away_score === "number" &&
      (m.status == null || m.status === "FINISHED");
  }

  function h2h(x, y, played) {
    var px = 0, py = 0;
    played.forEach(function (m) {
      var involved = (m.home === x && m.away === y) || (m.home === y && m.away === x);
      if (!involved) return;
      var xs = m.home === x ? m.home_score : m.away_score;
      var ys = m.home === x ? m.away_score : m.home_score;
      if (xs > ys) px += 3; else if (xs < ys) py += 3; else { px++; py++; }
    });
    return py - px; // positive => y ranks above x
  }

  function computeGroup(g) {
    var teams = (GROUPS[g] || []).slice();
    var row = {};
    teams.forEach(function (t) { row[t] = { team: t, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0 }; });
    var played = MATCHES.filter(function (m) { return m.group === g && isFinal(m); });
    played.forEach(function (m) {
      var H = row[m.home], A = row[m.away];
      if (!H || !A) return;
      var hs = m.home_score, as = m.away_score;
      H.p++; A.p++; H.gf += hs; H.ga += as; A.gf += as; A.ga += hs;
      if (hs > as) { H.w++; A.l++; H.pts += 3; }
      else if (hs < as) { A.w++; H.l++; A.pts += 3; }
      else { H.d++; A.d++; H.pts++; A.pts++; }
    });
    var arr = teams.map(function (t) { var r = row[t]; r.gd = r.gf - r.ga; return r; });
    arr.sort(function (a, b) {
      if (b.pts !== a.pts) return b.pts - a.pts;
      if (b.gd !== a.gd) return b.gd - a.gd;
      if (b.gf !== a.gf) return b.gf - a.gf;
      var hh = h2h(a.team, b.team, played);
      if (hh) return hh;
      return a.team.localeCompare(b.team);
    });
    return arr;
  }

  function buildStandings() {
    var grid = document.getElementById("standings-grid");
    if (!grid) return;
    grid.innerHTML = GROUP_ORDER.map(function (g) {
      var rows = computeGroup(g);
      var anyPlayed = rows.some(function (r) { return r.p > 0; });
      var body = rows.map(function (r, i) {
        var pos = i + 1;
        var cls = pos <= 2 ? "q1" : (pos === 3 ? "q3" : "");
        var t = TEAMS[r.team] || {};
        return '<tr class="' + cls + '">'
          + '<td class="st-pos">' + pos + "</td>"
          + '<td class="st-team"><img class="st-flag" src="https://flagcdn.com/w40/' + esc(t.code) + '.png" alt="">'
          +   '<button type="button" class="st-name team-trigger" data-team="' + esc(r.team) + '">' + esc(r.team) + "</button></td>"
          + "<td>" + r.p + "</td><td>" + r.w + "</td><td>" + r.d + "</td><td>" + r.l + "</td>"
          + '<td class="st-hide">' + r.gf + '</td><td class="st-hide">' + r.ga + "</td>"
          + "<td>" + (r.gd > 0 ? "+" : "") + r.gd + '</td><td class="st-pts">' + r.pts + "</td>"
          + "</tr>";
      }).join("");
      return '<div class="standings-card">'
        + '<h3 class="standings-title">Group ' + g + (anyPlayed ? "" : ' <span class="st-pending">not started</span>') + "</h3>"
        + '<table class="standings-table"><thead><tr>'
        + '<th>#</th><th class="st-team-h">Team</th><th title="Played">P</th><th title="Won">W</th><th title="Drawn">D</th><th title="Lost">L</th>'
        + '<th class="st-hide" title="Goals for">GF</th><th class="st-hide" title="Goals against">GA</th><th title="Goal difference">GD</th><th title="Points">Pts</th>'
        + "</tr></thead><tbody>" + body + "</tbody></table></div>";
    }).join("");
  }
})();
