"""Special-teams value above prior-season context expectations, in points/game."""
import numpy as np
import pandas as pd

KINDS = ("field_goal", "extra_point", "punt", "kickoff")
EXTRA_COLUMNS = ["ep", "kick_distance", "half_seconds_remaining", "field_goal_result",
                 "extra_point_result", "blocked_player_id"] + [f"{kind}_attempt" for kind in KINDS]
SHRINK_GAMES = 2.0
BUCKET_WIDTHS = {"field_goal": 5, "extra_point": 5, "punt": 10, "kickoff": 5}
BANDWIDTHS = {"field_goal": 5, "extra_point": 5, "punt": 10, "kickoff": 5}


def prepare_special_teams(pbp, games):
    rows = pbp[(pbp.season_type == "REG") & pbp.game_id.isin(games.game_id)
               & pbp.play_type.isin(KINDS) & (pbp.play_deleted.fillna(0) != 1)
               & (pbp.two_point_attempt.fillna(0) != 1)].copy()
    # A kick-labelled penalty row can be nullified without play_deleted == 1.
    # Require the matching live-attempt flag to avoid counting the retry twice.
    live = pd.Series(False, index=rows.index)
    for kind in KINDS:
        live |= (rows.play_type == kind) & (rows[f"{kind}_attempt"].fillna(0) == 1)
    rows = rows[live].copy()
    if set(games.game_id) - set(rows.game_id):
        raise ValueError("Missing special-teams game coverage")
    if not np.isfinite(rows[["ep", "epa", "yardline_100", "half_seconds_remaining"]]
                       .to_numpy(dtype=float)).all():
        raise ValueError("Missing/non-finite special-teams context or outcome")
    scoring_kicks = rows.play_type.isin(["field_goal", "extra_point"])
    if not np.isfinite(rows.loc[scoring_kicks, "kick_distance"].to_numpy(dtype=float)).all():
        raise ValueError("Missing scoring-kick distance")
    rows["context_distance"] = np.where(scoring_kicks, rows.kick_distance, rows.yardline_100)
    if not rows.context_distance.between(0, 100).all():
        raise ValueError("Invalid special-teams distance")
    rows["clock_bucket"] = np.select([rows.half_seconds_remaining <= 60,
                                      rows.half_seconds_remaining <= 180], [0, 1], default=2)
    rows["distance_bucket"] = (rows.context_distance / rows.play_type.map(BUCKET_WIDTHS)).astype(int)
    # EPA alone contains the value inherited from the offense's previous plays.
    # Compare the resulting value, ep + epa, against equivalent kick situations.
    rows["result_value"] = rows.ep + rows.epa
    expected_teams = {r.game_id: {r.home_team, r.away_team} for r in games.itertuples()}
    if any({r.posteam, r.defteam} != expected_teams[r.game_id] for r in rows.itertuples()):
        raise ValueError("Special-teams possession does not match schedule")
    return rows


def expected_values(rows, baseline):
    return pd.Series([baseline["lookup"][r.play_type][f"{r.clock_bucket}:{r.distance_bucket}"]
                      + baseline["offsets"][r.play_type] for r in rows.itertuples()], index=rows.index)


def make_baseline(rows):
    """Smooth prior-season resulting point value by distance and half clock.

    Scoring kicks use attempt distance; punts/kickoffs use pre-kick field position,
    never realized kick/return distance. Sparse clock buckets fall back to the type.
    """
    baseline = {"lookup": {}, "offsets": {kind: 0.0 for kind in KINDS}}
    for kind in KINDS:
        sample = rows[rows.play_type == kind]
        if sample.empty:
            raise ValueError(f"No prior-season {kind} calibration plays")
        lookup = {}
        width = BUCKET_WIDTHS[kind]
        for clock in range(3):
            subset = sample[sample.clock_bucket == clock]
            if len(subset) < 10:
                subset = sample
            for bucket in range(100 // width + 1):
                center = min(100, width * (bucket + .5))
                weights = np.exp(-.5 * ((subset.context_distance - center) / BANDWIDTHS[kind]) ** 2)
                lookup[f"{clock}:{bucket}"] = float(np.average(subset.result_value, weights=weights))
        baseline["lookup"][kind] = lookup
    residuals = rows.result_value - expected_values(rows, baseline)
    baseline["offsets"] = {kind: float(residuals[rows.play_type == kind].mean()) for kind in KINDS}
    return baseline


def team_values(rows, games, baseline):
    rows = rows.copy()
    rows["residual"] = rows.result_value - expected_values(rows, baseline)
    game_counts = pd.concat([games.home_team, games.away_team]).value_counts().sort_index()
    table = pd.DataFrame(index=game_counts.index)
    table["special_teams_games"] = game_counts
    for kind in KINDS:
        sample = rows[rows.play_type == kind]
        credits = [pd.DataFrame({"team": sample.posteam, "value": sample.residual})]
        # nflverse posteam is the receiving team on kickoffs, and the punting
        # team on punts. Credit the other team with the opposite value once.
        # Scoring-kick misses are not automatically credited to the opponent.
        if kind in ("punt", "kickoff"):
            counterpart = sample
        else:
            blocked = (sample.field_goal_result == "blocked") | sample.blocked_player_id.notna()
            returned = sample.td_team.notna() & (sample.td_team == sample.defteam)
            counterpart = sample[blocked | returned]
        credits.append(pd.DataFrame({"team": counterpart.defteam, "value": -counterpart.residual}))
        totals = pd.concat(credits).groupby("team").value.sum()
        table[f"special_teams_{kind}_points"] = totals.reindex(table.index, fill_value=0)
    point_columns = [f"special_teams_{kind}_points" for kind in KINDS]
    table["special_teams_total_points"] = table[point_columns].sum(axis=1)
    table["special_teams_points_per_game"] = table.special_teams_total_points / game_counts
    table["special_teams_adjusted_points_per_game"] = table.special_teams_total_points / (game_counts + SHRINK_GAMES)
    return table


def make_special_teams_calibration(pbp, games):
    rows = prepare_special_teams(pbp, games)
    baseline = make_baseline(rows)
    units = team_values(rows, games, baseline).special_teams_adjusted_points_per_game
    scale = float(units.std(ddof=0))
    if not np.isfinite(scale) or scale <= 1e-8:
        raise ValueError("Insufficient special-teams calibration variation")
    return {"baseline": baseline, "mean": float(units.mean()), "scale": scale}


def fit_special_teams(pbp, games, calibration):
    rows = prepare_special_teams(pbp, games)
    return team_values(rows, games, calibration["baseline"])
