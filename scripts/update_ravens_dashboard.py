#!/usr/bin/env python3
"""Build the Ravens dashboard's objective weekly snapshot from nflverse.

The script uses free, keyless nflverse schedule and play-by-play releases. It
keeps prior weekly snapshots in the generated JSON so the Jekyll dashboard can
show real week-over-week movement. Availability and editorial assessments stay
in _data/ravens_dashboard.yml so dated official club reports can be reviewed
before health context is published.

Usage:
  python scripts/update_ravens_dashboard.py
  python scripts/update_ravens_dashboard.py --as-of 2026-09-03

Requires pandas and pyarrow. A failed download leaves the existing JSON intact.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "_data" / "ravens_dashboard_stats.json"
TEAM = "BAL"
SCHEDULE_URL = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.parquet"
PBP_DOCS_URL = "https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html"

PBP_COLUMNS = [
    "game_id",
    "season_type",
    "week",
    "posteam",
    "defteam",
    "play_type",
    "epa",
    "success",
    "yards_gained",
    "interception",
    "fumble_lost",
    "yardline_100",
    "fixed_drive",
    "touchdown",
    "td_team",
    "qb_kneel",
    "qb_spike",
    "two_point_attempt",
    "play_deleted",
    "aborted_play",
]

TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills", "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns", "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos", "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs", "LA": "Los Angeles Rams", "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NE": "New England Patriots", "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}

METRICS = {
    "point_differential": {"direction": "higher", "source": "nflverse schedules"},
    "turnover_differential": {"direction": "higher", "source": "nflverse play-by-play"},
    "offensive_epa_per_play": {"direction": "higher", "source": "nflverse play-by-play"},
    "offensive_success_rate": {"direction": "higher", "source": "nflverse play-by-play"},
    "explosive_play_rate": {"direction": "higher", "source": "nflverse play-by-play"},
    "red_zone_td_rate": {"direction": "higher", "source": "nflverse play-by-play"},
    "defensive_epa_per_play": {"direction": "lower", "source": "nflverse play-by-play"},
    "defensive_success_rate": {"direction": "lower", "source": "nflverse play-by-play"},
    "explosive_play_rate_allowed": {"direction": "lower", "source": "nflverse play-by-play"},
    "opponent_red_zone_td_rate": {"direction": "lower", "source": "nflverse play-by-play"},
}


def finite_number(value, digits=None):
    if value is None or pd.isna(value) or not math.isfinite(float(value)):
        return None
    number = float(value)
    if digits is None:
        return int(round(number))
    return round(number, digits)


def read_existing(path):
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def comparable_payload(payload):
    """Drop retrieval-only fields so scheduled runs do not create empty commits."""
    clean = json.loads(json.dumps(payload))
    clean.pop("generated_at", None)
    clean.pop("as_of", None)
    clean.get("sources", {}).pop("retrieved_at", None)
    return clean


def completed_games(schedule, season, as_of):
    games = schedule[
        (schedule["season"] == season)
        & (schedule["game_type"] == "REG")
        & (pd.to_datetime(schedule["gameday"]).dt.date <= as_of)
        & schedule["home_score"].notna()
        & schedule["away_score"].notna()
    ].copy()
    return games


def team_records(games):
    rows = []
    for _, game in games.iterrows():
        home_margin = float(game["home_score"] - game["away_score"])
        for team, margin in ((game["home_team"], home_margin), (game["away_team"], -home_margin)):
            rows.append({
                "team": team,
                "wins": int(margin > 0),
                "losses": int(margin < 0),
                "ties": int(margin == 0),
                "point_differential": margin,
            })
    if not rows:
        return pd.DataFrame(columns=["wins", "losses", "ties", "point_differential"])
    return pd.DataFrame(rows).groupby("team", as_index=True).sum()


def eligible_scrimmage_plays(pbp, valid_game_ids):
    valid = pbp[
        (pbp["season_type"] == "REG")
        & pbp["game_id"].isin(valid_game_ids)
        & pbp["play_type"].isin(["run", "pass"])
        & pbp["epa"].notna()
        & (pbp["qb_kneel"].fillna(0) != 1)
        & (pbp["qb_spike"].fillna(0) != 1)
        & (pbp["two_point_attempt"].fillna(0) != 1)
        & (pbp["play_deleted"].fillna(0) != 1)
        & (pbp["aborted_play"].fillna(0) != 1)
    ].copy()
    valid["explosive"] = (
        ((valid["play_type"] == "run") & (valid["yards_gained"] >= 10))
        | ((valid["play_type"] == "pass") & (valid["yards_gained"] >= 20))
    )
    return valid


def red_zone_rates(plays, team_column):
    rows = plays[
        plays[team_column].notna()
        & plays["fixed_drive"].notna()
    ].copy()
    if rows.empty:
        return pd.Series(dtype=float)
    rows["reached_red_zone"] = rows["yardline_100"].notna() & (rows["yardline_100"] <= 20)
    rows["drive_td"] = (rows["touchdown"].fillna(0) == 1) & (rows["td_team"] == rows["posteam"])
    drives = rows.groupby([team_column, "game_id", "fixed_drive"], as_index=False)[["reached_red_zone", "drive_td"]].max()
    drives = drives[drives["reached_red_zone"]]
    return drives.groupby(team_column)["drive_td"].mean() * 100


def compute_league_metrics(schedule_games, pbp):
    records = team_records(schedule_games)
    if schedule_games.empty:
        return records, pd.DataFrame(columns=METRICS.keys())

    plays = eligible_scrimmage_plays(pbp, set(schedule_games["game_id"]))
    teams = sorted(set(records.index) | set(plays["posteam"].dropna()) | set(plays["defteam"].dropna()))
    table = pd.DataFrame(index=teams)
    table["point_differential"] = records["point_differential"]

    turnover_plays = pbp[
        (pbp["season_type"] == "REG")
        & pbp["game_id"].isin(set(schedule_games["game_id"]))
        & pbp["posteam"].notna()
        & (pbp["play_deleted"].fillna(0) != 1)
        & (pbp["two_point_attempt"].fillna(0) != 1)
    ].copy()
    turnover_plays["giveaway"] = (
        turnover_plays["interception"].fillna(0) + turnover_plays["fumble_lost"].fillna(0)
    )
    giveaways = turnover_plays.groupby("posteam")["giveaway"].sum()
    takeaways = turnover_plays.groupby("defteam")["giveaway"].sum()
    table["turnover_differential"] = takeaways.sub(giveaways, fill_value=0)

    offense = plays.groupby("posteam")
    defense = plays.groupby("defteam")
    table["offensive_epa_per_play"] = offense["epa"].mean()
    table["offensive_success_rate"] = offense["success"].mean() * 100
    table["explosive_play_rate"] = offense["explosive"].mean() * 100
    table["defensive_epa_per_play"] = defense["epa"].mean()
    table["defensive_success_rate"] = defense["success"].mean() * 100
    table["explosive_play_rate_allowed"] = defense["explosive"].mean() * 100
    table["red_zone_td_rate"] = red_zone_rates(plays, "posteam")
    table["opponent_red_zone_td_rate"] = red_zone_rates(plays, "defteam")

    return records, table


def metric_payload(table, team):
    payload = {}
    for metric_id, definition in METRICS.items():
        values = table[metric_id].dropna() if metric_id in table else pd.Series(dtype=float)
        value = table.at[team, metric_id] if team in table.index and metric_id in table else None
        rank = None
        if value is not None and not pd.isna(value):
            ascending = definition["direction"] == "lower"
            ranks = values.rank(method="min", ascending=ascending)
            rank = int(ranks.loc[team]) if team in ranks.index else None
        digits = 2 if "epa_per_play" in metric_id else (1 if "rate" in metric_id else None)
        payload[metric_id] = {
            "value": finite_number(value, digits),
            "rank": rank,
            "source": definition["source"],
        }
    return payload


def record_text(records, team):
    if team not in records.index:
        return "0-0"
    row = records.loc[team]
    base = f"{int(row['wins'])}-{int(row['losses'])}"
    return f"{base}-{int(row['ties'])}" if int(row["ties"]) else base


def format_next_game(schedule, season, as_of):
    upcoming = schedule[
        (schedule["season"] == season)
        & (schedule["game_type"] == "REG")
        & ((schedule["home_team"] == TEAM) | (schedule["away_team"] == TEAM))
        & (pd.to_datetime(schedule["gameday"]).dt.date >= as_of)
        & schedule["home_score"].isna()
    ].sort_values(["gameday", "gametime"])
    if upcoming.empty:
        return None
    game = upcoming.iloc[0]
    is_home = game["home_team"] == TEAM
    opponent = game["away_team"] if is_home else game["home_team"]
    game_date = pd.to_datetime(game["gameday"])
    raw_time = str(game.get("gametime") or "")
    try:
        time_display = datetime.strptime(raw_time, "%H:%M").strftime("%-I:%M %p")
    except (TypeError, ValueError):
        try:
            time_display = datetime.strptime(raw_time, "%H:%M").strftime("%I:%M %p").lstrip("0")
        except (TypeError, ValueError):
            time_display = "Time TBD"
    date_display = f"{game_date.strftime('%b')} {game_date.day}"
    return {
        "week": int(game["week"]),
        "opponent": TEAM_NAMES.get(opponent, opponent),
        "opponent_abbr": opponent,
        "location": "home" if is_home else "away",
        "date": game_date.date().isoformat(),
        "display": f"{'vs.' if is_home else 'at'} {TEAM_NAMES.get(opponent, opponent)} · {date_display} · {time_display} ET",
        "venue": game.get("stadium") if pd.notna(game.get("stadium")) else None,
        "source": "nflverse schedules",
    }


def recent_games_payload(schedule_games):
    games = schedule_games[(schedule_games["home_team"] == TEAM) | (schedule_games["away_team"] == TEAM)]
    games = games.sort_values(["gameday", "week"], ascending=False).head(5)
    payload = []
    for _, game in games.iterrows():
        is_home = game["home_team"] == TEAM
        team_score = int(game["home_score"] if is_home else game["away_score"])
        opp_score = int(game["away_score"] if is_home else game["home_score"])
        opponent = game["away_team"] if is_home else game["home_team"]
        payload.append({
            "game_id": game["game_id"],
            "week": f"Week {int(game['week'])}",
            "date": str(game["gameday"]),
            "location": "home" if is_home else "away",
            "opponent": TEAM_NAMES.get(opponent, opponent),
            "result": "W" if team_score > opp_score else ("L" if team_score < opp_score else "T"),
            "ravens_score": team_score,
            "opponent_score": opp_score,
        })
    return payload


def streak_text(recent_games):
    if not recent_games:
        return "—"
    result = recent_games[0]["result"]
    length = 0
    for game in recent_games:
        if game["result"] != result:
            break
        length += 1
    return f"{result}{length}"


def build_snapshot(season, records, table):
    games_played = int(records.loc[TEAM, ["wins", "losses", "ties"]].sum()) if TEAM in records.index else 0
    week = int(table.attrs.get("week", 0))
    snapshot_id = f"{season}-week-{week:02d}" if games_played else f"{season}-preseason"
    return {
        "id": snapshot_id,
        "week": week,
        "label": f"Through Week {week}" if games_played else f"{season} preseason",
        "previous_snapshot": None,
        "sample_note": f"{games_played} regular-season game{'s' if games_played != 1 else ''}" if games_played else "No 2026 regular-season games yet",
        "record": record_text(records, TEAM),
        "metrics": metric_payload(table, TEAM) if games_played else {
            metric_id: {"value": None, "rank": None, "source": definition["source"]}
            for metric_id, definition in METRICS.items()
        },
    }


def merge_snapshots(existing, current):
    snapshots = [s for s in existing.get("snapshots", []) if s.get("id") != current["id"]]
    prior = [s for s in snapshots if s.get("week", -1) < current["week"]]
    if prior:
        current["previous_snapshot"] = sorted(prior, key=lambda s: s.get("week", -1))[-1]["id"]
    snapshots.append(current)
    return sorted(snapshots, key=lambda s: (s.get("week", -1), s.get("id", "")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=date.today().year)
    parser.add_argument("--benchmark-season", type=int, default=None)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    benchmark_season = args.benchmark_season or args.season - 1

    try:
        schedule = pd.read_csv(SCHEDULE_URL)
        current_games = completed_games(schedule, args.season, args.as_of)
        benchmark_games = completed_games(schedule, benchmark_season, args.as_of)
        # A current-season release may not exist before the first regular-season
        # game. In that state the schedule is authoritative and the metrics stay
        # null; do not turn a missing preseason PBP file into a false zero.
        if current_games.empty:
            current_pbp = pd.DataFrame(columns=PBP_COLUMNS)
        else:
            current_pbp = pd.read_parquet(PBP_URL.format(season=args.season), columns=PBP_COLUMNS)
        benchmark_pbp = pd.read_parquet(PBP_URL.format(season=benchmark_season), columns=PBP_COLUMNS)

        current_records, current_table = compute_league_metrics(current_games, current_pbp)
        benchmark_records, benchmark_table = compute_league_metrics(benchmark_games, benchmark_pbp)
        ravens_games = current_games[(current_games["home_team"] == TEAM) | (current_games["away_team"] == TEAM)]
        current_table.attrs["week"] = int(ravens_games["week"].max()) if not ravens_games.empty else 0
        benchmark_ravens = benchmark_games[(benchmark_games["home_team"] == TEAM) | (benchmark_games["away_team"] == TEAM)]
        benchmark_table.attrs["week"] = int(benchmark_ravens["week"].max()) if not benchmark_ravens.empty else 18

        current = build_snapshot(args.season, current_records, current_table)
        benchmark = build_snapshot(benchmark_season, benchmark_records, benchmark_table)
        benchmark["id"] = f"{benchmark_season}-final"
        benchmark["label"] = f"{benchmark_season} final benchmark"
        benchmark["previous_snapshot"] = None

        output = args.output.resolve()
        existing = read_existing(output)
        snapshots = merge_snapshots(existing, current)
        recent_games = recent_games_payload(current_games)
        sequence = [game["result"] for game in reversed(recent_games)]
        recent_margin = sum(game["ravens_score"] - game["opponent_score"] for game in recent_games)
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        payload = {
            "generated_at": now,
            "as_of": args.as_of.isoformat(),
            "season": args.season,
            "benchmark_season": benchmark_season,
            "current_snapshot": current["id"],
            "snapshots": snapshots,
            "benchmark_snapshot": benchmark,
            "header": {
                "record": current["record"],
                "division_standing": "Standings begin after Week 1" if current["week"] == 0 else "AFC North",
                "streak": streak_text(recent_games),
                "next_game": format_next_game(schedule, args.season, args.as_of),
            },
            "recent_form": {
                "sequence": sequence,
                "record": None if not sequence else f"{sequence.count('W')}-{sequence.count('L')}",
                "point_differential": recent_margin if sequence else None,
            },
            "recent_games": recent_games,
            "sources": {
                "schedule": {"label": "nflverse schedules", "url": SCHEDULE_URL},
                "play_by_play": {"label": "nflverse play-by-play", "url": PBP_URL.format(season=args.season)},
                "methodology": {"label": "nflverse data update schedule", "url": PBP_DOCS_URL},
                "license": "CC BY 4.0",
                "retrieved_at": now,
            },
        }

        if existing and comparable_payload(existing) == comparable_payload(payload):
            print(f"No football-data changes; keeping {output.relative_to(ROOT)} unchanged.")
            return 0

        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary, output)
        print(f"Updated {output.relative_to(ROOT)}: {current['label']} ({current['record']}); benchmark {benchmark_season} loaded.")
        return 0
    except Exception as error:
        print(f"Ravens dashboard update failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
