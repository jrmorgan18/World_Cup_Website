(function () {
  "use strict";

  var board = document.querySelector("[data-big-board]");
  if (!board) return;

  var source = board.getAttribute("data-source");
  var body = board.querySelector("[data-board-body]");
  var resultText = board.querySelector("[data-board-results]");
  var snapshot = board.querySelector("[data-board-snapshot]");
  var search = board.querySelector("[data-board-search]");
  var positionFilter = board.querySelector("[data-board-position]");
  var leagueFilter = board.querySelector("[data-board-league]");
  var groupFilter = board.querySelector("[data-board-group]");
  var sortButtons = Array.prototype.slice.call(board.querySelectorAll("[data-board-sort]"));
  var sortKey = "current_score";
  var sortDirection = "desc";
  var players = [];

  function text(value) {
    return value === null || value === undefined || value === "" ? "—" : String(value);
  }

  function score(value) {
    return value === null || value === undefined ? "—" : Number(value).toFixed(1);
  }

  function addOptions(select, values) {
    values.forEach(function (value) {
      var option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
  }

  function populatedValues(key) {
    return players
      .map(function (player) { return player[key]; })
      .filter(Boolean)
      .filter(function (value, index, values) { return values.indexOf(value) === index; })
      .sort(function (a, b) { return a.localeCompare(b); });
  }

  function matchesFilters(player) {
    var query = search.value.trim().toLowerCase();
    var haystack = [player.name, player.club, player.league, player.position, player.group].join(" ").toLowerCase();
    return (!query || haystack.indexOf(query) !== -1) &&
      (!positionFilter.value || player.position === positionFilter.value) &&
      (!leagueFilter.value || player.league === leagueFilter.value) &&
      (!groupFilter.value || player.group === groupFilter.value);
  }

  function compare(a, b) {
    var first = a[sortKey];
    var second = b[sortKey];
    var firstMissing = first === null || first === undefined;
    var secondMissing = second === null || second === undefined;
    if (firstMissing || secondMissing) {
      if (firstMissing && secondMissing) return (a.rank || 999) - (b.rank || 999);
      return firstMissing ? 1 : -1;
    }
    var difference = typeof first === "number" ? first - second : String(first).localeCompare(String(second));
    if (difference === 0) return (a.rank || 999) - (b.rank || 999);
    return sortDirection === "asc" ? difference : -difference;
  }

  function cell(row, value, className) {
    var td = document.createElement("td");
    if (className) td.className = className;
    td.textContent = value;
    row.appendChild(td);
  }

  function render() {
    var visible = players.filter(matchesFilters).sort(compare);
    body.textContent = "";
    visible.forEach(function (player) {
      var row = document.createElement("tr");
      cell(row, text(player.rank), "big-board-rank");
      cell(row, text(player.name), "big-board-player");
      cell(row, text(player.position));
      cell(row, score(player.current_score), "big-board-score");
      cell(row, score(player.score_2030), "big-board-score big-board-score--projection");
      cell(row, text(player.age_2030));
      cell(row, text(player.club));
      cell(row, text(player.league));
      body.appendChild(row);
    });
    resultText.textContent = visible.length === players.length
      ? players.length + " players in the current pool"
      : visible.length + " of " + players.length + " players";
  }

  function updateSortButtons() {
    sortButtons.forEach(function (button) {
      var isActive = button.getAttribute("data-board-sort") === sortKey;
      var column = button.parentElement;
      var icon = button.querySelector("span");
      column.setAttribute("aria-sort", isActive ? (sortDirection === "asc" ? "ascending" : "descending") : "none");
      icon.textContent = isActive ? (sortDirection === "asc" ? "↑" : "↓") : "↕";
    });
  }

  function handleSort(event) {
    var requestedKey = event.currentTarget.getAttribute("data-board-sort");
    if (requestedKey === sortKey) {
      sortDirection = sortDirection === "asc" ? "desc" : "asc";
    } else {
      sortKey = requestedKey;
      sortDirection = requestedKey === "age_2030" ? "asc" : "desc";
    }
    updateSortButtons();
    render();
  }

  [search, positionFilter, leagueFilter, groupFilter].forEach(function (control) {
    control.addEventListener(control === search ? "input" : "change", render);
  });
  sortButtons.forEach(function (button) { button.addEventListener("click", handleSort); });

  fetch(source)
    .then(function (response) {
      if (!response.ok) throw new Error("The Big Board data could not be loaded.");
      return response.json();
    })
    .then(function (data) {
      players = data.players || [];
      addOptions(positionFilter, populatedValues("position"));
      addOptions(leagueFilter, populatedValues("league"));
      addOptions(groupFilter, populatedValues("group"));
      snapshot.textContent = data.snapshot_through ? "Snapshot through " + data.snapshot_through : "Current snapshot";
      updateSortButtons();
      render();
    })
    .catch(function () {
      resultText.textContent = "The Big Board is temporarily unavailable. Please try again shortly.";
      snapshot.textContent = "Data unavailable";
    });
}());
