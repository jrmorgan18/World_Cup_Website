(function () {
  "use strict";

  var shell = document.querySelector(".gc-shell");
  if (!shell) return;

  var tabs = Array.prototype.slice.call(shell.querySelectorAll("[data-gc-tab]"));
  var panels = Array.prototype.slice.call(shell.querySelectorAll("[data-gc-panel]"));
  var drills = Array.prototype.slice.call(shell.querySelectorAll(".gc-drill"));
  var search = shell.querySelector("[data-gc-search]");
  var chips = Array.prototype.slice.call(shell.querySelectorAll("[data-gc-filter]"));
  var empty = shell.querySelector("[data-gc-empty]");
  var activeFilter = "all";

  function showTab(name, focusTab) {
    tabs.forEach(function (tab) {
      var selected = tab.getAttribute("data-gc-tab") === name;
      tab.setAttribute("aria-selected", selected ? "true" : "false");
      tab.tabIndex = selected ? 0 : -1;
      if (selected && focusTab) tab.focus();
    });
    panels.forEach(function (panel) {
      panel.hidden = panel.getAttribute("data-gc-panel") !== name;
    });
  }

  // Keep the tab in the URL so a coach can share (or bookmark) a specific view.
  function rememberTab(name) {
    if (!window.history || !window.history.replaceState) return;
    // Games is the landing view, so it gets the bare URL.
    window.history.replaceState(null, "", name === "games" ? window.location.pathname : "#" + name);
  }

  tabs.forEach(function (tab, index) {
    tab.addEventListener("click", function () {
      var name = tab.getAttribute("data-gc-tab");
      showTab(name, false);
      rememberTab(name);
    });
    tab.addEventListener("keydown", function (event) {
      var step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
      if (!step) return;
      event.preventDefault();
      var next = tabs[(index + step + tabs.length) % tabs.length];
      showTab(next.getAttribute("data-gc-tab"), true);
    });
  });

  // --- Filtering the drill library -----------------------------------------

  function applyFilters() {
    var term = search ? search.value.trim().toLowerCase() : "";
    var shown = 0;

    drills.forEach(function (drill) {
      var matchesFocus = activeFilter === "all" || drill.getAttribute("data-focus") === activeFilter;
      var matchesTerm = !term || (drill.getAttribute("data-search") || "").indexOf(term) !== -1;
      var visible = matchesFocus && matchesTerm;
      drill.hidden = !visible;
      if (visible) shown += 1;
    });

    if (empty) empty.hidden = shown !== 0;
  }

  if (search) {
    search.addEventListener("input", applyFilters);
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      activeFilter = chip.getAttribute("data-gc-filter");
      chips.forEach(function (other) { other.classList.toggle("is-active", other === chip); });
      applyFilters();
    });
  });

  // --- Cross-links between the two views -----------------------------------

  function reveal(target) {
    if (!target) return;
    target.hidden = false;
    target.open = true;
    // Let the panel swap paint before measuring the scroll position.
    window.requestAnimationFrame(function () {
      target.scrollIntoView({ block: "start", behavior: "smooth" });
    });
  }

  shell.addEventListener("click", function (event) {
    var jump = event.target.closest ? event.target.closest("[data-gc-jump]") : null;
    if (jump) {
      event.preventDefault();
      showTab("games", false);
      reveal(document.getElementById("drill-" + jump.getAttribute("data-gc-jump")));
      return;
    }

    var week = event.target.closest ? event.target.closest("[data-gc-week]") : null;
    if (week) {
      event.preventDefault();
      showTab("plans", false);
      reveal(document.getElementById("week-" + week.getAttribute("data-gc-week")));
    }
  });

  // --- Deep links ----------------------------------------------------------

  function openFromHash() {
    var hash = window.location.hash.replace("#", "");
    if (!hash) return;

    // A bare panel name (#games, #pointers) just switches view.
    if (panels.some(function (p) { return p.getAttribute("data-gc-panel") === hash; })) {
      showTab(hash, false);
      return;
    }

    var target = document.getElementById(hash);
    if (!target) return;

    if (hash.indexOf("drill-") === 0) showTab("games", false);
    else if (hash.indexOf("week-") === 0) showTab("plans", false);
    reveal(target);
  }

  window.addEventListener("hashchange", openFromHash);
  openFromHash();
}());
