#!/usr/bin/env python3
"""Build the public Project 2030 Big Board data file from a vetted score export.

Usage:
    python scripts/build_project_2030_big_board.py \
      --scores path/to/big-board-pool-scores.json \
      --transfermarkt path/to/big-board-transfermarkt-full.json

The resulting JSON is intentionally small and contains only the fields shown
on the public board. The source model, evidence ledger and manual data queue
remain private working material.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
POOL_PATH = ROOT / "_data" / "project_2030_player_pool.yml"
PROFILES_PATH = ROOT / "_data" / "project_2030_profiles.yml"
DEFAULT_OUTPUT = ROOT / "assets" / "data" / "project-2030-big-board.json"


LEAGUE_NAMES = {
    "A1": "Austrian Bundesliga",
    "BE1": "Belgian Pro League",
    "BR1": "Brazilian Serie A",
    "CH1": "Swiss Super League",
    "DE1": "Bundesliga",
    "DE2": "2. Bundesliga",
    "DK1": "Danish Superliga",
    "DK2": "Danish 1st Division",
    "ES1": "La Liga",
    "ES2": "La Liga 2",
    "FR1": "Ligue 1",
    "GB1": "Premier League",
    "GB2": "Championship",
    "GR1": "Greek Super League",
    "HR1": "Croatian Football League",
    "IT1": "Serie A",
    "IT2": "Serie B",
    "L1": "Ligue 1",
    "MLS1": "Major League Soccer",
    "NL1": "Eredivisie",
    "NO1": "Eliteserien",
    "PO1": "Primeira Liga",
    "RO1": "Romanian SuperLiga",
    "SC1": "Scottish Premiership",
    "TR1": "Süper Lig",
    "USL1": "USL Championship",
}

# The Transfermarkt snapshot covers most of the pool. These keep the few
# players without a matched competition record useful to visitors as well.
CLUB_LEAGUE_FALLBACKS = {
    "Bayer Leverkusen": "Bundesliga",
    "Borussia Mönchengladbach": "Bundesliga",
    "Borussia M�nchengladbach II": "Regionalliga West",
    "Caleb Wiley (Chelsea / Watford)": "Premier League",
    "Chelsea (future unsettled after Watford loan)": "Premier League",
    "Columbus Crew": "Major League Soccer",
    "Colorado Rapids": "Major League Soccer",
    "Coventry City": "Championship",
    "D.C. United": "Major League Soccer",
    "Derby County": "Championship",
    "FC Cincinnati": "Major League Soccer",
    "Hajduk Split": "Croatian Football League",
    "Holstein Kiel": "2. Bundesliga",
    "Houston Dynamo": "Major League Soccer",
    "Jong PSV": "Eerste Divisie",
    "Jong PSV / PSV Eindhoven": "Eerste Divisie",
    "Middlesbrough": "Championship",
    "New England Revolution": "Major League Soccer",
    "New York City FC": "Major League Soccer",
    "New York Red Bulls": "Major League Soccer",
    "Philadelphia Union": "Major League Soccer",
    "Real Madrid academy": "Real Madrid academy",
    "Real Salt Lake": "Major League Soccer",
    "San Jose Earthquakes": "Major League Soccer",
    "Seattle Sounders": "Major League Soccer",
    "Venezia": "Serie B",
    "Vancouver Whitecaps": "Major League Soccer",
    "Club Am�rica": "Liga MX",
}

PLAYER_FALLBACKS = {
    "kristoffer-lund": {"club": "1. FC Köln", "league": "Bundesliga"},
    "luca-de-la-torre": {"club": "Charlotte FC", "league": "Major League Soccer"},
    "james-sands": {"club": "FC St. Pauli", "league": "Bundesliga"},
    "cade-cowell": {"club": "New York Red Bulls", "league": "Major League Soccer"},
}


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def rounded(value):
    return round(float(value), 1) if value is not None else None


def fallback_league(club: str) -> str | None:
    """Return a display league when the source snapshot lacks a competition."""
    if club.startswith("Club Am"):
        return "Liga MX"
    if club.startswith("Borussia M") and club.endswith("II"):
        return "Regionalliga West"
    return CLUB_LEAGUE_FALLBACKS.get(club)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", required=True, type=Path, help="Vetted Big Board score export")
    parser.add_argument(
        "--transfermarkt",
        required=True,
        type=Path,
        help="Transfermarkt full export used to identify the current league",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT, help="Public JSON destination")
    args = parser.parse_args()

    pool = load_yaml(POOL_PATH)
    profiles = load_yaml(PROFILES_PATH)
    score_export = load_json(args.scores)
    transfermarkt = load_json(args.transfermarkt)

    pool_by_profile = {player["profile"]: player for player in pool["players"]}
    group_names = {group["id"]: group["name"] for group in pool["groups"]}
    transfermarkt_by_player = {player["player_id"]: player for player in transfermarkt["players"]}

    players = []
    missing_leagues = []
    for score in score_export["players"]:
        player_id = score["player_id"]
        pool_player = pool_by_profile.get(player_id, {})
        profile = profiles.get(player_id, {})
        transfermarkt_player = transfermarkt_by_player.get(player_id, {})
        player_fallback = PLAYER_FALLBACKS.get(player_id, {})
        club = profile.get("club") or player_fallback.get("club", "")
        competitions = transfermarkt_player.get("competitions") or []
        league = LEAGUE_NAMES.get(competitions[0]) if competitions else None
        league = league or player_fallback.get("league") or fallback_league(club)
        if not league:
            missing_leagues.append(f"{score['name']} ({club or 'no club'})")

        players.append(
            {
                "rank": score.get("rank"),
                "name": score["name"],
                "profile": player_id,
                "position": score.get("position_group") or profile.get("position", ""),
                "group": group_names.get(pool_player.get("group"), ""),
                "current_score": rounded(score.get("current_score")),
                "score_2030": rounded(score.get("score_2030")),
                "age_2030": pool_player.get("age_2030"),
                "club": club,
                "league": league or "Unlisted",
                "data_status": score.get("data_status", "unscored"),
            }
        )

    players.sort(key=lambda player: (player["rank"] is None, player["rank"] or 999, player["name"]))
    output = {
        "schema_version": 1,
        "title": "Project 2030 Big Board",
        "snapshot_through": score_export.get("window", {}).get("end"),
        "players": players,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Wrote {len(players)} players to {args.out}")
    if missing_leagues:
        print("Players using the Unlisted league fallback:")
        for player in missing_leagues:
            print(f"  - {player}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
