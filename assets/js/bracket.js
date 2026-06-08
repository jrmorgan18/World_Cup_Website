(function () {
  "use strict";
  var TEAMS = window.WC_TEAMS || {};
  var GROUPS = window.WC_GROUPS || {};
  var GROUP_ORDER = window.WC_GROUP_ORDER || [];
  var BASE = window.WC_BASE || "";

  // Round-of-32 layout. Tokens: W:<g> group winner, R:<g> runner-up, T:<i> third slot.
  // Third slot i is paired with the winner group in SLOT_WG[i] (used to avoid same-group ties).
  var SLOT_WG = ["A", "C", "E", "G", "B", "D", "F", "H"];
  var R32SPECS = [
    ["W:A", "T:0"], ["R:B", "R:C"], ["W:C", "T:1"], ["W:I", "R:K"],
    ["W:E", "T:2"], ["R:F", "R:G"], ["W:G", "T:3"], ["W:L", "R:J"],
    ["W:B", "T:4"], ["R:A", "R:D"], ["W:D", "T:5"], ["W:J", "R:L"],
    ["W:F", "T:6"], ["R:E", "R:H"], ["W:H", "T:7"], ["W:K", "R:I"]
  ];

  var state = { order: {}, thirds: [], picks: { R32: {}, R16: {}, QF: {}, SF: {}, F: {}, T3: {} } };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function code(name) { var t = TEAMS[name]; return t ? t.code : ""; }
  function flag(name, w) { return '<img class="b-flag" src="https://flagcdn.com/w' + (w || 40) + "/" + esc(code(name)) + '.png" alt="">'; }
  function grp(name) { var t = TEAMS[name]; return t ? t.group : ""; }

  /* ---------- persistence ---------- */
  function save() {
    try { localStorage.setItem("wc_bracket", JSON.stringify(state)); } catch (e) {}
  }
  function encodeState() {
    try { return btoa(unescape(encodeURIComponent(JSON.stringify(state)))); } catch (e) { return ""; }
  }
  function decodeState(str) {
    try { return JSON.parse(decodeURIComponent(escape(atob(str)))); } catch (e) { return null; }
  }
  function load() {
    var fromHash = location.hash && location.hash.length > 1 ? decodeState(location.hash.slice(1)) : null;
    var s = fromHash;
    if (!s) {
      try { s = JSON.parse(localStorage.getItem("wc_bracket") || "null"); } catch (e) { s = null; }
    }
    if (s && s.order) {
      state.order = s.order || {};
      state.thirds = s.thirds || [];
      state.picks = Object.assign({ R32: {}, R16: {}, QF: {}, SF: {}, F: {}, T3: {} }, s.picks || {});
    }
  }

  /* ---------- group predictions ---------- */
  function groupComplete(g) { return (state.order[g] || []).length >= 3; }
  function allGroupsComplete() { return GROUP_ORDER.every(groupComplete); }

  function renderGroups() {
    var host = document.getElementById("b-groups");
    host.innerHTML = GROUP_ORDER.map(function (g) {
      var order = state.order[g] || [];
      var teams = GROUPS[g].map(function (tn) {
        var pos = order.indexOf(tn);
        return '<button type="button" class="b-team' + (pos >= 0 ? " ranked" : "") + '" data-group="' + g + '" data-team="' + esc(tn) + '">'
          + '<span class="b-rank">' + (pos >= 0 ? pos + 1 : "") + "</span>"
          + flag(tn) + '<span class="b-tname">' + esc(tn) + "</span></button>";
      }).join("");
      return '<div class="b-group">'
        + '<div class="b-group-head"><h3>Group ' + g + "</h3>"
        + '<button type="button" class="b-group-reset" data-group="' + g + '" title="Clear group">&#8635;</button></div>'
        + '<div class="b-group-teams">' + teams + "</div></div>";
    }).join("");
  }

  function onGroupClick(e) {
    var reset = e.target.closest(".b-group-reset");
    if (reset) { state.order[reset.getAttribute("data-group")] = []; pruneThirds(); commit(); return; }
    var btn = e.target.closest(".b-team");
    if (!btn) return;
    var g = btn.getAttribute("data-group"), tn = btn.getAttribute("data-team");
    var order = state.order[g] || (state.order[g] = []);
    var i = order.indexOf(tn);
    if (i >= 0) order.splice(i, 1);
    else if (order.length < 4) order.push(tn);
    pruneThirds();
    commit();
  }

  /* ---------- best thirds ---------- */
  function thirdsPool() { return GROUP_ORDER.map(function (g) { return (state.order[g] || [])[2]; }); }
  function pruneThirds() {
    var pool = thirdsPool();
    state.thirds = state.thirds.filter(function (t) { return t && pool.indexOf(t) !== -1; });
  }
  function renderThirds() {
    var step = document.getElementById("b-thirds-step");
    if (!allGroupsComplete()) { step.hidden = true; return; }
    step.hidden = false;
    document.getElementById("b-thirds-count").textContent = state.thirds.length + " / 8";
    var host = document.getElementById("b-thirds");
    host.innerHTML = GROUP_ORDER.map(function (g) {
      var tn = (state.order[g] || [])[2];
      var sel = state.thirds.indexOf(tn) !== -1;
      var dis = !sel && state.thirds.length >= 8;
      return '<button type="button" class="b-third' + (sel ? " sel" : "") + (dis ? " dis" : "") + '" data-team="' + esc(tn) + '"' + (dis ? " disabled" : "") + ">"
        + flag(tn) + '<span class="b-third-info"><span class="b-tname">' + esc(tn) + "</span><small>3rd &middot; Group " + g + "</small></span>"
        + '<span class="b-check">' + (sel ? "&#10003;" : "") + "</span></button>";
    }).join("");
  }
  function onThirdClick(e) {
    var btn = e.target.closest(".b-third");
    if (!btn || btn.disabled) return;
    var tn = btn.getAttribute("data-team");
    var i = state.thirds.indexOf(tn);
    if (i >= 0) state.thirds.splice(i, 1);
    else if (state.thirds.length < 8) state.thirds.push(tn);
    commit();
  }

  /* ---------- bracket ---------- */
  function assignThirds(chosen) {
    var res = new Array(8).fill(null);
    var used = new Array(chosen.length).fill(false);
    function bt(slot) {
      if (slot === 8) return true;
      for (var k = 0; k < chosen.length; k++) {
        if (used[k]) continue;
        if (grp(chosen[k]) === SLOT_WG[slot]) continue;
        used[k] = true; res[slot] = chosen[k];
        if (bt(slot + 1)) return true;
        used[k] = false; res[slot] = null;
      }
      return false;
    }
    if (!bt(0)) for (var s = 0; s < 8; s++) res[s] = chosen[s] || null;
    return res;
  }
  function resolve(tok, thirdAssign) {
    var p = tok.split(":"), t = p[0], v = p[1];
    if (t === "W") return (state.order[v] || [])[0] || null;
    if (t === "R") return (state.order[v] || [])[1] || null;
    return thirdAssign[+v] || null;
  }
  function buildMatch(round, i, a, b) {
    var pick = state.picks[round][i];
    if (pick && pick !== a && pick !== b) { pick = null; delete state.picks[round][i]; }
    return { a: a, b: b, w: pick || null };
  }
  function loserOf(m) { return m.w && m.a && m.b ? (m.w === m.a ? m.b : m.a) : null; }

  function computeBracket() {
    var ta = assignThirds(state.thirds);
    var R32 = R32SPECS.map(function (s, i) { return buildMatch("R32", i, resolve(s[0], ta), resolve(s[1], ta)); });
    var R16 = [], QF = [], SF = [], i;
    for (i = 0; i < 8; i++) R16.push(buildMatch("R16", i, R32[2 * i].w, R32[2 * i + 1].w));
    for (i = 0; i < 4; i++) QF.push(buildMatch("QF", i, R16[2 * i].w, R16[2 * i + 1].w));
    for (i = 0; i < 2; i++) SF.push(buildMatch("SF", i, QF[2 * i].w, QF[2 * i + 1].w));
    var F = buildMatch("F", 0, SF[0].w, SF[1].w);
    var T3 = buildMatch("T3", 0, loserOf(SF[0]), loserOf(SF[1]));
    return { R32: R32, R16: R16, QF: QF, SF: SF, F: F, T3: T3 };
  }

  function slot(round, idx, team, winner) {
    var cls = "b-slot";
    if (!team) cls += " tbd";
    else if (winner === team) cls += " won";
    else if (winner) cls += " lost";
    return '<button type="button" class="' + cls + '" data-round="' + round + '" data-match="' + idx + '"'
      + (team ? ' data-team="' + esc(team) + '"' : " disabled") + ">"
      + (team ? flag(team) + '<span class="b-tname">' + esc(team) + "</span>" : '<span class="b-tname b-tbd">TBD</span>')
      + "</button>";
  }
  function matchCard(round, idx, m) {
    return '<div class="b-match">' + slot(round, idx, m.a, m.w) + slot(round, idx, m.b, m.w) + "</div>";
  }
  function column(label, round, matches) {
    return '<div class="b-col"><div class="b-col-head">' + label + "</div>"
      + matches.map(function (m, i) { return matchCard(round, i, m); }).join("") + "</div>";
  }

  function renderBracket() {
    var step = document.getElementById("b-bracket-step");
    if (!allGroupsComplete() || state.thirds.length !== 8) { step.hidden = true; return; }
    step.hidden = false;
    var b = computeBracket();
    var host = document.getElementById("b-bracket");
    host.innerHTML =
      column("Round of 32", "R32", b.R32) +
      column("Round of 16", "R16", b.R16) +
      column("Quarter-finals", "QF", b.QF) +
      column("Semi-finals", "SF", b.SF) +
      '<div class="b-col b-col-final"><div class="b-col-head">Final</div>' + matchCard("F", 0, b.F)
        + '<div class="b-col-head b-3rd-head">Third place</div>' + matchCard("T3", 0, b.T3) + "</div>";

    var champEl = document.getElementById("b-champion");
    if (b.F.w) {
      champEl.hidden = false;
      champEl.innerHTML = '<span class="b-champ-label">Your champion</span>'
        + flag(b.F.w, 160) + '<span class="b-champ-name">' + esc(b.F.w) + " &#127942;</span>";
    } else {
      champEl.hidden = true;
    }
  }
  function onBracketClick(e) {
    var btn = e.target.closest(".b-slot");
    if (!btn || btn.disabled) return;
    var team = btn.getAttribute("data-team");
    if (!team) return;
    state.picks[btn.getAttribute("data-round")][btn.getAttribute("data-match")] = team;
    commit();
  }

  /* ---------- status / orchestration ---------- */
  function renderStatus() {
    var done = GROUP_ORDER.filter(groupComplete).length;
    var el = document.getElementById("bracket-status");
    var inc = document.getElementById("bracket-incomplete");
    var champ = state.picks.F[0];
    if (champ && allGroupsComplete() && state.thirds.length === 8) {
      el.innerHTML = "Your champion: <strong>" + esc(champ) + "</strong> &#127942;";
      inc.hidden = true;
    } else if (!allGroupsComplete()) {
      el.textContent = done + " / 12 groups predicted";
      inc.hidden = false;
    } else if (state.thirds.length !== 8) {
      el.textContent = "Pick " + (8 - state.thirds.length) + " more third-place team(s)";
      inc.hidden = true;
    } else {
      el.textContent = "Bracket ready — pick your winners";
      inc.hidden = true;
    }
  }

  function render() {
    renderGroups();
    renderThirds();
    renderBracket();
    renderStatus();
  }
  function commit() { save(); writeHash(); render(); }

  var hashTimer = null;
  function writeHash() {
    if (hashTimer) clearTimeout(hashTimer);
    hashTimer = setTimeout(function () {
      try { history.replaceState(null, "", "#" + encodeState()); } catch (e) {}
    }, 250);
  }

  /* ---------- wire up ---------- */
  document.getElementById("b-groups").addEventListener("click", onGroupClick);
  document.getElementById("b-thirds").addEventListener("click", onThirdClick);
  document.getElementById("b-bracket").addEventListener("click", onBracketClick);

  document.getElementById("bracket-reset").addEventListener("click", function () {
    if (!confirm("Clear your entire bracket?")) return;
    state = { order: {}, thirds: [], picks: { R32: {}, R16: {}, QF: {}, SF: {}, F: {}, T3: {} } };
    try { localStorage.removeItem("wc_bracket"); } catch (e) {}
    try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
    render();
  });
  document.getElementById("bracket-share").addEventListener("click", function (e) {
    var url = location.origin + location.pathname + "#" + encodeState();
    var btn = e.target;
    function done() { var t = btn.textContent; btn.textContent = "Link copied!"; setTimeout(function () { btn.textContent = t; }, 1600); }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(url).then(done, function () { prompt("Copy your bracket link:", url); });
    else prompt("Copy your bracket link:", url);
  });

  load();
  render();
})();
