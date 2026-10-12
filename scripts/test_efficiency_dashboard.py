"""Offline checks for production use of the published v2.1 model."""
import unittest
from datetime import date
from unittest.mock import patch

import numpy as np
import pandas as pd

import efficiency_dashboard as wiring
import efficiency_model as model
import special_teams as st


class EfficiencyDashboardTests(unittest.TestCase):
    def test_frozen_calibration_and_published_weights(self):
        anchors = wiring.calibration(2026)
        self.assertEqual(anchors["season"], 2025)
        self.assertAlmostEqual(sum(anchors["phase_weights"].values()), 1)
        self.assertEqual(model.VERSION, "2.1")
        self.assertAlmostEqual(sum(model.COMPONENT_WEIGHTS.values()), 1)
        self.assertEqual(model.COMPONENT_WEIGHTS["special_teams"], .10)
        self.assertTrue(all(model.COMPONENT_WEIGHTS[key] == .225 for key in model.COMPONENTS))

    def test_scoring_uses_frozen_magnitudes_and_special_teams(self):
        anchors = wiring.calibration(2026)
        fitted = pd.DataFrame({column: [scale, -scale] for column, scale in anchors["scales"].items()}, index=["BAL", "CLE"])
        specials = pd.DataFrame({"special_teams_adjusted_points_per_game": [anchors["special_teams"]["mean"] + anchors["special_teams"]["scale"], anchors["special_teams"]["mean"] - anchors["special_teams"]["scale"]]}, index=fitted.index)
        scored = model.score_units(fitted, anchors, specials)
        self.assertAlmostEqual(scored.at["BAL", "composite"], 1)
        self.assertAlmostEqual(scored.at["BAL", "overall_efficiency"], 50 + 50 * np.tanh(.5))
        self.assertAlmostEqual(scored.at["CLE", "composite"], -1)

    def test_raw_rates_are_not_replaced(self):
        table = pd.DataFrame({"overall_efficiency": [80, 20], "offensive_epa_per_play": [.2, -.1]}, index=["BAL", "CLE"])
        adjusted = pd.DataFrame({"overall_efficiency": [61.2, 44.8]}, index=table.index)
        with patch.object(model, "prepare_plays"), patch.object(model, "fit_units"), patch.object(model, "score_units", return_value=adjusted), patch.object(st, "fit_special_teams"):
            result = wiring.apply_model(table, None, pd.DataFrame({"game_id": ["game"]}), lambda *args: None, wiring.calibration(2026))
        self.assertEqual(result.offensive_epa_per_play.tolist(), [.2, -.1])
        self.assertEqual(result.overall_efficiency.tolist(), [61.2, 44.8])
        self.assertEqual(result.attrs["model_version"], "2.1")

    def test_missing_scheduled_game_fails_closed(self):
        games = pd.DataFrame({"game_id": ["2026_05_BAL_ATL"], "home_team": ["ATL"], "away_team": ["BAL"]})
        with self.assertRaisesRegex(ValueError, "Missing eligible"):
            model.prepare_plays(pd.DataFrame(columns=["game_id", "posteam"]), games)

    def test_prior_v1_history_and_published_v21_snapshot(self):
        original = {"value": 71.1, "rank": 5, "source": "original"}
        earlier = {"id": "2026-week-03", "metrics": {"overall_efficiency": original.copy()}}
        latest = {"id": "2026-week-04", "metrics": {"overall_efficiency": original.copy()}}
        existing = {"snapshots": [earlier, latest]}
        published = {"season": 2026, "through_week": 4, "model_version": "2.1", "teams": [{"abbr": "BAL", "value": 60.5, "rank": 6}]}
        wiring.preserve_published_history(existing, published)
        self.assertEqual(earlier["metrics"]["overall_efficiency"], original)
        self.assertEqual(earlier["model_version"], "1")
        self.assertEqual(latest["model_version"], "2.1")
        self.assertEqual(latest["metrics"]["overall_efficiency"]["value"], 60.5)

    def test_sidebar_uses_same_live_rankings(self):
        rankings = {"teams": [{"abbr": "BAL", "rank": 6, "value": 61.2}]}
        result = wiring.sidebar_payload(rankings, 2026, 5, date(2026, 10, 12))
        self.assertEqual(result["teams"], rankings["teams"])
        self.assertEqual(result["through_week"], 5)
        self.assertEqual(result["model_version"], "2.1")


if __name__ == "__main__":
    unittest.main()
