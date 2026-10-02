"""Behavioral checks for the ranking model; run with unittest discovery."""
import unittest

import numpy as np
import pandas as pd

from efficiency_model import COMPONENTS, PLAY_TYPES, fit_units, prepare_plays, score_units
from update_ravens_dashboard import compute_league_metrics, PBP_COLUMNS


def fixture():
    games = pd.DataFrame([dict(game_id="g1", home_team="A", away_team="B", location="Home",
                               home_score=14, away_score=7, week=1)])
    rows = []
    for offense, defense in (("A", "B"), ("B", "A")):
        for dropback in (0, 1):
            row = dict.fromkeys(PBP_COLUMNS, 0)
            row.update(game_id="g1", season_type="REG", week=1, posteam=offense,
                       defteam=defense, play_type="pass" if dropback else "run", epa=.1,
                       success=1, qb_dropback=dropback, wp=.5, qtr=1,
                       game_seconds_remaining=3000, fixed_drive=1, yardline_100=50)
            rows.append(row)
    return pd.DataFrame(rows), games


def calibration():
    return {"phase_weights": {"dropback": .6, "designed_run": .4},
            "scales": {f"{phase}_{component}": 1 for phase in PLAY_TYPES for component in COMPONENTS}}


class ModelTests(unittest.TestCase):
    def test_late_weight_is_symmetric_and_excludes_early_and_overtime(self):
        rows, games = fixture()
        sample = pd.concat([rows] * 7, ignore_index=True)
        sample["qtr"] = np.repeat([4, 4, 4, 4, 4, 1, 5], 4)
        sample["wp"] = np.repeat([.01, .10, .5, .90, .99, .99, .99], 4)
        sample["game_seconds_remaining"] = 300
        result = prepare_plays(sample, games)
        np.testing.assert_allclose(result.weight.to_numpy()[::4], [.25, .625, 1, .625, .25, 1, 1])

    def test_sacks_scrambles_and_neutral_venues(self):
        rows, games = fixture()
        rows.loc[0, ["play_type", "qb_dropback", "sack"]] = ["pass", 1, 1]
        rows.loc[1, ["play_type", "qb_dropback"]] = ["run", 1]
        games["location"] = "Neutral"
        result = prepare_plays(rows, games)
        self.assertEqual(result.phase.iloc[:2].tolist(), ["dropback", "dropback"])
        self.assertTrue((result.venue == 0).all())
        games["location"] = "Home"
        self.assertEqual(prepare_plays(rows, games).venue.tolist(), [1, 1, -1, -1])

    def test_missing_game_or_unknown_state_fails_closed(self):
        rows, games = fixture()
        with self.assertRaisesRegex(ValueError, "Missing eligible"):
            prepare_plays(rows.iloc[:2], games)
        rows.loc[0, "wp"] = np.nan
        with self.assertRaisesRegex(ValueError, "Missing/non-finite"):
            prepare_plays(rows, games)

    def test_adjustment_recovers_stronger_offense_despite_harder_schedule(self):
        attack = {"A": .25, "B": .1, "C": 0, "D": 0}
        defense = {"A": 0, "B": 0, "C": .8, "D": -.8}
        rows = []
        for home in attack:
            for away in attack:
                if home == away:
                    continue
                repeats = 5 if (home, away) in [("A", "C"), ("B", "D")] else 1
                for phase in PLAY_TYPES:
                    for _ in range(400 * repeats):
                        rows.append(dict(posteam=home, defteam=away, phase=phase, weight=1., venue=0.,
                                         epa=attack[home] - defense[away], success=.5))
        rows = pd.DataFrame(rows)
        raw = rows.groupby("posteam").epa.mean()
        self.assertLess(raw["A"], raw["B"])
        fitted = fit_units(rows)
        self.assertGreater(fitted.loc["A", "dropback_offense_epa"], fitted.loc["B", "dropback_offense_epa"])
        self.assertGreater(fitted.loc["C", "dropback_defense_epa"], fitted.loc["D", "dropback_defense_epa"])
        pd.testing.assert_frame_equal(fitted, fit_units(rows.sample(frac=1, random_state=4)))

    def test_score_preserves_magnitude_and_uses_fixed_mix(self):
        cal = calibration()
        fitted = pd.DataFrame(0., index=["A", "B"], columns=list(cal["scales"]))
        self.assertTrue((score_units(fitted, cal).overall_efficiency == 50).all())
        fitted.loc["A", "dropback_offense_epa"] = 2
        first = score_units(fitted, cal)
        self.assertAlmostEqual(first.loc["A", "composite"], .3)
        fitted.loc["A", "dropback_offense_epa"] = 4
        second = score_units(fitted, cal)
        self.assertGreater(second.loc["A", "overall_efficiency"], first.loc["A", "overall_efficiency"])
        self.assertEqual(second.loc["B", "overall_efficiency"], 50)

    def test_future_games_cannot_change_historical_cutoff(self):
        rows, games = fixture()
        later = rows.copy()
        later["game_id"] = "future"
        later["epa"] = 10
        _, original = compute_league_metrics(games, rows, calibration())
        _, with_future = compute_league_metrics(games, pd.concat([rows, later]), calibration())
        pd.testing.assert_frame_equal(original, with_future)


if __name__ == "__main__":
    unittest.main()
