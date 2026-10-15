"""Optional receiver efficiency from SumerSports' public season WR table."""

from __future__ import annotations

import html
import re
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

SOURCE_URL = "https://sumersports.com/players/wide-receiver/"
TEAM_ALIASES = {"BLT": "BAL", "CLV": "CLE", "HST": "HOU", "ARZ": "ARI", "LAR": "LA"}
TEAMS = set("ARI ATL BAL BUF CAR CHI CIN CLE DAL DEN DET GB HOU IND JAX KC LA LAC LV MIA MIN NE NO NYG NYJ PHI PIT SEA SF TB TEN WAS".split())


def text(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def parse_receivers(page, season):
    # Read only the visible public table, never hydration data or paid splits.
    if not re.search(rf">\s*{season} Season\s*<", page):
        raise ValueError("Public receiver table is not the requested season")
    timestamp = re.search(r'<time\b[^>]*datetime="([^"]+)"', page, re.I)
    if not timestamp:
        raise ValueError("Receiver table has no update timestamp")
    updated = datetime.fromisoformat(timestamp[1].replace("Z", "+00:00"))
    if updated.tzinfo is None or not season <= updated.year <= season + 1:
        raise ValueError("Receiver table timestamp has an invalid season or timezone")
    if updated > datetime.now(timezone.utc):
        raise ValueError("Receiver table timestamp is in the future")
    for table in re.findall(r"<table\b[^>]*>(.*?)</table>", page, re.I | re.S):
        headers = [text(cell) for cell in re.findall(r"<th\b[^>]*>(.*?)</th>", table, re.I | re.S)]
        if not all(label in headers for label in ("Player", "Routes Run", "Rec. Yards", "YPRR")):
            continue
        players = []
        for row in re.findall(r"<tr\b[^>]*>(.*?)</tr>", table, re.I | re.S):
            cells = re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.I | re.S)
            if not cells:
                continue
            if len(cells) != len(headers):
                raise ValueError("Receiver table columns changed")
            identity = cells[headers.index("Player")]
            name = re.search(r'<span\b[^>]*class="[^"]*\bhidden md:inline\b[^"]*"[^>]*>([^<]+)</span>', identity)
            names = text(identity).split()
            aliases = TEAMS | set(TEAM_ALIASES)
            team = next((TEAM_ALIASES.get(token, token) for token in names if token in aliases), None)
            if not name or team not in TEAMS:
                raise ValueError("Receiver table player identity changed")
            routes_text = text(cells[headers.index("Routes Run")]).replace(",", "")
            yards_text = text(cells[headers.index("Rec. Yards")]).replace(",", "")
            if not routes_text.isdigit() or not re.fullmatch(r"-?\d+", yards_text):
                raise ValueError("Receiver table is missing route or yard totals")
            routes, yards = int(routes_text), int(yards_text)
            if routes <= 0:
                continue
            rate = yards / routes
            if abs(float(text(cells[headers.index("YPRR")])) - rate) > 0.015:
                raise ValueError("Published YPRR does not match the displayed yards and routes")
            players.append({"name": html.unescape(name[1]), "team": team, "routes": routes, "yards": yards})
        if len(players) < 32 or {p["team"] for p in players} != TEAMS:
            raise ValueError("Receiver table does not cover all 32 teams")
        keys = [(p["name"], p["team"]) for p in players]
        if len(set(keys)) != len(keys):
            raise ValueError("Receiver table repeats players")
        return updated.isoformat(), players
    raise ValueError("Public receiver table was not found")


def yprr_metric(page, season, games_by_team):
    updated, players = parse_receivers(page, season)
    if set(games_by_team) != TEAMS or any(n < 1 for n in games_by_team.values()):
        raise ValueError("Qualification requires a completed game count for every team")
    qualified = [p for p in players if p["routes"] >= 10 * games_by_team[p["team"]]]
    player = next((p for p in qualified if p["name"] == "Zay Flowers" and p["team"] == "BAL"), None)
    if player is None:
        return None
    # Compare exact ratios, not rounded display values. Equal ratios share a rank.
    rank = 1 + sum(p["yards"] * player["routes"] > player["yards"] * p["routes"] for p in qualified)
    minimum = 10 * games_by_team["BAL"]
    return {
        "source_label": "SumerSports", "source_url": SOURCE_URL,
        "period_label": "Updated " + datetime.fromisoformat(updated).astimezone(ZoneInfo("America/New_York")).strftime("%b. %d, %Y"),
        "label": "Flowers YPRR", "value": f"{player['yards'] / player['routes']:.2f}",
        "rank": rank, "rank_group": "WR", "season": season,
        "source_updated_at": updated, "routes": player["routes"], "receiving_yards": player["yards"],
        "qualified_receivers": len(qualified), "minimum_routes": minimum,
        "qualification": "10 routes per completed team game",
        "qualification_games": games_by_team,
        "sample_note": f"{player['routes']} routes · Min. {minimum} for BAL (10/team game)",
    }


def fetch_page():
    request = Request(SOURCE_URL, headers={"User-Agent": "DualEights-RavensDashboard/1.0"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def refresh_yprr(existing, season, games_by_team, fetch=fetch_page):
    stored = next((m for m in existing.get("unit_analytics", {}).get("Wide receivers", [])
                   if m.get("label") == "Flowers YPRR" and m.get("source_label") == "SumerSports"
                   and m.get("season") == season), None)
    try:
        fresh = yprr_metric(fetch(), season, games_by_team)
        if stored and fresh and fresh["source_updated_at"] < stored.get("source_updated_at", ""):
            return stored
        # A successfully parsed current table with Flowers below the minimum is
        # authoritative: do not retain an old qualified rank in that case.
        return fresh
    except Exception as error:
        print(f"SumerSports YPRR unavailable; keeping the last good value: {error}", file=sys.stderr)
        return stored
