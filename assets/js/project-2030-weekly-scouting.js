(function () {
  "use strict";

  var table = document.querySelector("[data-weekly-scouting-board]");
  if (!table) return;

  var source = table.getAttribute("data-source");
  var body = table.querySelector("[data-weekly-scouting-body]");
  var rows = Array.prototype.slice.call(body.querySelectorAll("[data-profile]"));

  fetch(source)
    .then(function (response) {
      if (!response.ok) throw new Error("The Big Board data could not be loaded.");
      return response.json();
    })
    .then(function (data) {
      var boardPlayers = {};

      (data.players || []).forEach(function (player) {
        boardPlayers[player.profile] = player;
      });

      rows.forEach(function (row, index) {
        var player = boardPlayers[row.getAttribute("data-profile")];
        var score = player && player.score_2030;
        var scoreOutput = row.querySelector("[data-weekly-scouting-score]");

        row._weeklyScoutingIndex = index;
        row._weeklyScoutingRank = player && player.rank ? player.rank : 999;
        row._weeklyScoutingScore = score === null || score === undefined ? null : Number(score);
        scoreOutput.textContent = row._weeklyScoutingScore === null ? "\u2014" : row._weeklyScoutingScore.toFixed(1);
      });

      rows.sort(function (first, second) {
        if (first._weeklyScoutingScore === null || second._weeklyScoutingScore === null) {
          if (first._weeklyScoutingScore === null && second._weeklyScoutingScore === null) {
            return first._weeklyScoutingIndex - second._weeklyScoutingIndex;
          }
          return first._weeklyScoutingScore === null ? 1 : -1;
        }

        if (first._weeklyScoutingScore !== second._weeklyScoutingScore) {
          return second._weeklyScoutingScore - first._weeklyScoutingScore;
        }

        return first._weeklyScoutingRank - second._weeklyScoutingRank;
      });

      rows.forEach(function (row) { body.appendChild(row); });
      table.setAttribute("data-score-order", "ready");
    })
    .catch(function () {
      table.setAttribute("data-score-order", "unavailable");
    });
}());
