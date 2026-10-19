"""Offline regression coverage for the Barcelona dashboard's player reconciliation."""
import unittest
from datetime import date
from unittest.mock import patch

import update_barcelona_dashboard as dashboard


def athlete(player_id="1"):
    return {
        "id": player_id, "displayName": "Test player", "position": {"abbreviation": "F"},
        # Deliberately lagging season statistics: the latest goal is absent.
        "statistics": {"splits": {"categories": [{"stats": [
            {"name": "appearances", "value": 0}, {"name": "totalGoals", "value": 0},
        ]}]}},
    }


class PlayerReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.events = [{"event_id": "test", "competition": "laliga", "date": "2026-10-17T16:30Z"}]
        self.cache = {"matches": {"test": {
            "barcelona_minutes": [{"player_id": "1", "minutes": 90, "starter": True, "played": True}],
            "barcelona_player_stats": {"1": {"goals": 1, "assists": 2}},
        }}}

    def build(self):
        with patch.object(dashboard, "fetch_json", return_value={"athletes": [athlete()]}):
            return dashboard.build_squad({"laliga": "esp.1"}, self.cache, self.events, date(2026, 10, 17))

    def test_match_totals_override_lagging_roster(self):
        result = self.build()
        totals = result["players"][0]["totals"]
        self.assertEqual((totals["appearances"], totals["starts"], totals["minutes"]), (1, 1, 90))
        self.assertEqual((totals["goals"], totals["assists"]), (1, 2))
        self.assertTrue(result["data_status"]["complete_match_box_scores"]["laliga"])

    def test_unused_substitute_is_not_an_appearance(self):
        self.cache["matches"]["test"]["barcelona_minutes"][0].update(minutes=0, starter=False, played=False)
        self.cache["matches"]["test"]["barcelona_player_stats"]["1"] = {"goals": 0, "assists": 0}
        totals = self.build()["players"][0]["totals"]
        self.assertEqual((totals["appearances"], totals["starts"], totals["minutes"]), (0, 0, 0))

    def test_missing_box_score_labels_fallback(self):
        del self.cache["matches"]["test"]["barcelona_player_stats"]
        result = self.build()
        self.assertFalse(result["data_status"]["complete_match_box_scores"]["laliga"])
        self.assertIn("pending", result["data_status"]["note"])
        self.assertEqual(result["players"][0]["totals"]["appearances"], 1)

    def test_other_competitions_stay_separate(self):
        self.events.append({"event_id": "europe", "competition": "ucl", "date": "2026-10-13T19:00Z"})
        self.cache["matches"]["europe"] = {
            "barcelona_minutes": [{"player_id": "1", "minutes": 25, "starter": False, "played": True}],
            "barcelona_player_stats": {"1": {"goals": 2, "assists": 0}},
        }
        with patch.object(dashboard, "fetch_json", return_value={"athletes": [athlete()]}):
            player = dashboard.build_squad({"laliga": "esp.1", "ucl": "uefa.champions"}, self.cache, self.events, date(2026, 10, 17))["players"][0]
        self.assertEqual(player["competitions"]["laliga"]["goals"], 1)
        self.assertEqual(player["competitions"]["ucl"]["goals"], 2)
        self.assertEqual((player["totals"]["goals"], player["totals"]["appearances"]), (3, 2))

    def test_box_score_parser_ignores_opponent(self):
        payload = {"rosters": [
            {"team": {"id": "99"}, "roster": [{"athlete": {"id": "other"}, "stats": [{"name": "totalGoals", "value": 8}]}]},
            {"team": {"id": dashboard.TEAM_ID}, "roster": [{"athlete": {"id": "1"}, "stats": [{"name": "totalGoals", "value": 1}]}]},
        ]}
        with patch.object(dashboard, "fetch_json", return_value=payload):
            self.assertEqual(dashboard.fetch_match_player_stats("esp.1", "test"), {"1": {"goals": 1}})

    def test_refresh_preserves_cached_player_data_when_minutes_fetch_fails(self):
        event = {"event_id": "test", "competition": "laliga", "date": "2026-10-17T16:30Z",
                 "home": {"team_id": dashboard.TEAM_ID, "score": 5}, "away": {"team_id": "99", "score": 2}}
        with patch.object(dashboard, "fetch_match_stats", return_value={"totalShots": 18}), patch.object(dashboard, "fetch_match_minutes", return_value=[]):
            self.assertTrue(dashboard.ensure_match_cached(self.cache, event, "esp.1", refresh=True))
        self.assertEqual(self.cache["matches"]["test"]["barcelona_minutes"][0]["minutes"], 90)
        self.assertEqual(self.cache["matches"]["test"]["barcelona_player_stats"]["1"]["goals"], 1)


if __name__ == "__main__":
    unittest.main()
