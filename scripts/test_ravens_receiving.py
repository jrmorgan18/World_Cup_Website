"""Guard the optional public WR feed, qualification, ranking, and stale fallback."""
import unittest
from ravens_receiving import TEAMS, parse_receivers, profile_team, refresh_yprr, yprr_metric


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

    def test_missing_team_can_be_ranked_when_qualification_is_certain(self):
        self.counts["CAR"] = 4
        page = fixture([("No team", "FA", 100, 500)])
        metric = yprr_metric(page, 2026, self.counts)
        self.assertEqual(metric["rank"], 2)
        page = fixture([("No team", "FA", 39, 390)])
        self.assertEqual(yprr_metric(page, 2026, self.counts)["rank"], 1)

    def test_missing_team_between_bye_thresholds_keeps_last_good_metric(self):
        self.counts["CAR"] = 4
        previous = yprr_metric(fixture(), 2026, self.counts)
        existing = {"unit_analytics": {"Wide receivers": [previous]}}
        page = fixture([("No team", "FA", 45, 450)])
        with self.assertRaisesRegex(ValueError, "ambiguous route qualification"):
            yprr_metric(page, 2026, self.counts)
        self.assertEqual(refresh_yprr(existing, 2026, self.counts, fetch=lambda: page), previous)

    def test_missing_badge_uses_verified_profile_before_qualification(self):
        self.counts["CAR"] = 4
        page = fixture([("No team", "FA", 45, 450)])
        metric = yprr_metric(page, 2026, self.counts, team_resolver=lambda player, season: "CAR")
        self.assertEqual(metric["rank"], 2)
        metric = yprr_metric(page, 2026, self.counts, team_resolver=lambda player, season: "ATL")
        self.assertEqual(metric["rank"], 1)

    def test_profile_requires_identity_season_and_matching_totals(self):
        player = {"name": "Jared Wayne", "routes": 73, "yards": 65}
        profile = ('<h1>JARED WAYNE</h1><table><tr><th>SEASON</th><th>TEAM</th>'
                   '<th>ROUTES RUN</th><th>REC. YARDS</th></tr><tr><td>2026</td>'
                   '<td><img src="https://cdn.sumersports.com/assets/pro/logos/transparent/MIA.svg"></td>'
                   '<td>73</td><td>65</td></tr></table>')
        self.assertEqual(profile_team(profile, player, 2026), "MIA")
        for invalid in [profile.replace('JARED WAYNE', 'OTHER PLAYER'),
                        profile.replace('<td>2026</td>', '<td>2025</td>'),
                        profile.replace('<td>73</td>', '<td>72</td>'),
                        profile.replace('<td>65</td>', '<td>66</td>')]:
            with self.assertRaises(ValueError):
                profile_team(invalid, player, 2026)

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
