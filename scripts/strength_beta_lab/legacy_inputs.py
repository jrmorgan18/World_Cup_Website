"""Frozen eligibility rules and team labels used by beta 0.1; production is unchanged."""

import pandas as pd
from efficiency_model import EXTRA_COLUMNS
from special_teams import EXTRA_COLUMNS as ST_COLUMNS

PBP_COLUMNS = [
    "game_id",
    "season_type",
    "week",
    "posteam",
    "defteam",
    "play_type",
    "pass_attempt",
    "epa",
    "cpoe",
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
    "sack",
] + EXTRA_COLUMNS + ST_COLUMNS

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
