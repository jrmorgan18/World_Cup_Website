#!/usr/bin/env python3
"""Build the Barcelona dashboard's objective snapshot.

The script uses ESPN's free, keyless soccer feeds: competition standings, team
schedules, per-match team statistics and team rosters. Every ranked metric is
calculated here from per-match team statistics so La Liga and Champions League
numbers stay in separate, comparable samples.

Per-match statistics are cached in scripts/cache/barcelona_match_stats.json so
daily runs only download matches that are new or recently completed. Editorial
judgments live in _data/barcelona_dashboard.yml and are never written here.

Usage:
  python scripts/update_barcelona_dashboard.py
  python scripts/update_barcelona_dashboard.py --as-of 2026-09-17
  python scripts/update_barcelona_dashboard.py --competition laliga

A failed download leaves the existing JSON intact.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "_data" / "barcelona_dashboard_stats.json"
CACHE_PATH = ROOT / "scripts" / "cache" / "barcelona_match_stats.json"

TEAM_ID = "83"
TEAM_NAME = "Barcelona"
SEASON = 2026
SEASON_LABEL = "2026-27"

SITE_API = "https://site.api.espn.com/apis/site/v2/sports/soccer"
SITE_V2_API = "https://site.api.espn.com/apis/v2/sports/soccer"
CORE_API = "https://sports.core.api.espn.com/v2/sports/soccer/leagues"

COMPETITIONS = {
    "laliga": {
        "slug": "esp.1",
        "label": "La Liga",
        "short_label": "La Liga",
        "rank_label": "La Liga rank",
        "table_label": "La Liga table",
        "matchday_label": "Matchday",
    },
    "ucl": {
        "slug": "uefa.champions",
        "label": "Champions League",
        "short_label": "UCL",
        "rank_label": "League-phase rank",
        "table_label": "League phase",
        "matchday_label": "Matchday",
    },
}

# Metric ids must stay in sync with _data/barcelona_dashboard.yml.
METRICS = {
    "blaugrana_index": {"direction": "higher", "source": "Dual Eights index from ESPN match statistics"},
    "points_per_match": {"direction": "higher", "source": "ESPN competition results"},
    "goal_difference": {"direction": "higher", "source": "ESPN competition results"},
    "xg_difference_per_match": {"direction": "higher", "source": "ESPN match statistics"},
    "goals_per_match": {"direction": "higher", "source": "ESPN match statistics"},
    "xg_per_match": {"direction": "higher", "source": "ESPN match statistics"},
    "big_chances_per_match": {"direction": "higher", "source": "ESPN match statistics"},
    "shot_conversion": {"direction": "higher", "source": "ESPN match statistics"},
    "goals_conceded_per_match": {"direction": "lower", "source": "ESPN match statistics"},
    "xga_per_match": {"direction": "lower", "source": "ESPN match statistics"},
    "clean_sheet_rate": {"direction": "higher", "source": "ESPN match statistics"},
    "box_shots_conceded_per_match": {"direction": "lower", "source": "ESPN match statistics"},
    "possession_pct": {"direction": "higher", "source": "ESPN match statistics"},
    "pass_accuracy": {"direction": "higher", "source": "ESPN match statistics"},
    "ppda": {"direction": "lower", "source": "ESPN match statistics"},
    "final_third_entries_per_match": {"direction": "higher", "source": "ESPN match statistics"},
}

INDEX_COMPONENTS = (
    ("xg_per_match", "higher"),
    ("xga_per_match", "lower"),
    ("goals_per_match", "higher"),
    ("goals_conceded_per_match", "lower"),
)

# Per-match team statistics kept in the cache.
MATCH_STAT_KEYS = (
    "expectedGoals",
    "expectedGoalsConceded",
    "possessionPct",
    "totalPasses",
    "accuratePasses",
    "totalShots",
    "shotsOnTarget",
    "bigChanceCreated",
    "finalThirdEntries",
    "penAreaEntries",
    "touchesInOppBox",
    "attemptsConcededIbox",
    "ppda",
    "possWonAtt3rd",
    "ballRecovery",
    "defensiveActions",
    "offsideProvoked",
    "totalTackles",
    "interceptions",
    "foulsCommitted",
    "yellowCards",
    "redCards",
    "saves",
    "goalsPrevented",
)

ROTATION_WINDOW_DAYS = 21
REQUEST_DELAY_SECONDS = 0.12

# ESPN's edge rejects custom User-Agent strings with a 403, so requests go out
# with urllib's default agent and identify themselves through Accept only.
REQUEST_HEADERS = {"Accept": "application/json"}


class UpdateError(RuntimeError):
    """Raised when the update cannot be completed safely."""


def fetch_json(url: str, attempts: int = 3, optional: bool = False):
    """Fetch JSON with retries. Returns None for optional resources that fail."""
    last_error = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers=REQUEST_HEADERS)
            with urlopen(request, timeout=45) as response:
                payload = json.loads(response.read().decode("utf-8"))
            time.sleep(REQUEST_DELAY_SECONDS)
            return payload
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(2 ** attempt)
    if optional:
        print(f"  ! optional fetch failed: {url} ({last_error})", file=sys.stderr)
        return None
    raise UpdateError(f"Could not fetch {url}: {last_error}")


def number(value, digits=None):
    """Coerce to a finite float, optionally rounded. Returns None when unusable."""
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return round(result, digits) if digits is not None else result


def as_int(value):
    """Whole numbers render as integers so templates never print 7.0."""
    result = number(value)
    if result is None:
        return None
    return int(round(result))


def safe_divide(numerator, denominator, digits=None):
    if not denominator:
        return None
    return number(numerator / denominator, digits)


def stat_values(payload) -> dict:
    """Flatten an ESPN statistics payload into {stat_name: float}."""
    values = {}
    if not payload:
        return values
    for category in payload.get("splits", {}).get("categories", []):
        for stat in category.get("stats", []):
            name = stat.get("name")
            if not name:
                continue
            value = stat.get("value")
            if value is None:
                value = stat.get("displayValue")
            parsed = number(value)
            if parsed is not None:
                values[name] = parsed
    return values


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {"version": 1, "matches": {}}
    try:
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "matches": {}}
    cache.setdefault("matches", {})
    return cache


def write_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def competition_standings(slug: str):
    """Return (ordered entries, team index) for a competition, or ([], {})."""
    payload = fetch_json(f"{SITE_V2_API}/{slug}/standings", optional=True)
    if not payload:
        return [], {}
    groups = payload.get("children") or [payload]
    entries = []
    for group in groups:
        entries.extend(group.get("standings", {}).get("entries", []))
    table = []
    index = {}
    for entry in entries:
        team = entry.get("team", {})
        stats = {stat.get("name"): stat for stat in entry.get("stats", [])}

        def stat_number(name):
            stat = stats.get(name)
            return number(stat.get("value") if stat else None)

        row = {
            "team_id": str(team.get("id")),
            "name": team.get("displayName"),
            "short_name": team.get("shortDisplayName"),
            "abbreviation": team.get("abbreviation"),
            "logo": team.get("logos", [{}])[0].get("href") if team.get("logos") else None,
            "rank": as_int(stat_number("rank")),
            "played": as_int(stat_number("gamesPlayed")),
            "wins": as_int(stat_number("wins")),
            "draws": as_int(stat_number("ties") if stat_number("ties") is not None else stat_number("draws")),
            "losses": as_int(stat_number("losses")),
            "goals_for": as_int(stat_number("pointsFor")),
            "goals_against": as_int(stat_number("pointsAgainst")),
            "goal_difference": as_int(stat_number("pointDifferential")),
            "points": as_int(stat_number("points")),
        }
        if row["goal_difference"] is None and row["goals_for"] is not None and row["goals_against"] is not None:
            row["goal_difference"] = row["goals_for"] - row["goals_against"]
        table.append(row)
        index[row["team_id"]] = row
    table.sort(key=lambda row: row["rank"] if row["rank"] is not None else 999)
    return table, index


def team_schedule(slug: str, team_id: str, fixtures: bool = False):
    """Return the raw events on a team's schedule."""
    url = f"{SITE_API}/{slug}/teams/{team_id}/schedule?season={SEASON}"
    if fixtures:
        url += "&fixture=true"
    payload = fetch_json(url, optional=True)
    if not payload:
        return []
    return payload.get("events", []) or []


def parse_event(event: dict, competition_key: str) -> dict | None:
    """Reduce an ESPN schedule event to the fields the dashboard needs."""
    competitions = event.get("competitions") or []
    if not competitions:
        return None
    competition = competitions[0]
    status = competition.get("status", {}).get("type", {}) or {}
    competitors = competition.get("competitors") or []
    if len(competitors) != 2:
        return None

    teams = {}
    for competitor in competitors:
        team = competitor.get("team", {})
        teams[competitor.get("homeAway")] = {
            "team_id": str(team.get("id")),
            "name": team.get("displayName"),
            "short_name": team.get("shortDisplayName"),
            "abbreviation": team.get("abbreviation"),
            "logo": team.get("logos", [{}])[0].get("href") if team.get("logos") else None,
            "score": as_int((competitor.get("score") or {}).get("value")
                            if isinstance(competitor.get("score"), dict) else competitor.get("score")),
            "winner": competitor.get("winner"),
        }
    if "home" not in teams or "away" not in teams:
        return None

    venue = (competition.get("venue") or {}).get("fullName")
    return {
        "event_id": str(event.get("id")),
        "competition": competition_key,
        "date": event.get("date"),
        "name": event.get("name"),
        "completed": bool(status.get("completed")),
        "state": status.get("state"),
        "status_detail": status.get("shortDetail") or status.get("detail"),
        "venue": venue,
        "home": teams["home"],
        "away": teams["away"],
    }


def collect_events(competition_key: str, slug: str, team_ids: list[str]) -> dict:
    """Union every completed event across a competition's teams, keyed by event id."""
    events = {}
    for team_id in team_ids:
        for raw in team_schedule(slug, team_id):
            event = parse_event(raw, competition_key)
            if event and event["completed"]:
                events[event["event_id"]] = event
    return events


def fetch_match_stats(slug: str, event_id: str, team_id: str) -> dict | None:
    url = (
        f"{CORE_API}/{slug}/events/{event_id}/competitions/{event_id}"
        f"/competitors/{team_id}/statistics"
    )
    payload = fetch_json(url, optional=True)
    if not payload:
        return None
    values = stat_values(payload)
    if not values:
        return None
    return {key: values[key] for key in MATCH_STAT_KEYS if key in values}


def fetch_match_minutes(slug: str, event_id: str, team_id: str) -> list[dict]:
    """Per-player minutes for one team in one match, derived from substitution clocks."""
    url = (
        f"{CORE_API}/{slug}/events/{event_id}/competitions/{event_id}"
        f"/competitors/{team_id}/roster"
    )
    payload = fetch_json(url, optional=True)
    if not payload:
        return []

    appearances = []
    for entry in payload.get("entries", []) or []:
        athlete = entry.get("athlete", {}) or {}
        player_id = str(entry.get("playerId") or athlete.get("id") or "").strip()
        if not player_id:
            continue
        starter = bool(entry.get("starter"))
        subbed_in = entry.get("subbedIn") or {}
        subbed_out = entry.get("subbedOut") or {}
        came_on = bool(subbed_in.get("didSub"))
        went_off = bool(subbed_out.get("didSub"))

        def clock_minutes(payload_clock):
            seconds = number((payload_clock or {}).get("clock", {}).get("value"))
            if seconds is None:
                return None
            return max(0.0, min(90.0, seconds / 60.0))

        if starter:
            minutes = clock_minutes(subbed_out) if went_off else 90.0
            if minutes is None:
                minutes = 90.0
        elif came_on:
            entered = clock_minutes(subbed_in)
            minutes = 90.0 - entered if entered is not None else 0.0
        else:
            minutes = 0.0

        appearances.append({
            "player_id": player_id,
            "minutes": round(minutes),
            "starter": starter,
            "played": starter or came_on,
        })
    return appearances


def ensure_match_cached(cache: dict, event: dict, slug: str, refresh: bool) -> bool:
    """Download and cache one match's team statistics. Returns True when cached."""
    event_id = event["event_id"]
    record = cache["matches"].get(event_id)
    if record and not refresh:
        return True

    home_id = event["home"]["team_id"]
    away_id = event["away"]["team_id"]
    home_stats = fetch_match_stats(slug, event_id, home_id)
    away_stats = fetch_match_stats(slug, event_id, away_id)
    if home_stats is None or away_stats is None:
        return record is not None

    record = {
        "event_id": event_id,
        "competition": event["competition"],
        "date": event["date"],
        "home_team": home_id,
        "away_team": away_id,
        "home_score": event["home"]["score"],
        "away_score": event["away"]["score"],
        "stats": {home_id: home_stats, away_id: away_stats},
    }

    if TEAM_ID in (home_id, away_id):
        minutes = fetch_match_minutes(slug, event_id, TEAM_ID)
        if minutes:
            record["barcelona_minutes"] = minutes

    cache["matches"][event_id] = record
    return True


def blank_totals() -> dict:
    return {
        "matches": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0.0,
        "goals_against": 0.0,
        "clean_sheets": 0,
        "xg": 0.0,
        "xga": 0.0,
        "shots": 0.0,
        "shots_on_target": 0.0,
        "big_chances": 0.0,
        "final_third_entries": 0.0,
        "box_shots_conceded": 0.0,
        "total_passes": 0.0,
        "accurate_passes": 0.0,
        "possession_sum": 0.0,
        "possession_matches": 0,
        "ppda_sum": 0.0,
        "ppda_matches": 0,
        "high_turnovers": 0.0,
        "recoveries": 0.0,
        "offsides_provoked": 0.0,
    }


def accumulate(totals: dict, stats: dict, goals_for, goals_against) -> None:
    totals["matches"] += 1
    if goals_for is not None and goals_against is not None:
        totals["goals_for"] += goals_for
        totals["goals_against"] += goals_against
        if goals_for > goals_against:
            totals["wins"] += 1
        elif goals_for == goals_against:
            totals["draws"] += 1
        else:
            totals["losses"] += 1
        if goals_against == 0:
            totals["clean_sheets"] += 1

    mapping = {
        "xg": "expectedGoals",
        "xga": "expectedGoalsConceded",
        "shots": "totalShots",
        "shots_on_target": "shotsOnTarget",
        "big_chances": "bigChanceCreated",
        "final_third_entries": "finalThirdEntries",
        "box_shots_conceded": "attemptsConcededIbox",
        "total_passes": "totalPasses",
        "accurate_passes": "accuratePasses",
        "high_turnovers": "possWonAtt3rd",
        "recoveries": "ballRecovery",
        "offsides_provoked": "offsideProvoked",
    }
    for key, stat_name in mapping.items():
        value = stats.get(stat_name)
        if value is not None:
            totals[key] += value

    possession = stats.get("possessionPct")
    if possession is not None:
        totals["possession_sum"] += possession
        totals["possession_matches"] += 1

    ppda = stats.get("ppda")
    if ppda is not None:
        totals["ppda_sum"] += ppda
        totals["ppda_matches"] += 1


def metrics_from_totals(totals: dict) -> dict:
    matches = totals["matches"]
    if not matches:
        return {}
    points = totals["wins"] * 3 + totals["draws"]
    return {
        "points_per_match": safe_divide(points, matches, 2),
        "goal_difference": number(totals["goals_for"] - totals["goals_against"]),
        "xg_difference_per_match": safe_divide(totals["xg"] - totals["xga"], matches, 2),
        "goals_per_match": safe_divide(totals["goals_for"], matches, 2),
        "xg_per_match": safe_divide(totals["xg"], matches, 2),
        "big_chances_per_match": safe_divide(totals["big_chances"], matches, 1),
        "shot_conversion": safe_divide(totals["goals_for"] * 100.0, totals["shots"], 1),
        "goals_conceded_per_match": safe_divide(totals["goals_against"], matches, 2),
        "xga_per_match": safe_divide(totals["xga"], matches, 2),
        "clean_sheet_rate": safe_divide(totals["clean_sheets"] * 100.0, matches, 1),
        "box_shots_conceded_per_match": safe_divide(totals["box_shots_conceded"], matches, 1),
        "possession_pct": safe_divide(totals["possession_sum"], totals["possession_matches"], 1),
        "pass_accuracy": safe_divide(totals["accurate_passes"] * 100.0, totals["total_passes"], 1),
        "ppda": safe_divide(totals["ppda_sum"], totals["ppda_matches"], 1),
        "final_third_entries_per_match": safe_divide(totals["final_third_entries"], matches, 1),
    }


def percentile(values: list[float], value: float, direction: str) -> float | None:
    """Percentile of a value within a population (100 = best for the direction)."""
    population = [item for item in values if item is not None]
    if len(population) < 2 or value is None:
        return None
    if direction == "lower":
        better = sum(1 for item in population if item > value)
    else:
        better = sum(1 for item in population if item < value)
    ties = sum(1 for item in population if item == value)
    return (better + 0.5 * (ties - 1)) / (len(population) - 1) * 100.0


def rank_of(values: list[float], value: float, direction: str) -> int | None:
    population = [item for item in values if item is not None]
    if not population or value is None:
        return None
    if direction == "lower":
        return sum(1 for item in population if item < value) + 1
    return sum(1 for item in population if item > value) + 1


def build_competition_metrics(team_metrics: dict[str, dict]) -> dict[str, dict]:
    """Add the composite index, then attach ranks for every team."""
    populations = {
        metric_id: [metrics.get(metric_id) for metrics in team_metrics.values()]
        for metric_id in METRICS
        if metric_id != "blaugrana_index"
    }

    for metrics in team_metrics.values():
        components = []
        for metric_id, direction in INDEX_COMPONENTS:
            score = percentile(populations[metric_id], metrics.get(metric_id), direction)
            if score is not None:
                components.append(score)
        metrics["blaugrana_index"] = (
            number(sum(components) / len(components), 1) if len(components) == len(INDEX_COMPONENTS) else None
        )
    populations["blaugrana_index"] = [metrics.get("blaugrana_index") for metrics in team_metrics.values()]

    ranked = {}
    for team_id, metrics in team_metrics.items():
        ranked[team_id] = {
            metric_id: {
                "value": metrics.get(metric_id),
                "rank": rank_of(populations[metric_id], metrics.get(metric_id), METRICS[metric_id]["direction"]),
                "source": METRICS[metric_id]["source"],
            }
            for metric_id in METRICS
        }
    return ranked


def match_summary(event: dict, perspective_id: str = TEAM_ID) -> dict:
    """Describe a match from Barcelona's point of view."""
    is_home = event["home"]["team_id"] == perspective_id
    us = event["home"] if is_home else event["away"]
    them = event["away"] if is_home else event["home"]
    result = None
    if event["completed"] and us["score"] is not None and them["score"] is not None:
        if us["score"] > them["score"]:
            result = "W"
        elif us["score"] == them["score"]:
            result = "D"
        else:
            result = "L"
    return {
        "event_id": event["event_id"],
        "competition": event["competition"],
        "date": event["date"],
        "completed": event["completed"],
        "status_detail": event["status_detail"],
        "location": "home" if is_home else "away",
        "venue": event.get("venue"),
        "opponent": them["name"],
        "opponent_short": them["short_name"],
        "opponent_abbr": them["abbreviation"],
        "opponent_id": them["team_id"],
        "opponent_logo": them["logo"],
        "goals_for": us["score"],
        "goals_against": them["score"],
        "result": result,
    }


def attach_match_detail(summary: dict, cache: dict) -> dict:
    """Add cached team statistics for both sides of a completed match."""
    record = cache["matches"].get(summary["event_id"])
    if not record:
        return summary
    our_stats = record["stats"].get(TEAM_ID, {})
    their_id = record["away_team"] if record["home_team"] == TEAM_ID else record["home_team"]
    their_stats = record["stats"].get(their_id, {})
    summary["detail"] = {
        "xg": number(our_stats.get("expectedGoals"), 2),
        "xga": number(our_stats.get("expectedGoalsConceded"), 2),
        "possession": number(our_stats.get("possessionPct"), 1),
        "shots": as_int(our_stats.get("totalShots")),
        "shots_on_target": as_int(our_stats.get("shotsOnTarget")),
        "big_chances": as_int(our_stats.get("bigChanceCreated")),
        "ppda": number(our_stats.get("ppda"), 1),
        "final_third_entries": as_int(our_stats.get("finalThirdEntries")),
        "touches_in_box": as_int(our_stats.get("touchesInOppBox")),
        "high_turnovers": as_int(our_stats.get("possWonAtt3rd")),
        "opponent_xg": number(their_stats.get("expectedGoals"), 2),
        "opponent_shots": as_int(their_stats.get("totalShots")),
        "opponent_possession": number(their_stats.get("possessionPct"), 1),
    }
    return summary


def build_snapshots(competition_key: str, events: list[dict], cache: dict, team_ids: list[str]) -> list[dict]:
    """Rebuild the matchday-by-matchday history so week-over-week deltas are real."""
    config = COMPETITIONS[competition_key]
    our_events = sorted(
        [event for event in events if TEAM_ID in (event["home"]["team_id"], event["away"]["team_id"])],
        key=lambda event: event["date"],
    )
    if not our_events:
        return []

    snapshots = []
    previous_id = None
    for index, event in enumerate(our_events, start=1):
        # A snapshot covers every match played before Barcelona's next fixture, so
        # each matchday is ranked against a complete round rather than the partial
        # table that existed at Barcelona's own kickoff. The last snapshot is open
        # ended and therefore reflects the competition as it stands today.
        cutoff = our_events[index]["date"] if index < len(our_events) else None
        totals = {team_id: blank_totals() for team_id in team_ids}
        for candidate in events:
            if cutoff is not None and candidate["date"] >= cutoff:
                continue
            record = cache["matches"].get(candidate["event_id"])
            if not record:
                continue
            for side, opposite in (("home_team", "away_team"), ("away_team", "home_team")):
                team_id = record[side]
                if team_id not in totals:
                    continue
                goals_for = record["home_score"] if side == "home_team" else record["away_score"]
                goals_against = record["away_score"] if side == "home_team" else record["home_score"]
                accumulate(totals[team_id], record["stats"].get(team_id, {}), goals_for, goals_against)

        team_metrics = {team_id: metrics_from_totals(value) for team_id, value in totals.items()}
        team_metrics = {team_id: metrics for team_id, metrics in team_metrics.items() if metrics}
        if TEAM_ID not in team_metrics:
            continue
        ranked = build_competition_metrics(team_metrics)

        our_totals = totals[TEAM_ID]
        record_label = f"{our_totals['wins']}-{our_totals['draws']}-{our_totals['losses']}"
        snapshot_id = f"{competition_key}-md-{index:02d}"
        snapshots.append({
            "id": snapshot_id,
            "matchday": index,
            "label": f"{config['matchday_label']} {index}",
            "previous_snapshot": previous_id,
            "date": event["date"],
            "sample_note": f"{index} {config['label']} {'match' if index == 1 else 'matches'} played",
            "record": record_label,
            "points": our_totals["wins"] * 3 + our_totals["draws"],
            "teams_ranked": len(team_metrics),
            "metrics": ranked[TEAM_ID],
        })
        previous_id = snapshot_id
    return snapshots


def build_squad(slug_by_competition: dict[str, str], cache: dict, our_events: list[dict], as_of: date) -> dict:
    """Per-player season output, availability and rolling minutes load."""
    players: dict[str, dict] = {}
    injuries = []

    for competition_key, slug in slug_by_competition.items():
        payload = fetch_json(f"{SITE_API}/{slug}/teams/{TEAM_ID}/roster", optional=True)
        if not payload:
            continue
        for athlete in payload.get("athletes", []) or []:
            player_id = str(athlete.get("id"))
            values = stat_values(athlete.get("statistics"))
            position = athlete.get("position", {}) or {}
            player = players.setdefault(player_id, {
                "player_id": player_id,
                "name": athlete.get("displayName"),
                "short_name": athlete.get("shortName"),
                "jersey": athlete.get("jersey"),
                "position": position.get("displayName"),
                "position_abbr": position.get("abbreviation"),
                "citizenship": athlete.get("citizenship"),
                "age": as_int(athlete.get("age")),
                "headshot": (athlete.get("headshot") or {}).get("href"),
                "competitions": {},
                "minutes_total": 0,
                "starts_total": 0,
                "appearances_total": 0,
            })
            if not player.get("headshot") and (athlete.get("headshot") or {}).get("href"):
                player["headshot"] = athlete["headshot"]["href"]

            player["competitions"][competition_key] = {
                "appearances": as_int(values.get("appearances")),
                "goals": as_int(values.get("totalGoals")),
                "assists": as_int(values.get("goalAssists")),
                "shots": as_int(values.get("totalShots")),
                "shots_on_target": as_int(values.get("shotsOnTarget")),
                "yellow_cards": as_int(values.get("yellowCards")),
                "red_cards": as_int(values.get("redCards")),
                "saves": as_int(values.get("saves")),
                "goals_conceded": as_int(values.get("goalsConceded")),
                "clean_sheets": as_int(values.get("cleanSheet")),
                "minutes": 0,
                "starts": 0,
            }

            for injury in athlete.get("injuries", []) or []:
                detail = injury.get("details") or {}
                injuries.append({
                    "player_id": player_id,
                    "player": athlete.get("displayName"),
                    "position": position.get("abbreviation"),
                    "status": injury.get("status"),
                    "type": detail.get("type") or injury.get("type"),
                    "detail": detail.get("detail"),
                    "side": detail.get("side"),
                    "return_date": detail.get("returnDate"),
                    "date": injury.get("date"),
                    "source": "ESPN team roster feed",
                })

    # Minutes come from per-match rosters, which are the only per-competition source.
    window_start = as_of - timedelta(days=ROTATION_WINDOW_DAYS)
    window_minutes: dict[str, dict] = {}
    window_matches = 0

    for event in our_events:
        record = cache["matches"].get(event["event_id"])
        if not record or not record.get("barcelona_minutes"):
            continue
        event_date = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).date()
        in_window = window_start <= event_date <= as_of
        if in_window:
            window_matches += 1
        for appearance in record["barcelona_minutes"]:
            player_id = appearance["player_id"]
            player = players.get(player_id)
            minutes = appearance.get("minutes") or 0
            if player:
                competition = player["competitions"].setdefault(event["competition"], {"minutes": 0, "starts": 0})
                competition["minutes"] = competition.get("minutes", 0) + minutes
                if appearance.get("starter"):
                    competition["starts"] = competition.get("starts", 0) + 1
                player["minutes_total"] += minutes
                if appearance.get("starter"):
                    player["starts_total"] += 1
                if appearance.get("played"):
                    player["appearances_total"] += 1
            if in_window:
                bucket = window_minutes.setdefault(player_id, {"minutes": 0, "starts": 0, "matches": 0})
                bucket["minutes"] += minutes
                if appearance.get("starter"):
                    bucket["starts"] += 1
                if appearance.get("played"):
                    bucket["matches"] += 1

    available_minutes = window_matches * 90
    rotation_players = []
    for player_id, bucket in window_minutes.items():
        player = players.get(player_id)
        if not player or not bucket["minutes"]:
            continue
        rotation_players.append({
            "player_id": player_id,
            "name": player["name"],
            "position_abbr": player["position_abbr"],
            "minutes": bucket["minutes"],
            "starts": bucket["starts"],
            "matches": bucket["matches"],
            "share": safe_divide(bucket["minutes"] * 100.0, available_minutes, 1),
        })
    rotation_players.sort(key=lambda item: item["minutes"], reverse=True)

    # Templates cannot sum across competitions, so totals are precomputed here.
    for player in players.values():
        totals = {key: 0 for key in ("appearances", "goals", "assists", "shots", "yellow_cards", "red_cards", "saves")}
        for competition in player["competitions"].values():
            for key in totals:
                totals[key] += competition.get(key) or 0
        totals["minutes"] = player["minutes_total"]
        totals["starts"] = player["starts_total"]
        totals["goal_contributions"] = totals["goals"] + totals["assists"]
        totals["minutes_per_contribution"] = (
            as_int(player["minutes_total"] / totals["goal_contributions"])
            if totals["goal_contributions"] else None
        )
        player["totals"] = totals

    squad = sorted(
        players.values(),
        key=lambda player: (-player["minutes_total"], player["name"] or ""),
    )
    return {
        "players": squad,
        "injuries": injuries,
        "rotation": {
            "window_days": ROTATION_WINDOW_DAYS,
            "window_start": window_start.isoformat(),
            "window_end": as_of.isoformat(),
            "matches_in_window": window_matches,
            "available_minutes": available_minutes,
            "players": rotation_players,
        },
    }


def build_congestion(all_events: list[dict], upcoming: list[dict], as_of: date) -> dict:
    """Fixture density behind and ahead, with the shortest rest gaps."""
    def event_date(event):
        return datetime.fromisoformat(event["date"].replace("Z", "+00:00")).date()

    played = [event for event in all_events if event["completed"]]
    window_start = as_of - timedelta(days=ROTATION_WINDOW_DAYS)
    recent = [event for event in played if window_start <= event_date(event) <= as_of]
    next_14 = [event for event in upcoming if as_of <= event_date(event) <= as_of + timedelta(days=14)]
    next_30 = [event for event in upcoming if as_of <= event_date(event) <= as_of + timedelta(days=30)]

    def gaps(events):
        dates = sorted({event_date(event) for event in events})
        return [(dates[index] - dates[index - 1]).days for index in range(1, len(dates))]

    recent_gaps = gaps(recent)
    upcoming_gaps = gaps([event for event in next_30])

    matches_per_week = safe_divide(len(recent) * 7.0, ROTATION_WINDOW_DAYS, 2) or 0
    if matches_per_week >= 2.0:
        load_level = "Heavy"
    elif matches_per_week >= 1.4:
        load_level = "Moderate"
    else:
        load_level = "Light"

    return {
        "window_days": ROTATION_WINDOW_DAYS,
        "matches_last_window": len(recent),
        "matches_per_week": matches_per_week,
        "load_level": load_level,
        "shortest_rest_recent": min(recent_gaps) if recent_gaps else None,
        "average_rest_recent": number(sum(recent_gaps) / len(recent_gaps), 1) if recent_gaps else None,
        "matches_next_14_days": len(next_14),
        "matches_next_30_days": len(next_30),
        "shortest_rest_upcoming": min(upcoming_gaps) if upcoming_gaps else None,
        "recent": [
            {
                "date": event["date"],
                "competition": event["competition"],
                "opponent": (event["away"] if event["home"]["team_id"] == TEAM_ID else event["home"])["short_name"],
            }
            for event in sorted(recent, key=lambda item: item["date"])
        ],
        "upcoming": [
            {
                "date": event["date"],
                "competition": event["competition"],
                "opponent": (event["away"] if event["home"]["team_id"] == TEAM_ID else event["home"])["short_name"],
                "location": "home" if event["home"]["team_id"] == TEAM_ID else "away",
            }
            for event in sorted(next_30, key=lambda item: item["date"])
        ],
    }


def build(as_of: date, competitions: list[str], refresh_recent: int) -> dict:
    cache = load_cache()
    output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "as_of": as_of.isoformat(),
        "season": SEASON,
        "season_label": SEASON_LABEL,
        "team": {"id": TEAM_ID, "name": TEAM_NAME},
        "competitions": {},
    }

    all_our_events: list[dict] = []
    all_upcoming: list[dict] = []
    slug_by_competition = {}

    for competition_key in competitions:
        config = COMPETITIONS[competition_key]
        slug = config["slug"]
        slug_by_competition[competition_key] = slug
        print(f"[{config['label']}] standings")
        table, table_index = competition_standings(slug)
        team_ids = [row["team_id"] for row in table] or [TEAM_ID]

        print(f"[{config['label']}] schedules for {len(team_ids)} teams")
        events = collect_events(competition_key, slug, team_ids)
        ordered_events = sorted(events.values(), key=lambda event: event["date"])

        recent_ids = {event["event_id"] for event in ordered_events[-refresh_recent:]} if refresh_recent else set()
        new_matches = 0
        for event in ordered_events:
            already_cached = event["event_id"] in cache["matches"]
            if already_cached and event["event_id"] not in recent_ids:
                continue
            if ensure_match_cached(cache, event, slug, refresh=True) and not already_cached:
                new_matches += 1
        print(f"[{config['label']}] {len(ordered_events)} completed matches, {new_matches} newly cached")

        our_events = [
            event for event in ordered_events
            if TEAM_ID in (event["home"]["team_id"], event["away"]["team_id"])
        ]
        all_our_events.extend(our_events)

        upcoming_raw = [
            parse_event(raw, competition_key)
            for raw in team_schedule(slug, TEAM_ID, fixtures=True)
        ]
        upcoming = sorted(
            [event for event in upcoming_raw if event and not event["completed"]],
            key=lambda event: event["date"],
        )
        all_upcoming.extend(upcoming)

        snapshots = build_snapshots(competition_key, ordered_events, cache, team_ids)
        recent_matches = [
            attach_match_detail(match_summary(event), cache)
            for event in sorted(our_events, key=lambda item: item["date"], reverse=True)
        ]
        standing_row = table_index.get(TEAM_ID)
        form = [match["result"] for match in reversed(recent_matches[:5]) if match["result"]]

        output["competitions"][competition_key] = {
            "key": competition_key,
            "label": config["label"],
            "short_label": config["short_label"],
            "rank_label": config["rank_label"],
            "table_label": config["table_label"],
            "slug": slug,
            "teams_ranked": snapshots[-1]["teams_ranked"] if snapshots else len(team_ids),
            "current_snapshot": snapshots[-1]["id"] if snapshots else None,
            "snapshots": snapshots,
            "table": table,
            "standing": standing_row,
            "form": form,
            "matches": recent_matches,
            "last_match": recent_matches[0] if recent_matches else None,
            "next_match": match_summary(upcoming[0]) if upcoming else None,
            "fixtures": [match_summary(event) for event in upcoming[:6]],
        }

    print("[squad] rosters, minutes and availability")
    squad = build_squad(slug_by_competition, cache, sorted(all_our_events, key=lambda e: e["date"]), as_of)
    output["squad"] = squad["players"]
    output["injuries"] = squad["injuries"]
    output["rotation"] = squad["rotation"]
    output["congestion"] = build_congestion(all_our_events, all_upcoming, as_of)

    completed = sorted(all_our_events, key=lambda event: event["date"], reverse=True)
    upcoming_all = sorted(all_upcoming, key=lambda event: event["date"])
    overall = {"wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}
    for event in completed:
        summary = match_summary(event)
        if summary["result"] == "W":
            overall["wins"] += 1
        elif summary["result"] == "D":
            overall["draws"] += 1
        elif summary["result"] == "L":
            overall["losses"] += 1
        if summary["goals_for"] is not None:
            overall["goals_for"] += int(summary["goals_for"])
            overall["goals_against"] += int(summary["goals_against"])

    output["all_competitions"] = {
        "record": f"{overall['wins']}-{overall['draws']}-{overall['losses']}",
        "wins": overall["wins"],
        "draws": overall["draws"],
        "losses": overall["losses"],
        "goals_for": overall["goals_for"],
        "goals_against": overall["goals_against"],
        "matches_played": len(completed),
        "form": [match_summary(event)["result"] for event in list(reversed(completed[:6])) ],
        "last_match": attach_match_detail(match_summary(completed[0]), cache) if completed else None,
        "next_match": match_summary(upcoming_all[0]) if upcoming_all else None,
        "fixtures": [match_summary(event) for event in upcoming_all[:8]],
        "results": [attach_match_detail(match_summary(event), cache) for event in completed[:10]],
    }

    write_cache(cache)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--as-of", default=None, help="Override today's date (YYYY-MM-DD)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path to the generated JSON")
    parser.add_argument(
        "--competition",
        action="append",
        choices=sorted(COMPETITIONS),
        help="Limit the update to one competition (repeatable)",
    )
    parser.add_argument(
        "--refresh-recent",
        type=int,
        default=4,
        help="Re-download the most recent N matches per competition to pick up corrections",
    )
    args = parser.parse_args()

    as_of = date.fromisoformat(args.as_of) if args.as_of else datetime.now(timezone.utc).date()
    competitions = args.competition or list(COMPETITIONS)

    try:
        payload = build(as_of, competitions, args.refresh_recent)
    except UpdateError as error:
        print(f"Update failed: {error}", file=sys.stderr)
        print("The existing dashboard data was left unchanged.", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        display_path = output_path.resolve().relative_to(ROOT)
    except ValueError:
        display_path = output_path
    print(f"Wrote {display_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
