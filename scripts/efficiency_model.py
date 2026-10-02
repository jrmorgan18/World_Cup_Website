"""Dual Eights v2: opponent/venue-adjusted, game-state-weighted efficiency.

Only eligible scrimmage plays enter this module. Raw dashboard statistics are
left untouched. All constants and fitted calibration are published in the JSON.
"""

import numpy as np
import pandas as pd

VERSION = "2.0"
RIDGE_PLAYS = 100.0
PLAY_TYPES = ("dropback", "designed_run")
COMPONENTS = ("offense_epa", "offense_success", "defense_epa", "defense_success")
EXTRA_COLUMNS = ["qb_dropback", "wp", "qtr", "game_seconds_remaining"]


def prepare_plays(plays, games):
    """Fail closed on incomplete inputs; neutral venues have no home advantage."""
    if games["game_id"].duplicated().any():
        raise ValueError("Duplicate schedule game IDs")
    expected = {(r.game_id, team) for r in games.itertuples()
                for team in (r.home_team, r.away_team)}
    actual = set(zip(plays.game_id, plays.posteam))
    if expected - actual:
        raise ValueError(f"Missing eligible play-by-play for {sorted(expected - actual)}")
    columns = EXTRA_COLUMNS + ["epa", "success"]
    if not np.isfinite(plays[columns].to_numpy(dtype=float)).all():
        raise ValueError("Missing/non-finite efficiency model inputs")
    if not plays.wp.between(0, 1).all() or not plays.success.isin([0, 1]).all():
        raise ValueError("Invalid win probability or success indicator")
    if not plays.qb_dropback.isin([0, 1]).all():
        raise ValueError("Invalid dropback indicator")
    rows = plays.merge(games[["game_id", "home_team", "away_team", "location"]],
                       on="game_id", how="left", validate="many_to_one")
    if not rows.location.isin(["Home", "Neutral"]).all():
        raise ValueError("Missing/unrecognized schedule venue")
    matches = ((rows.posteam == rows.home_team) & (rows.defteam == rows.away_team)) | (
        (rows.posteam == rows.away_team) & (rows.defteam == rows.home_team))
    if not matches.all():
        raise ValueError("Play-by-play teams do not match the schedule")
    rows["venue"] = np.where(rows.location == "Neutral", 0.0,
                             np.where(rows.posteam == rows.home_team, 1.0, -1.0))
    rows["phase"] = np.where(rows.qb_dropback == 1, "dropback", "designed_run")
    # Full weight outside Q4. In Q4, smoothly taper from 1 at 15%/85%
    # pre-snap WP to 0.25 at 5%/95%; never discard a competitive comeback.
    closeness = np.minimum(rows.wp, 1 - rows.wp)
    late_weight = .25 + .75 * ((closeness - .05) / .10).clip(0, 1)
    late = (rows.qtr == 4) & rows.game_seconds_remaining.between(0, 900)
    rows["weight"] = np.where(late, late_weight, 1.0)
    return rows


def fit_units(rows):
    """Joint ridge fit: outcome = intercept + offense - defense + venue.

    Success uses a linear probability fit for relative effects, not predicted
    probabilities. Penalizing unit effects makes sparse schedules identifiable.
    The intercept is unpenalized; venue and units use the same ridge penalty.
    """
    teams = sorted(set(rows.posteam) | set(rows.defteam))
    positions = {team: i for i, team in enumerate(teams)}
    n = len(teams)
    result = pd.DataFrame(index=teams)
    context = {}
    for phase in PLAY_TYPES:
        sample = rows[rows.phase == phase].copy()
        if sample.empty:
            raise ValueError(f"No {phase} plays available")
        sample["weighted_epa"] = sample.epa * sample.weight
        sample["weighted_success"] = sample.success * sample.weight
        grouped = sample.groupby(["posteam", "defteam", "venue"], as_index=False)[
            ["weight", "weighted_epa", "weighted_success"]].sum()
        x = np.zeros((len(grouped), 2 * n + 2))
        idx = np.arange(len(grouped))
        x[:, 0] = 1
        x[idx, 1 + grouped.posteam.map(positions).to_numpy()] = 1
        x[idx, 1 + n + grouped.defteam.map(positions).to_numpy()] = -1
        x[:, -1] = grouped.venue
        penalty = np.eye(x.shape[1]) * RIDGE_PLAYS
        penalty[0, 0] = 0
        weighted_x = x * grouped.weight.to_numpy()[:, None]
        coefficients = np.linalg.solve(x.T @ weighted_x + penalty,
                                      x.T @ grouped[["weighted_epa", "weighted_success"]].to_numpy())
        for target, column in (("epa", 0), ("success", 1)):
            result[f"{phase}_offense_{target}"] = coefficients[1:1+n, column]
            result[f"{phase}_defense_{target}"] = coefficients[1+n:1+2*n, column]
        context[phase] = {
            "intercept_epa": float(coefficients[0, 0]),
            "intercept_success": float(coefficients[0, 1]),
            "venue_epa": float(coefficients[-1, 0]),
            "venue_success": float(coefficients[-1, 1]),
        }
    result.attrs["fit"] = context
    return result


def make_calibration(rows, season):
    fitted = fit_units(rows)
    scales = {column: float(fitted[column].std(ddof=0)) for column in fitted.columns}
    if any(not np.isfinite(value) or value <= 1e-8 for value in scales.values()):
        raise ValueError("Calibration lacks sufficient variation")
    counts = rows.groupby("phase").weight.sum()
    return {
        "season": int(season),
        "phase_weights": {phase: float(counts[phase] / counts.sum()) for phase in PLAY_TYPES},
        "scales": scales,
    }


def score_units(fitted, calibration):
    """Standardize magnitudes against a fixed prior-season league scale."""
    scored = fitted.copy()
    for component in COMPONENTS:
        scored[component] = sum(
            calibration["phase_weights"][phase] * fitted[f"{phase}_{component}"]
            / calibration["scales"][f"{phase}_{component}"] for phase in PLAY_TYPES)
    scored["composite"] = scored[list(COMPONENTS)].mean(axis=1)
    # A monotone display transform, not a percentile or a win probability.
    scored["overall_efficiency"] = 50 + 50 * np.tanh(scored.composite / 2)
    return scored


def model_metadata(calibration):
    return {
        "version": VERSION,
        "calibration": calibration,
        "ridge_effective_plays": RIDGE_PLAYS,
        "component_weights": {component: .25 for component in COMPONENTS},
        "game_state": {"quarter": 4, "full_weight_wp": [.15, .85],
                       "minimum_weight_wp": [.05, .95], "minimum_weight": .25},
        "display_transform": "50 + 50 * tanh(composite / 2)",
        "note": "50 is average unit strength; score is neither a percentile nor a win probability.",
    }
