"""Offline regression tests for the optional Filmstudy scoring feed."""
import unittest
from datetime import date
from unittest.mock import patch

import update_ravens_dashboard as dashboard


def report(week, snaps=50, points=40, grade="B-"):
    content = "".join(
        f"<p><strong>{name}</strong>: Player notes.</p>"
        f"<p>Scoring: {snaps} plays, 45 blocks, {points} points (.80 per play). "
        f"That’s a <b>{grade}</b> after adjustment.</p>"
        for name in ("Stanley", "Simpson", "Gwyn", "Ioane", "Rosengarten")
    )
    return {"slug": f"offensiveline-notes-2026-w{week}", "date": "2026-09-22T13:00:00",
            "link": f"https://www.filmstudybaltimore.com/offensiveline-notes-2026-w{week}/",
            "content": {"rendered": content}}


class FilmstudyTests(unittest.TestCase):
    def aggregate(self, posts):
        return dashboard.aggregate_filmstudy(posts, 2026, 4, date(2026, 10, 5))

    def test_weighted_letter_grades_use_scored_snaps(self):
        result = self.aggregate([report(2, 20, 10), report(1, 80, 80, "A")])
        self.assertEqual(result["week"], 2)
        for row in result["players"]:
            self.assertEqual(row["aggregate_grade"], "A-")
            self.assertEqual(row["graded_snaps"], 100)
            self.assertEqual(row["latest_grade"], "B-")
            self.assertEqual(row["rank"], 1)

    def test_nested_tags_and_replacement_apostrophe(self):
        post = report(1)
        post["content"]["rendered"] = post["content"]["rendered"].replace("That’s", "That\ufffds")
        result = self.aggregate([post])
        self.assertTrue(all(row["latest_grade"] == "B-" for row in result["players"]))

    def test_grade_scale_rounds_to_nearest_letter(self):
        self.assertEqual(dashboard.filmstudy_letter_grade(3.84), "A")
        self.assertEqual(dashboard.filmstudy_letter_grade(2.50), "B-")

    def test_small_samples_stay_unranked(self):
        post = report(1)
        post["content"]["rendered"] += (
            "<p><u>Vinson</u>: Notes.</p>"
            "<p>Scoring: 12 plays, 9 blocks, 5.5 points (.46 per play).</p>"
        )
        result = self.aggregate([post])
        self.assertEqual(len(result["players"]), 5)
        self.assertEqual(result["unranked_players"], [{"player": "Carson Vinson", "snaps": 12}])

    def test_missing_week_fails_closed(self):
        with self.assertRaises(ValueError):
            self.aggregate([report(1), report(3)])

    def test_malformed_scoring_is_not_silently_skipped(self):
        post = report(1)
        post["content"]["rendered"] = post["content"]["rendered"].replace("40 points", "unknown points", 1)
        with self.assertRaises(ValueError):
            self.aggregate([post])

    def test_wrong_season_future_week_and_future_publication_are_ignored(self):
        old = report(2)
        old["slug"] = "offensiveline-notes-2025-w2"
        future = report(2)
        future["date"] = "2026-10-06T12:00:00"
        result = self.aggregate([report(1), old, report(5), future])
        self.assertEqual(result["week"], 1)

    def test_network_failure_and_feed_regression_preserve_last_good(self):
        stored = self.aggregate([report(1), report(2)])
        existing = {"offensive_line_filmstudy": stored}
        with patch.object(dashboard, "fetch_filmstudy", side_effect=OSError("offline")):
            self.assertEqual(dashboard.refresh_filmstudy(existing, 2026, 4, date(2026, 10, 5)), stored)
        with patch.object(dashboard, "fetch_filmstudy", return_value=self.aggregate([report(1)])):
            self.assertEqual(dashboard.refresh_filmstudy(existing, 2026, 4, date(2026, 10, 5)), stored)

    def test_prior_season_is_not_retained_on_failure(self):
        with patch.object(dashboard, "fetch_filmstudy", side_effect=OSError("offline")):
            self.assertIsNone(dashboard.refresh_filmstudy(
                {"offensive_line_filmstudy": {"season": 2025}}, 2026, 4, date(2026, 10, 5)))


if __name__ == "__main__":
    unittest.main()
