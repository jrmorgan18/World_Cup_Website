(function () {
  "use strict";
  var TEAMS = window.WC_TEAMS || {};
  var BASE = window.WC_BASE || "";

  var groupView = document.getElementById("view-group");
  var dateView = document.getElementById("view-date");
  var teamView = document.getElementById("view-team");

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
      groupView.hidden = view !== "group";
      dateView.hidden = view !== "date";
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
    groupView.hidden = v !== "group";
    dateView.hidden = v !== "date";
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
    mmGroup.textContent = "Group " + card.getAttribute("data-group");
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
    if (card) { openMatch(card); return; }
    var tt = e.target.closest(".team-trigger");
    if (tt) { openTeam(tt.getAttribute("data-team")); return; }
    if (e.target.closest("[data-close]")) { close(); return; }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) close();
  });
})();
