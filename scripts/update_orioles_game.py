#!/usr/bin/env python3
"""Update _data/orioles_last_game.json with the Orioles' most recent final score.

Pulls the last completed Orioles game (score, decisions, hits/errors, top
performers) and the current AL East / Wild Card standing from the free MLB
Stats API (statsapi.mlb.com — no key required) and writes them to
_data/orioles_last_game.json. The card on /orioles/ then reflects the new
result on the next GitHub Pages build.

Behaviour:
  * Never fails the build — any network/parsing error is logged and the
    script exits 0 without touching the data file.
  * Only looks at regular-season games with status "Final".
  * The card can also be edited by hand in _data/orioles_last_game.json.
"""
import json
import os
import sys
import urllib.request
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "_data", "orioles_last_game.json")

ORIOLES_ID = 110
WILD_CARD_SPOTS = 3
AL_EAST_DIVISION_ID = 201
AL_LEAGUE_ID = 103


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dualeights-orioles-card/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def find_last_final_game():
    end = date.today()
    start = end - timedelta(days=14)
    url = (
        "https://statsapi.mlb.com/api/v1/schedule"
        "?sportId=1&teamId=%d&gameType=R&hydrate=team,linescore,decisions"
        "&startDate=%s&endDate=%s" % (ORIOLES_ID, start.isoformat(), end.isoformat())
    )
    data = fetch_json(url)
    games = []
    for d in data.get("dates", []):
        games.extend(d.get("games", []))
    finals = [g for g in games if g.get("status", {}).get("detailedState") == "Final"]
    if not finals:
        return None
    finals.sort(key=lambda g: g.get("gameDate", ""))
    return finals[-1]


def pitcher_from_box(box, side_key, person):
    if not person:
        return None
    pid = person["id"]
    for side in ("home", "away"):
        team = box["teams"][side]
        player = team["players"].get("ID%d" % pid)
        if player:
            pitching = player.get("stats", {}).get("pitching", {})
            note = (pitching.get("note") or "").strip("() ")
            # note looks like "W, 7-7" / "L, 3-8" / "S, 5" — keep just the record part
            record = note.split(",", 1)[1].strip() if "," in note else note
            return {
                "name": person["fullName"],
                "team": team["team"]["abbreviation"],
                "record": record or None,
                "line": pitching.get("summary"),
            }
    return None


def build_key_players(box):
    players = []
    for tp in box.get("topPerformers", [])[:4]:
        p = tp["player"]
        team_id = p.get("parentTeamId")
        team_abbr = "BAL" if team_id == ORIOLES_ID else None
        if team_abbr is None:
            for side in ("home", "away"):
                if box["teams"][side]["team"]["id"] == team_id:
                    team_abbr = box["teams"][side]["team"]["abbreviation"]
        stats = p.get("stats", {})
        line = (stats.get("batting") or {}).get("summary") or (stats.get("pitching") or {}).get("summary")
        if not line:
            continue
        players.append({"name": p["person"]["fullName"], "team": team_abbr, "position": p["position"]["abbreviation"], "line": line})
    return players


def build_summary(orioles_name, opponent, is_home, os_, as_, result, streak_code, key_players):
    verb = "beat" if result == "W" else "fell to"
    location = "at Camden Yards" if is_home else "on the road at %s" % opponent
    streak_num = "".join(c for c in (streak_code or "") if c.isdigit()) or "1"
    streak_word = "won" if (streak_code or "").startswith("W") else "lost"
    highlight = ""
    if key_players:
        top = key_players[0]
        highlight = " %s led the way (%s)." % (top["name"], top["line"])
    return "The Orioles %s the %s %d-%d %s.%s Baltimore has %s %s straight." % (
        verb, opponent, os_, as_, location, highlight, streak_word, streak_num,
    )


def wild_card_status_text(rank, games_back):
    if rank is not None and rank <= WILD_CARD_SPOTS:
        return "Holding the No. %d AL Wild Card spot." % rank
    if games_back in (None, "-"):
        return "In the AL Wild Card race."
    return "%s games back of the third AL Wild Card spot." % games_back


def main():
    try:
        game = find_last_final_game()
        if not game:
            print("No recent Final games found — skipping.")
            return 0

        home = game["teams"]["home"]
        away = game["teams"]["away"]
        is_home = home["team"]["id"] == ORIOLES_ID
        orioles_side, opp_side = (home, away) if is_home else (away, home)
        opponent = opp_side["team"]["name"]
        opponent_short = opp_side["team"].get("teamName", opponent)

        ls = game.get("linescore", {}).get("teams", {})
        home_ls = ls.get("home", {})
        away_ls = ls.get("away", {})
        orioles_ls, opp_ls = (home_ls, away_ls) if is_home else (away_ls, home_ls)

        result = "W" if orioles_side.get("isWinner") else "L"

        box = fetch_json("https://statsapi.mlb.com/api/v1/game/%d/boxscore" % game["gamePk"])

        decisions = game.get("decisions", {})
        winning_pitcher = pitcher_from_box(box, "home", decisions.get("winner"))
        losing_pitcher = pitcher_from_box(box, "away", decisions.get("loser"))
        save_pitcher = pitcher_from_box(box, "home", decisions.get("save"))

        key_players = build_key_players(box)

        standings = fetch_json(
            "https://statsapi.mlb.com/api/v1/standings"
            "?leagueId=%d&season=%s&standingsTypes=regularSeason" % (AL_LEAGUE_ID, date.today().year)
        )
        orioles_record = None
        for rec in standings.get("records", []):
            if rec.get("division", {}).get("id") != AL_EAST_DIVISION_ID:
                continue
            for t in rec.get("teamRecords", []):
                if t["team"]["id"] == ORIOLES_ID:
                    orioles_record = t
                    break

        record_block = None
        wild_card_block = None
        if orioles_record:
            lr = orioles_record.get("leagueRecord", {})
            last_ten = next(
                (s for s in orioles_record.get("records", {}).get("splitRecords", []) if s.get("type") == "lastTen"),
                None,
            )
            record_block = {
                "wins": lr.get("wins"),
                "losses": lr.get("losses"),
                "pct": lr.get("pct"),
                "division": "AL East",
                "division_rank": int(orioles_record.get("divisionRank")) if orioles_record.get("divisionRank") else None,
                "games_back": orioles_record.get("gamesBack"),
                "streak": orioles_record.get("streak", {}).get("streakCode"),
                "last_10": "%d-%d" % (last_ten["wins"], last_ten["losses"]) if last_ten else None,
            }
            wc_rank = int(orioles_record.get("wildCardRank")) if orioles_record.get("wildCardRank") else None
            wc_gb = orioles_record.get("wildCardGamesBack")
            wild_card_block = {
                "rank": wc_rank,
                "spots": WILD_CARD_SPOTS,
                "games_back": wc_gb,
                "status_text": wild_card_status_text(wc_rank, wc_gb),
            }

        summary = build_summary(
            "Orioles", opponent_short, is_home,
            orioles_side.get("score"), opp_side.get("score"),
            result, record_block.get("streak") if record_block else None,
            key_players,
        )

        out = {
            "generated_at": None,  # filled below
            "game_pk": game["gamePk"],
            "date": game.get("officialDate"),
            "venue": game.get("venue", {}).get("name"),
            "home_away": "home" if is_home else "away",
            "opponent": opponent,
            "opponent_abbr": opp_side["team"].get("abbreviation"),
            "result": result,
            "orioles_score": orioles_side.get("score"),
            "opponent_score": opp_side.get("score"),
            "orioles_hits": orioles_ls.get("hits"),
            "opponent_hits": opp_ls.get("hits"),
            "orioles_errors": orioles_ls.get("errors"),
            "opponent_errors": opp_ls.get("errors"),
            "winning_pitcher": winning_pitcher,
            "losing_pitcher": losing_pitcher,
            "save_pitcher": save_pitcher,
            "key_players": key_players,
            "summary": summary,
            "record": record_block,
            "wild_card": wild_card_block,
        }

        import datetime
        out["generated_at"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        existing = None
        if os.path.exists(OUT_PATH):
            with open(OUT_PATH, encoding="utf-8") as f:
                existing = json.load(f)

        if existing and existing.get("game_pk") == out["game_pk"] and existing.get("result") == out["result"] \
                and existing.get("orioles_score") == out["orioles_score"] and existing.get("record") == out["record"]:
            print("No changes (game %s already up to date)." % out["game_pk"])
            return 0

        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("Updated orioles_last_game.json: %s %s %d-%d vs %s" % (
            out["date"], result, out["orioles_score"], out["opponent_score"], opponent,
        ))
        return 0
    except Exception as e:  # network/API changes/etc. — never fail the build
        print("Orioles game update failed (%s) — skipping." % e)
        return 0


if __name__ == "__main__":
    sys.exit(main())
