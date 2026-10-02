"""Walk forward through historical seasons without using future games in fits.

This is a diagnostic, not a parameter tuner or a proof of predictive superiority.
Compare each rating with raw net EPA/play and scoring margin in the next four
scheduled weeks. Cache public input files locally for reproducible reruns.
"""
import argparse
import json
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd

from efficiency_model import make_calibration, prepare_plays, VERSION
from update_ravens_dashboard import (
    PBP_COLUMNS, PBP_URL, SCHEDULE_URL, completed_games, compute_league_metrics,
    eligible_scrimmage_plays, team_records,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", nargs="+", type=int, default=[2024, 2025])
    parser.add_argument("--cache-dir", type=Path, default=Path(tempfile.gettempdir()) / "dual-eights-model-data")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    schedule_file = args.cache_dir / "games.csv"
    if not schedule_file.exists():
        pd.read_csv(SCHEDULE_URL).to_csv(schedule_file, index=False)
    schedule = pd.read_csv(schedule_file)
    frames = {}
    for season in sorted(set(args.seasons) | {s - 1 for s in args.seasons}):
        path = args.cache_dir / f"pbp-{season}.parquet"
        if not path.exists():
            pd.read_parquet(PBP_URL.format(season=season), columns=PBP_COLUMNS).to_parquet(path)
        frames[season] = pd.read_parquet(path, columns=PBP_COLUMNS)
    folds = []
    for season in args.seasons:
        games = completed_games(schedule, season, date(season + 1, 3, 1))
        prior = completed_games(schedule, season - 1, date(season, 3, 1))
        prior_rows = prepare_plays(eligible_scrimmage_plays(frames[season-1], set(prior.game_id)), prior)
        calibration = make_calibration(prior_rows, season - 1)
        for cutoff in (3, 6, 9, 12):
            train = games[games.week <= cutoff]
            future = games[(games.week > cutoff) & (games.week <= cutoff + 4)]
            _, ratings = compute_league_metrics(train, frames[season], calibration)
            plays = eligible_scrimmage_plays(frames[season], set(future.game_id))
            net_epa = plays.groupby("posteam").epa.mean() - plays.groupby("defteam").epa.mean()
            records = team_records(future)
            margin = records.point_differential / records[["wins", "losses", "ties"]].sum(axis=1)
            comparisons = {}
            for name, target in (("next_four_weeks_net_epa", net_epa), ("next_four_weeks_margin", margin)):
                comparisons[name] = {
                    "v1_spearman": float(ratings.legacy_overall_efficiency.rank().corr(target.rank())),
                    "v2_spearman": float(ratings.overall_efficiency.rank().corr(target.rank())),
                }
            folds.append({"season": season, "cutoff_week": cutoff,
                          "calibration_season": season - 1, "comparisons": comparisons})
            print(f"Validated {season} through week {cutoff}", flush=True)
    means = {}
    for target in folds[0]["comparisons"]:
        means[target] = {version: sum(f["comparisons"][target][version] for f in folds) / len(folds)
                         for version in ("v1_spearman", "v2_spearman")}
    result = {"model_version": VERSION, "cutoffs": [3, 6, 9, 12],
              "evaluation": "Spearman correlation with the next four calendar weeks; higher is better.",
              "limitations": "Overlapping windows and repeated teams; descriptive diagnostic, not independent trials. No parameters selected using these results.",
              "sources": {"schedule": SCHEDULE_URL, "pbp": PBP_URL},
              "mean_correlations": means, "folds": folds}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(means, indent=2))


if __name__ == "__main__":
    main()
