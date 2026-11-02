import sys
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_ravens_dashboard as dashboard


class ScheduleOnlyPayloadTests(unittest.TestCase):
    def test_latest_full_pbp_week_stops_before_a_partial_week(self):
        games = []
        plays = []
        for week in range(1, 9):
            game_id = f"2026_{week:02d}_BAL_X{week:02d}"
            games.append({
                "game_id": game_id,
                "week": week,
                "home_team": "BAL",
                "away_team": f"X{week:02d}",
            })
            if week == 8:
                continue
            for posteam, defteam in (("BAL", f"X{week:02d}"), (f"X{week:02d}", "BAL")):
                plays.append({
                    "game_id": game_id,
                    "season_type": "REG",
                    "week": week,
                    "posteam": posteam,
                    "defteam": defteam,
                    "play_type": "run",
                    "epa": 0.1,
                    "yards_gained": 5,
                    "qb_kneel": 0,
                    "qb_spike": 0,
                    "two_point_attempt": 0,
                    "play_deleted": 0,
                    "aborted_play": 0,
                })

        self.assertEqual(
            dashboard.last_fully_covered_week(pd.DataFrame(games), pd.DataFrame(plays)),
            7,
        )

    def test_last_game_total_yards_includes_kneels_but_efficiency_excludes_them(self):
        rows = []

        def play(posteam, defteam, yards, *, kneel=0, spike=0, deleted=0, two_point=0, aborted=0, epa=0.1, success=1):
            rows.append({
                "game_id": "2026_08_BAL_BUF",
                "season_type": "REG",
                "week": 8,
                "posteam": posteam,
                "defteam": defteam,
                "play_type": "run",
                "epa": epa,
                "success": success,
                "yards_gained": yards,
                "interception": 0,
                "fumble_lost": 0,
                "qb_kneel": kneel,
                "qb_spike": spike,
                "two_point_attempt": two_point,
                "play_deleted": deleted,
                "aborted_play": aborted,
            })

        play("BAL", "BUF", 6)
        play("BAL", "BUF", -1, kneel=1, epa=99, success=1)
        play("BAL", "BUF", 0, spike=1, epa=99, success=1)
        play("BAL", "BUF", 100, deleted=1, epa=99, success=1)
        play("BAL", "BUF", 2, two_point=1, epa=99, success=1)
        play("BAL", "BUF", 99, aborted=1, epa=99, success=1)
        play("BUF", "BAL", 9, epa=-0.2, success=0)
        play("BUF", "BAL", 0, spike=1, epa=99, success=1)

        result = dashboard.last_game_payload(
            [{
                "game_id": "2026_08_BAL_BUF",
                "week": "Week 8",
                "date": "2026-11-01",
                "location": "away",
                "opponent": "Buffalo Bills",
                "result": "L",
                "ravens_score": 10,
                "opponent_score": 36,
            }],
            pd.DataFrame(rows),
        )
        stats = {item["label"]: item["value"] for item in result["key_stats"]}

        self.assertEqual(stats["Scrimmage yards"], "5–9")
        self.assertEqual(stats["EPA / play"], "0.10 / -0.20")
        self.assertEqual(stats["Success rate"], "100.0% / 0.0%")

    def test_updates_postgame_fields_and_preserves_published_metrics(self):
        games = []
        outcomes = ["W", "L", "W", "W", "L", "W", "L", "L"]
        for week, outcome in enumerate(outcomes, start=1):
            ravens_score, opponent_score = (24, 17) if outcome == "W" else (17, 24)
            games.append({
                "game_id": f"2026_{week:02d}_BAL_X{week:02d}",
                "week": week,
                "gameday": f"2026-09-{week + 1:02d}",
                "home_team": "BAL",
                "away_team": f"X{week:02d}",
                "home_score": ravens_score,
                "away_score": opponent_score,
            })
        current_games = pd.DataFrame(games)
        recent_games = [
            {
                "game_id": games[-1]["game_id"],
                "week": "Week 8",
                "date": "2026-11-01",
                "location": "away",
                "opponent": "Buffalo Bills",
                "result": "L",
                "ravens_score": 10,
                "opponent_score": 36,
                "takeaway": "The Ravens lost to the Buffalo Bills 10–36.",
            }
        ]
        next_game = {
            "week": 9,
            "opponent": "Jacksonville Jaguars",
            "opponent_abbr": "JAX",
            "date": "2026-11-05",
            "display": "vs. Jacksonville Jaguars · Nov 5 · 8:15 PM ET",
            "matchup": {"label": "2026 through Week 7 · Week 8 update pending", "items": []},
        }
        last_game = {
            **recent_games[0],
            "type_label": "Regular season",
            "source": "nflverse play-by-play",
            "key_stats": [{"label": "Scrimmage yards", "value": "144–426"}],
        }
        existing = {
            "season": 2026,
            "benchmark_season": 2025,
            "current_snapshot": "2026-week-07",
            "snapshots": [{"id": "2026-week-07", "week": 7, "label": "Through available Week 7 games", "sample_note": "7 regular-season games", "metrics": {"overall_efficiency": {"value": 44.0, "rank": 20}}}],
            "league_efficiency_rankings": {"label": "Prior published rankings", "teams": [{"abbr": "BAL", "rank": 20}]},
            "unit_analytics": {"Quarterback": [{"label": "Jackson QBR", "period_label": "Through Week 7"}]},
            "header": {"record": "4-3", "streak": "L2", "next_game": {"opponent_abbr": "BUF"}},
            "last_game": {"game_id": "week7"},
            "recent_games": [{"game_id": "week7"}],
            "recent_form": {"sequence": ["L", "L", "W", "W", "W"], "record": "3-2", "point_differential": 10},
        }
        args = SimpleNamespace(season=2026, as_of=date(2026, 11, 1))

        updated = dashboard.schedule_only_payload(
            existing, current_games, recent_games, next_game, last_game, args
        )

        self.assertEqual(updated["header"]["record"], "4-4")
        self.assertEqual(updated["header"]["division_standing"], "AFC North")
        self.assertEqual(updated["header"]["streak"], "L1")
        self.assertEqual(updated["header"]["next_game"]["opponent_abbr"], "JAX")
        self.assertIn("2026 through Week 7", updated["header"]["next_game"]["matchup"]["label"])
        self.assertEqual(updated["last_game"]["key_stats"][0]["value"], "144–426")
        self.assertEqual(updated["recent_games"][0]["game_id"], recent_games[0]["game_id"])
        self.assertEqual(updated["schedule_update"]["period_label"], "Week 8 final · 2026-11-01")
        self.assertEqual(updated["schedule_update"]["metrics_period"], "Through available Week 7 games (7 regular-season games)")
        self.assertEqual(updated["snapshots"], existing["snapshots"])
        self.assertEqual(updated["league_efficiency_rankings"], existing["league_efficiency_rankings"])
        self.assertEqual(updated["unit_analytics"], existing["unit_analytics"])


if __name__ == "__main__":
    unittest.main()
