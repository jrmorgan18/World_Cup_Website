(function () {
  "use strict";
  var TEAMS = window.WC_TEAMS || {};
  var BASE = window.WC_BASE || "";

  /* ---- View toggle ---- */
  var toggle = document.querySelector(".view-toggle");
  if (toggle) {
    toggle.addEventListener("click", function (e) {
      var btn = e.target.closest(".view-btn");
      if (!btn) return;
      var view = btn.getAttribute("data-view");
      toggle.querySelectorAll(".view-btn").forEach(function (b) {
        var active = b === btn;
        b.classList.toggle("active", active);
        b.setAttribute("aria-selected", active ? "true" : "false");
      });
      document.getElementById("view-group").hidden = view !== "group";
      document.getElementById("view-date").hidden = view !== "date";
    });
  }

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
    mmVenue.textContent = card.getAttribute("data-city") + " · " + card.getAttribute("data-venue");
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
