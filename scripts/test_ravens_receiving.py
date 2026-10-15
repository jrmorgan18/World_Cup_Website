"""Guard the optional public WR feed, qualification, ranking, and stale fallback."""
import unittest
from ravens_receiving import TEAMS, parse_receivers, refresh_yprr, yprr_metric


def fixture(extra=(), routes=91, season=2026, stamp="2026-10-15T08:36:41Z"):
    headers = ["Player", "Routes Run", "Rec. Yards", "YPRR"]
    players = [(f"Receiver {team}", team, 100, 100) for team in sorted(TEAMS)]
    players += [("Zay Flowers", "BLT", routes, 405), *extra]
    rows = []
    for name, team, count, yards in players:
        rows.append(f'<tr><td><span>{team}</span><span class="hidden md:inline truncate">{name}</span>'
                    f'<span class="inline md:hidden">Short name</span></td><td>{count}</td>'
                    f'<td>{yards:,}</td><td>{yards / count:.2f}</td></tr>')
    return (f'<button>{season} Season</button><time datetime="{stamp}">Updated</time><table><thead><tr>'
            + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>")


class ReceiverFeedTests(unittest.TestCase):
    def setUp(self):
        self.counts = {t: 5 for t in TEAMS}

    def test_uniform_team_game_threshold_includes_bye_teams(self):
        self.counts["CAR"] = 4
        metric = yprr_metric(fixture([("Bye player", "CAR", 40, 200),
                                     ("Small sample", "ATL", 49, 490),
                                     ("Tie player", "SEA", 182, 810)]), 2026, self.counts)
        self.assertEqual((metric["value"], metric["routes"], metric["rank"], metric["minimum_routes"]), ("4.45", 91, 2, 50))
        self.assertEqual(metric["receiving_yards"], 405)

    def test_ranks_exact_ratios_instead_of_rounded_display(self):
        metric = yprr_metric(fixture([("Narrow lead", "SEA", 1000, 4451)]), 2026, self.counts)
        self.assertEqual(metric["rank"], 2)

    def test_wrong_season_and_incomplete_league_fail_closed(self):
        with self.assertRaises(ValueError):
            parse_receivers(fixture(season=2025), 2026)
        with self.assertRaises(ValueError):
            parse_receivers(fixture().replace("<span>SEA</span>", "<span>BAL</span>"), 2026)

    def test_failed_fetch_preserves_exact_dated_metric(self):
        previous = yprr_metric(fixture(), 2026, self.counts)
        existing = {"unit_analytics": {"Wide receivers": [previous]}}
        def fail():
            raise OSError("temporary outage")
        self.assertEqual(refresh_yprr(existing, 2026, self.counts, fetch=fail), previous)

    def test_old_source_cannot_replace_newer_metric(self):
        previous = yprr_metric(fixture(), 2026, self.counts)
        existing = {"unit_analytics": {"Wide receivers": [previous]}}
        metric = refresh_yprr(existing, 2026, self.counts, fetch=lambda: fixture(stamp="2026-10-14T08:00:00Z"))
        self.assertEqual(metric, previous)

    def test_unqualified_current_player_does_not_keep_old_rank(self):
        previous = yprr_metric(fixture(), 2026, self.counts)
        existing = {"unit_analytics": {"Wide receivers": [previous]}}
        self.assertIsNone(refresh_yprr(existing, 2026, self.counts, fetch=lambda: fixture(routes=49)))

    def test_invalid_rate_and_future_timestamp_are_rejected(self):
        for page in [fixture().replace("4.45</td>", "9.99</td>"), fixture(stamp="2099-01-01T00:00:00Z")]:
            with self.assertRaises(ValueError):
                yprr_metric(page, 2026, self.counts)


if __name__ == "__main__":
    unittest.main()
