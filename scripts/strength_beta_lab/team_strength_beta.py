"""Independent, local-only Dual Eights Power Index beta.

Run fetch_strength_beta_inputs.py first. Never writes dashboard or post files.
All historical forecast features are cut off before the games being forecast.
"""
import argparse
import hashlib
import itertools
import json
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .efficiency_model import prepare_plays
from .special_teams import expected_values, make_baseline, prepare_special_teams
from .legacy_inputs import TEAM_NAMES, eligible_scrimmage_plays

VERSION = "0.1-beta"
TEAMS = sorted(TEAM_NAMES)
ALIASES = {"OAK": "LV", "SD": "LAC", "STL": "LA", "JAC": "JAX", "LAR": "LA"}
FEATURES = ["pass_offense", "pass_defense", "run_offense", "run_defense", "st", "qb_epa_delta", "qb_cpoe_delta"]
OFFSEASON_CARRY = .75
ST_CARRY = .35
ST_PRIOR_GAMES = 8.0
QB_PRIOR_PLAYS = 200.0
QB_YEAR_CARRY = .55


@dataclass(frozen=True)
class Settings:
    ridge_plays: float
    half_life_weeks: float

    @property
    def label(self):
        return f"{self.ridge_plays:g} prior plays / {self.half_life_weeks:g}-week half-life"


def normalize(frame, columns):
    frame = frame.copy()
    for column in columns:
        frame[column] = frame[column].replace(ALIASES)
    return frame


def decay(weeks, cutoff, half_life):
    if np.any(np.asarray(weeks) > cutoff):
        raise ValueError("Future weeks reached recency weighting")
    return np.power(.5, (cutoff - np.asarray(weeks, dtype=float)) / half_life)


def fit_phase(rows, phase, cutoff, settings, prior):
    sample = rows[(rows.phase == phase) & (rows.week <= cutoff)].copy()
    if sample.empty:
        return prior * OFFSEASON_CARRY, {"intercept": 0., "venue": 0.}, np.zeros(32)
    sample["w"] = sample.weight * decay(sample.week, cutoff, settings.half_life_weeks)
    sample["wy"] = sample.w * sample.epa
    grouped = sample.groupby(["posteam", "defteam", "venue"], as_index=False)[["w", "wy"]].sum()
    indexes = {team: i for i, team in enumerate(TEAMS)}
    x = np.zeros((len(grouped), 66))
    ix = np.arange(len(grouped))
    x[:, 0] = 1.
    x[ix, 1 + grouped.posteam.map(indexes).to_numpy()] = 1.
    x[ix, 33 + grouped.defteam.map(indexes).to_numpy()] = -1.
    x[:, -1] = grouped.venue
    penalty = np.full(66, settings.ridge_plays)
    penalty[0] = 0.
    penalty[-1] = 100.
    target = np.r_[0., prior[:, 0] * OFFSEASON_CARRY, prior[:, 1] * OFFSEASON_CARRY, 0.]
    a = x.T @ (x * grouped.w.to_numpy()[:, None]) + np.diag(penalty)
    b = x.T @ grouped.wy.to_numpy() + penalty * target
    beta = np.linalg.solve(a, b)
    units = np.column_stack([beta[1:33], beta[33:65]])
    # An explicit league-zero anchor preserves the neutral average interpretation.
    units -= units.mean(axis=0)
    counts = sample.groupby("posteam").w.sum().reindex(TEAMS, fill_value=0).to_numpy()
    return units, {"intercept": float(beta[0]), "venue": float(beta[-1])}, counts


def legacy_scores(rows, cutoff):
    sample = rows[rows.week <= cutoff]
    if sample.empty:
        return pd.Series(50., index=TEAMS), pd.Series(0., index=TEAMS)
    offense = sample.groupby("posteam")[["epa", "success"]].mean()
    defense = sample.groupby("defteam")[["epa", "success"]].mean()
    score = (offense.epa.rank(pct=True) + offense.success.rank(pct=True)
             + defense.epa.rank(pct=True, ascending=False)
             + defense.success.rank(pct=True, ascending=False)) * 25.
    return score.reindex(TEAMS).fillna(50.), (offense.epa - defense.epa).reindex(TEAMS).fillna(0.)


def st_game_values(pbp, games, baseline):
    rows = prepare_special_teams(pbp, games)
    # Limit the influence of a single rare return or blocked kick in a forecast.
    rows["value"] = (rows.result_value - expected_values(rows, baseline)).clip(-3., 3.)
    own = rows[["game_id", "posteam", "value"]].rename(columns={"posteam": "team"})
    opposite = rows[rows.play_type.isin(["punt", "kickoff"])
                    | (rows.field_goal_result == "blocked") | rows.blocked_player_id.notna()
                    | (rows.td_team.notna() & (rows.td_team == rows.defteam))]
    other = opposite[["game_id", "defteam", "value"]].rename(columns={"defteam": "team"}).copy()
    other["value"] *= -1
    totals = pd.concat([own, other]).groupby(["game_id", "team"], as_index=False).value.sum()
    return totals.merge(games[["game_id", "week"]], validate="many_to_one")


def fit_st(values, games, cutoff, settings, prior):
    counts = pd.concat([games[games.week <= cutoff][["game_id", "week", "home_team"]].rename(columns={"home_team": "team"}),
                        games[games.week <= cutoff][["game_id", "week", "away_team"]].rename(columns={"away_team": "team"})])
    counts["w"] = decay(counts.week, cutoff, settings.half_life_weeks)
    exposure = counts.groupby("team").w.sum().reindex(TEAMS, fill_value=0)
    sample = values[values.week <= cutoff].copy()
    sample["weighted"] = sample.value * decay(sample.week, cutoff, settings.half_life_weeks)
    total = sample.groupby("team").weighted.sum().reindex(TEAMS, fill_value=0)
    result = (total.to_numpy() + ST_PRIOR_GAMES * ST_CARRY * prior) / (exposure.to_numpy() + ST_PRIOR_GAMES)
    return result - result.mean()


def qb_rows(rows, units, context, season):
    sample = rows[rows.phase == "dropback"].copy()
    sample["qb_id"] = sample.passer_player_id.where(sample.passer_player_id.notna(), sample.rusher_player_id)
    sample["qb_name"] = sample.passer_player_name.where(sample.passer_player_id.notna(), sample.rusher_player_name)
    if sample.qb_id.isna().any():
        raise ValueError("Unattributed dropbacks in QB inputs")
    defense = dict(zip(TEAMS, units[:, 1]))
    sample["relative_epa"] = sample.epa - context["intercept"] + sample.defteam.map(defense) - context["venue"] * sample.venue
    sample["season"] = season
    return sample[["qb_id", "qb_name", "posteam", "week", "season", "relative_epa", "cpoe", "weight"]]


def qb_skills(history, current, season, cutoff):
    past = [frame for year, frame in history.items() if season - 2 <= year < season]
    frames = past + [current[current.week <= cutoff]]
    data = pd.concat(frames, ignore_index=True)
    age = data.groupby("season").week.transform("max") - data.week
    # Current aging is anchored on the actual forecast cutoff, including byes.
    age = age.where(data.season != season, cutoff - data.week)
    data["w"] = data.weight * QB_YEAR_CARRY ** (season - data.season) * .5 ** (age / 16.)
    data["wy"] = data.w * data.relative_epa
    data["wc"] = data.w.where(data.cpoe.notna(), 0.)
    data["wcy"] = data.wc * data.cpoe.fillna(0.)
    # Learn a conservative population prior from previously observed QBs,
    # rather than assigning an unseen backup the play-weighted league average.
    prior_data = data[data.season < season].groupby("qb_id")[["w", "wy", "wc", "wcy"]].sum()
    qualifying = prior_data[prior_data.w >= 20]
    prior_epa = float((qualifying.wy / qualifying.w).clip(-.5, .5).mean()) if len(qualifying) else 0.
    c = qualifying[qualifying.wc >= 20]
    prior_cpoe = float((c.wcy / c.wc).clip(-15, 15).mean()) if len(c) else 0.
    summed = data.groupby("qb_id")[["w", "wy", "wc", "wcy"]].sum()
    skill = pd.DataFrame(index=summed.index)
    skill["epa"] = (summed.wy + QB_PRIOR_PLAYS * prior_epa) / (summed.w + QB_PRIOR_PLAYS)
    skill["cpoe"] = (summed.wcy + QB_PRIOR_PLAYS * prior_cpoe) / (summed.wc + QB_PRIOR_PLAYS)
    skill["effective_dropbacks"] = summed.w
    names = data.drop_duplicates("qb_id", keep="last").set_index("qb_id").qb_name
    skill["name"] = names
    return skill, {"epa": prior_epa, "cpoe": prior_cpoe, "effective_dropbacks": 0.}


def lookup_skill(skills, qb_id, fallback):
    return skills.loc[qb_id].to_dict() if qb_id in skills.index else dict(fallback)


def qb_reference(rows, past, skills, fallback, cutoff, settings):
    sample = rows[(rows.phase == "dropback") & (rows.week <= cutoff)].copy()
    sample["qb_id"] = sample.passer_player_id.where(sample.passer_player_id.notna(), sample.rusher_player_id)
    sample["w"] = sample.weight * decay(sample.week, cutoff, settings.half_life_weeks)
    exposure = sample.groupby("posteam").w.sum().reindex(TEAMS, fill_value=0)
    result = []
    previous = past.copy() if past is not None else pd.DataFrame()
    if len(previous):
        previous["w"] = previous.weight * decay(previous.week, int(previous.week.max()), settings.half_life_weeks)
        previous_exposure = previous.groupby("posteam").w.sum().reindex(TEAMS, fill_value=0)
    for metric in ("epa", "cpoe"):
        mapping = skills[metric].to_dict()
        sample["weighted"] = sample.w * sample.qb_id.map(mapping).fillna(fallback[metric])
        total = sample.groupby("posteam").weighted.sum().reindex(TEAMS, fill_value=0)
        prior_value = pd.Series(0., index=TEAMS)
        if len(previous):
            previous["weighted"] = previous.w * previous.qb_id.map(mapping).fillna(fallback[metric])
            prior_value = (previous.groupby("posteam").weighted.sum().reindex(TEAMS, fill_value=0)
                           / previous_exposure.replace(0, np.nan)).fillna(0.) * OFFSEASON_CARRY
        result.append(((total + settings.ridge_plays * prior_value) / (exposure + settings.ridge_plays)).to_numpy())
    return np.column_stack(result)


def observed_starters(games, cutoff, prior_games=None):
    available = games[games.week <= cutoff]
    if prior_games is not None:
        available = pd.concat([prior_games, available]).sort_values(["season", "week", "gameday"])
    result = {}
    for row in available.itertuples():
        for side in ("home", "away"):
            qb_id = getattr(row, side + "_qb_id")
            if pd.notna(qb_id):
                result[getattr(row, side + "_team")] = {"id": str(qb_id), "name": getattr(row, side + "_qb_name")}
    return result


def add_qb_features(table, reference, skills, fallback, starters):
    table = table.copy()
    for i, team in enumerate(TEAMS):
        player = starters.get(team, {"id": "", "name": "Unconfirmed"})
        skill = lookup_skill(skills, player["id"], fallback)
        table.loc[team, "qb_epa_delta"] = skill["epa"] - reference[i, 0]
        table.loc[team, "qb_cpoe_delta"] = skill["cpoe"] - reference[i, 1]
    return table


def fit_margin(x, y, penalty):
    """Nonnegative ridge by coordinate descent; positive unit skill helps margin.

    Training-only scaling. The final column is home-field advantage, unscaled
    and unpenalized. No intercept: average vs average at a neutral venue is zero.
    """
    scale = np.std(x, axis=0)
    scale[scale < 1e-8] = 1.
    scale[-1] = 1.
    z = x / scale
    gram = z.T @ z
    regularizer = np.full(x.shape[1], float(penalty))
    regularizer[-1] = 0.
    gram += np.diag(regularizer)
    target = z.T @ y
    beta = np.zeros(x.shape[1])
    for _ in range(3000):
        before = beta.copy()
        for j in range(len(beta)):
            beta[j] = max(0., (target[j] - gram[j] @ beta + gram[j, j] * beta[j]) / gram[j, j]) if gram[j, j] > 0 else 0.
        if np.max(np.abs(before - beta)) < 1e-9:
            break
    return beta / scale


def metrics(actual, predictions):
    errors = np.asarray(actual) - np.asarray(predictions)
    return {"games": int(len(errors)), "mae": float(np.abs(errors).mean()), "rmse": float(np.sqrt(np.mean(errors ** 2)))}


class Builder:
    def __init__(self, cache, season, week):
        self.cache, self.season, self.week = cache, season, week
        manifest = json.loads((cache / "manifest.json").read_text(encoding="utf-8"))
        for source in manifest:
            if hashlib.sha256((cache / source["file"]).read_bytes()).hexdigest() != source["cache_sha256"]:
                raise ValueError(f"Cached input changed since retrieval: {source['file']}")
        self.all_schedule = normalize(pd.read_csv(cache / "games.csv"), ["home_team", "away_team"])
        self.schedule = self.all_schedule[(self.all_schedule.game_type == "REG") & self.all_schedule.home_score.notna() & self.all_schedule.away_score.notna()]
        self.games, self.rows, self.st = {}, {}, {}
        self.names = {}
        previous_baseline = None
        for year in range(2016, season + 1):
            pbp = normalize(pd.read_parquet(cache / f"pbp-{year}.parquet"), ["posteam", "defteam"])
            games = self.schedule[self.schedule.season == year].copy()
            if year == season:
                games = games[games.week <= week]
            if len(games) == 0:
                raise ValueError(f"No completed games for {year}")
            eligible = eligible_scrimmage_plays(pbp, set(games.game_id))
            self.games[year] = games
            self.rows[year] = prepare_plays(eligible, games)
            st_rows = prepare_special_teams(pbp, games)
            baseline = previous_baseline or make_baseline(st_rows)
            self.st[year] = st_game_values(pbp, games, baseline)
            previous_baseline = make_baseline(st_rows)
            for id_col, name_col in (("passer_player_id", "passer_player_name"), ("rusher_player_id", "rusher_player_name")):
                names = pbp[[id_col, name_col]].dropna().drop_duplicates(id_col, keep="last")
                self.names.update(dict(zip(names[id_col], names[name_col])))
        self.depth_all = normalize(pd.read_parquet(cache / "depth_charts.parquet"), ["team"])
        self.depth = self.depth_all[self.depth_all.dt == self.depth_all.dt.max()].copy()
        self.injuries = normalize(pd.read_parquet(cache / "injuries.parquet"), ["team"])

    def generate(self, settings):
        snapshots, forecast_rows, current_details = {}, [], None
        prior_pass, prior_run, prior_st = np.zeros((32, 2)), np.zeros((32, 2)), np.zeros(32)
        qb_history = {}
        for year in range(2016, self.season + 1):
            maximum = self.week if year == self.season else int(self.games[year].week.max())
            cutoffs = range(maximum + 1) if year >= 2019 else [maximum]
            for cutoff in cutoffs:
                passing, context, exposure = fit_phase(self.rows[year], "dropback", cutoff, settings, prior_pass)
                running, _, _ = fit_phase(self.rows[year], "designed_run", cutoff, settings, prior_run)
                st = fit_st(self.st[year], self.games[year], cutoff, settings, prior_st)
                table = pd.DataFrame({"pass_offense": passing[:, 0], "pass_defense": passing[:, 1],
                                      "run_offense": running[:, 0], "run_defense": running[:, 1], "st": st}, index=TEAMS)
                visible = self.rows[year][self.rows[year].week <= cutoff]
                current_qbs = qb_rows(visible, passing, context, year)
                skills, fallback = qb_skills(qb_history, current_qbs, year, cutoff)
                reference = qb_reference(self.rows[year], qb_history.get(year - 1), skills, fallback, cutoff, settings)
                starters = observed_starters(self.games[year], cutoff, self.games.get(year - 1))
                table = add_qb_features(table, reference, skills, fallback, starters)
                legacy, net_epa = legacy_scores(self.rows[year], cutoff)
                snapshots[year, cutoff] = table
                if year >= 2019:
                    future = self.games[year][self.games[year].week == cutoff + 1]
                    for game in future.itertuples():
                        forecast_rows.append({"season": year, "week": int(game.week), "game_id": game.game_id,
                            "home": game.home_team, "away": game.away_team, "actual": float(game.home_score - game.away_score),
                            "features": list((table.loc[game.home_team, FEATURES] - table.loc[game.away_team, FEATURES]).to_numpy())
                                        + [float(game.location == "Home")],
                            "legacy": [float(legacy[game.home_team] - legacy[game.away_team]), float(game.location == "Home")],
                            "net_epa": [float(net_epa[game.home_team] - net_epa[game.away_team]), float(game.location == "Home")],
                            "market": float(game.spread_line) if pd.notna(game.spread_line) else None})
                if year == self.season and cutoff == self.week:
                    current_details = {"table": table, "reference": reference, "skills": skills, "fallback": fallback,
                                       "starters": starters, "legacy": legacy, "effective_pass_plays": exposure}
            prior_pass, prior_run, prior_st = passing, running, st
            qb_history[year] = qb_rows(self.rows[year], passing, context, year)
        return pd.DataFrame(forecast_rows), current_details


def select_beta(builder):
    candidates = []
    generated = {}
    for ridge, half in itertools.product((150., 350., 700.), (4., 8., 16.)):
        settings = Settings(ridge, half)
        rows, details = builder.generate(settings)
        generated[settings] = (rows, details)
        train = rows[rows.season <= 2021]
        tune = rows[rows.season.isin([2022, 2023])]
        x = np.stack(train.features)
        tx = np.stack(tune.features)
        for penalty in (10., 40., 120.):
            coef = fit_margin(x, train.actual.to_numpy(), penalty)
            result = metrics(tune.actual, tx @ coef)
            candidates.append({"settings": settings, "margin_penalty": penalty, "validation": result})
        print(f"Evaluated {settings.label}", flush=True)
    candidates.sort(key=lambda r: (r["validation"]["mae"], r["validation"]["rmse"]))
    best = candidates[0]
    rows, details = generated[best["settings"]]
    train = rows[rows.season <= 2023]
    coef = fit_margin(np.stack(train.features), train.actual.to_numpy(), best["margin_penalty"])
    sensitivity = []
    chosen = set()
    for candidate in candidates:
        settings = candidate["settings"]
        if settings in chosen:
            continue
        chosen.add(settings)
        r, d = generated[settings]
        training = r[r.season <= 2023]
        c = fit_margin(np.stack(training.features), training.actual.to_numpy(), candidate["margin_penalty"])
        sensitivity.append((settings, d, c))
        if len(sensitivity) == 3:
            break
    validation = {"training": "2019-2021", "parameter_selection": "2022-2023",
                  "final_fit": "2019-2023", "comparison_seasons": [2024, 2025],
                  "note": "2024-25 were previously inspected in efficiency research; these are retrospective comparisons, not untouched holdouts. Historical QB selection uses only the most recently observed starter, not the next game's realized starter. No historical injury forecasts are included.",
                  "selected": {"ridge_plays": best["settings"].ridge_plays, "half_life_weeks": best["settings"].half_life_weeks,
                               "margin_penalty": best["margin_penalty"], "tuning_mae": best["validation"]["mae"]}, "seasons": {}}
    for year in (2024, 2025):
        test = rows[rows.season == year]
        x = np.stack(test.features)
        results = {"beta": metrics(test.actual, x @ coef)}
        for name, features in (("efficiency_index", "legacy"), ("raw_net_epa", "net_epa")):
            baseline = fit_margin(np.stack(train[features]), train.actual.to_numpy(), 40.)
            results[name] = metrics(test.actual, np.stack(test[features]) @ baseline)
        for name, remove in (("without_qb", [5, 6]), ("without_st", [4])):
            keep = [i for i in range(8) if i not in remove]
            c = fit_margin(np.stack(train.features)[:, keep], train.actual.to_numpy(), best["margin_penalty"])
            results[name] = metrics(test.actual, x[:, keep] @ c)
        available = test[test.market.notna()]
        results["market_spread"] = metrics(available.actual, available.market)
        validation["seasons"][str(year)] = results
        after_three = test[test.week >= 4]
        validation["seasons"][str(year)]["week_4_onward"] = {
            "beta": metrics(after_three.actual, np.stack(after_three.features) @ coef),
            "efficiency_index": metrics(after_three.actual, np.stack(after_three.legacy) @ fit_margin(np.stack(train.legacy), train.actual.to_numpy(), 40.)),
        }
    validation["candidates"] = [{"ridge_plays": c["settings"].ridge_plays, "half_life_weeks": c["settings"].half_life_weeks,
                                "margin_penalty": c["margin_penalty"], **c["validation"]} for c in candidates]
    return rows, details, coef, sensitivity, validation


def build_payload(builder, details, coef, sensitivity, validation):
    depth = builder.depth[(builder.depth.pos_abb == "QB") & builder.depth.gsis_id.notna()].sort_values(["team", "pos_rank"])
    expected = {}
    for team in TEAMS:
        listed = depth[depth.team == team]
        if len(listed):
            player = listed.iloc[0]
            expected[team] = {"id": player.gsis_id, "name": player.player_name}
        else:
            expected[team] = details["starters"].get(team, {"id": "", "name": "Unconfirmed"})
    table = add_qb_features(details["table"], details["reference"], details["skills"], details["fallback"], expected)
    contributions = table[FEATURES].to_numpy() * coef[:-1]
    center = contributions.mean(axis=0)
    contributions -= center
    strength = contributions.sum(axis=1)
    ranks = pd.Series(strength, index=TEAMS).rank(method="min", ascending=False).astype(int)
    legacy_ranks = details["legacy"].rank(method="min", ascending=False).astype(int)
    rank_samples = []
    for settings, d, c in sensitivity:
        t = add_qb_features(d["table"], d["reference"], d["skills"], d["fallback"], expected)
        s = t[FEATURES].to_numpy() @ c[:-1]
        rank_samples.append(pd.Series(s, index=TEAMS).rank(method="min", ascending=False).astype(int))
    teams = []
    games = builder.games[builder.season]
    for i, team in enumerate(TEAMS):
        played = games[(games.home_team == team) | (games.away_team == team)]
        margins = np.where(played.home_team == team, played.home_score - played.away_score, played.away_score - played.home_score)
        record = f"{int((margins > 0).sum())}-{int((margins < 0).sum())}"
        if (margins == 0).any():
            record += f"-{int((margins == 0).sum())}"
        options = []
        for qb in depth[depth.team == team].itertuples():
            skill = lookup_skill(details["skills"], qb.gsis_id, details["fallback"])
            change = (skill["epa"] - lookup_skill(details["skills"], expected[team]["id"], details["fallback"])["epa"]) * coef[5]
            change += (skill["cpoe"] - lookup_skill(details["skills"], expected[team]["id"], details["fallback"])["cpoe"]) * coef[6]
            options.append({"id": qb.gsis_id, "name": qb.player_name, "depth_rank": int(qb.pos_rank),
                            "points_change": float(change), "effective_dropbacks": float(skill["effective_dropbacks"])})
        warnings = []
        recent = details["starters"].get(team, {})
        if recent.get("id") != expected[team]["id"]:
            warnings.append(f"Depth-chart QB differs from last observed starter ({recent.get('name', 'unknown')}).")
        report = builder.injuries[(builder.injuries.team == team) & (builder.injuries.gsis_id == expected[team]["id"])]
        if len(report):
            latest = report.sort_values("week").iloc[-1]
            if pd.notna(latest.report_status):
                warnings.append(f"Latest injury designation: {latest.report_status}, Week {int(latest.week)}; this is not confirmation for the upcoming game.")
        if lookup_skill(details["skills"], expected[team]["id"], details["fallback"])["effective_dropbacks"] < 100:
            warnings.append("Limited quarterback sample; estimate relies heavily on the pooled prior.")
        teams.append({"abbr": team, "name": TEAM_NAMES[team], "record": record, "games": len(played),
                      "rank": int(ranks[team]), "strength": float(strength[i]), "efficiency_rank": int(legacy_ranks[team]),
                      "efficiency_value": float(details["legacy"][team]), "rank_difference": int(legacy_ranks[team] - ranks[team]),
                      "offense_points": float(contributions[i, 0] + contributions[i, 2]),
                      "defense_points": float(contributions[i, 1] + contributions[i, 3]),
                      "st_points": float(contributions[i, 4]), "qb_points": float(contributions[i, 5] + contributions[i, 6]),
                      "components": dict(zip(FEATURES, map(float, contributions[i]))),
                      "effective_pass_plays": float(details["effective_pass_plays"][i]),
                      "sensitivity_rank_min": min(int(r[team]) for r in rank_samples),
                      "sensitivity_rank_max": max(int(r[team]) for r in rank_samples),
                      "expected_qb": expected[team], "qb_options": options, "warnings": warnings})
    teams.sort(key=lambda t: t["rank"])
    # Reuse the chosen settings to provide a comparable Week 3 snapshot.
    settings = Settings(validation["selected"]["ridge_plays"], validation["selected"]["half_life_weeks"])
    previous_builder = Builder(builder.cache, builder.season, builder.week - 1)
    _, previous = previous_builder.generate(settings)
    previous_cutoff = pd.Timestamp(previous_builder.games[builder.season].gameday.max(), tz="UTC") + pd.Timedelta(days=1, hours=12)
    archived = builder.depth_all[pd.to_datetime(builder.depth_all.dt, utc=True) <= previous_cutoff]
    previous_starters = dict(previous["starters"])
    if len(archived):
        latest = archived[archived.dt == archived.dt.max()]
        for qb in latest[(latest.pos_abb == "QB") & (latest.pos_rank == 1) & latest.gsis_id.notna()].itertuples():
            previous_starters[qb.team] = {"id": qb.gsis_id, "name": qb.player_name}
    previous_table = add_qb_features(previous["table"], previous["reference"], previous["skills"], previous["fallback"], previous_starters)
    previous_values = previous_table[FEATURES].to_numpy() @ coef[:-1]
    previous_values -= previous_values.mean()
    previous_ranks = pd.Series(previous_values, index=TEAMS).rank(method="min", ascending=False).astype(int)
    for team in teams:
        team["previous_week_beta_rank"] = int(previous_ranks[team["abbr"]])
        team["previous_week_beta_strength"] = float(previous_values[TEAMS.index(team["abbr"])])
        team["weekly_rank_change"] = int(previous_ranks[team["abbr"]] - team["rank"])
    upcoming = builder.all_schedule[(builder.all_schedule.season == builder.season) & (builder.all_schedule.game_type == "REG")
                                    & (builder.all_schedule.week == builder.week + 1)]
    strength_by_team = dict(zip(TEAMS, strength))
    forecasts = [{"home": r.home_team, "away": r.away_team, "date": str(r.gameday), "venue": r.location,
                  "home_margin": float(strength_by_team[r.home_team] - strength_by_team[r.away_team] + (coef[-1] if r.location == "Home" else 0.))}
                 for r in upcoming.itertuples()]
    return {"version": VERSION, "season": builder.season, "week": builder.week,
            "generated_at": datetime.now(timezone.utc).isoformat(), "games": len(games),
            "depth_timestamp": str(builder.depth.dt.max()), "previous_week_depth_timestamp": str(archived.dt.max()) if len(archived) else None,
            "teams": teams, "forecasts": forecasts, "home_advantage": float(coef[-1]),
            "coefficients": dict(zip(FEATURES + ["home_advantage"], map(float, coef))), "validation": validation,
            "constants": {"offseason_carry": OFFSEASON_CARRY, "st_carry": ST_CARRY, "st_prior_games": ST_PRIOR_GAMES,
                          "st_play_residual_cap": 3., "qb_prior_plays": QB_PRIOR_PLAYS, "qb_year_carry": QB_YEAR_CARRY},
            "notes": ["Local research beta; published Efficiency Index is unchanged.",
                      "Points estimate above an average team at a neutral venue; not a win probability.",
                      "QB selection uses the latest depth chart, with scenarios for listed alternatives. Future participation is uncertain.",
                      "Week 3 comparison uses an archived depth snapshot from the Tuesday after Week 3, with most-recent observed starters as fallback.",
                      "Rank range reflects three tuned parameter settings, not a statistical confidence interval.",
                      "QB skill is an opponent-adjusted statistical proxy and retains surrounding-offense confounding.",
                      "ST is pooled at team level, not a separate individual kicker/punter forecast; weather and availability of non-QBs are not modeled."]}
