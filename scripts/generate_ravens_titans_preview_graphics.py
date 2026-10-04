#!/usr/bin/env python3
"""Build the Week 4 preview's branded SVGs from a frozen Week 3 sample.

Run from any directory with pandas/pyarrow installed. Shared nflverse filtering
and ranking helpers match the Week 2 preview; no dashboard data is changed.
Official counting stats: Titans Week 4 game release, pp. 5, 85–87.
Personnel frequency: Sharp's public table as published October 3, 2026.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import generate_ravens_saints_matchup_visual as dna

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/images/ravens/titans-week-four-2026"
GAME_RELEASE = "https://static.clubs.nfl.com/image/upload/titans/l8phsolqmz7ogquqcmcx"
PERSONNEL = "https://www.sharpfootballanalysis.com/stats-nfl/nfl-offensive-personnel/"
WHITE, GOLD, MUTED, PURPLE = "#f7f4fb", "#e8bc55", "#cfc8d5", "#9b6ee6"


def text(x, y, value, size=24, fill=WHITE, weight=600, anchor="start"):
    return dna.text(x, y, str(value), size, fill, weight=weight, anchor=anchor)


def card(x, y, w, h):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="#17131d" stroke="#49315f" stroke-width="2"/>'


def frame(title, subtitle, body, description, footer, height=720):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{dna.escape(title)}</title><desc id="desc">{dna.escape(description)}</desc>',
        f'<rect width="1200" height="{height}" fill="#09080c"/>',
        '<rect width="1200" height="130" fill="#1d1427"/><rect width="1200" height="8" fill="#7c4dc4"/>',
        text(50, 43, "DUAL EIGHTS · WEEK 4", 18, PURPLE, 800),
        text(50, 85, title, 36, WHITE, 800),
        text(50, 115, subtitle, 21, MUTED),
        body,
        text(50, height - 25, footer, 17, MUTED),
        "</svg>\n",
    ])


def write(name, svg):
    (OUT / f"ravens-titans-{name}.svg").write_text(svg, encoding="utf-8")


def overview():
    # Counting stats verified in the official game release, not scraped rankings.
    body = ""
    for x, team, record, yards, points in [
        (50, "THE RAVENS", "2–1", "398.7", "30.7"),
        (615, "TITANS", "0–3", "249.3", "12.3"),
    ]:
        body += card(x, 160, 535, 225)
        body += text(x + 25, 204, team, 27, GOLD, 800) + text(x + 510, 204, record, 30, WHITE, 800, "end")
        body += text(x + 25, 266, yards, 44, WHITE, 800) + text(x + 270, 266, points, 44, WHITE, 800)
        body += text(x + 25, 305, "Yards / game", 24) + text(x + 270, 305, "Points / game", 24)
        body += text(x + 25, 353, "OFFENSE · FIRST THREE GAMES", 18, PURPLE, 800)
    for i, (value, label, detail) in enumerate([
        ("6", "Henry rushing TDs", "The run threat is real"),
        ("3.6", "Titans YPC allowed", "Tennessee's run-defense test"),
        ("19.7", "Titans points allowed", "Per game · not a typical 0–3 defense"),
    ]):
        x = 50 + i * 375
        body += card(x, 420, 350, 210) + text(x + 25, 482, value, 48, GOLD, 800)
        body += text(x + 25, 527, label, 24, WHITE, 800)
        # Split the longest explanatory line deliberately for mobile readability.
        if i == 2:
            body += text(x + 25, 568, "Per game · not a typical", 21, MUTED)
            body += text(x + 25, 597, "0–3 defense", 21, MUTED)
        else:
            body += text(x + 25, 568, detail, 21, MUTED)
    write("at-a-glance-2026", frame(
        "RAVENS vs. TITANS", "Sunday, October 4 · 1:00 PM ET · M&T Bank Stadium · CBS", body,
        "Through Week 3: Ravens 2–1, 398.7 yards and 30.7 points per game; Titans 0–3, 249.3 yards and 12.3 points per game. Henry has six rushing touchdowns. Tennessee allows 3.6 yards per carry and 19.7 points per game.",
        "SOURCE: TITANS WEEK 4 GAME RELEASE · THROUGH WEEK 3 · THREE-GAME SAMPLE"))


def matchup(units, ranks):
    # Eight execution measures, each explicitly ranked #1 best for its unit.
    metrics = dna.METRICS[:8]
    body = ""
    for y, kicker, a, a_side, b, b_side in [
        (160, "WHEN THE RAVENS HAVE THE BALL", "BAL", "offense", "TEN", "defense"),
        (800, "WHEN THE TITANS HAVE THE BALL", "TEN", "offense", "BAL", "defense"),
    ]:
        body += card(50, y, 1100, 610)
        body += text(75, y + 35, kicker, 20, PURPLE, 800)
        body += text(75, y + 75, f"{dna.TEAMS[a].upper()} {a_side.upper()}", 27, WHITE, 800)
        body += text(1125, y + 75, f"{dna.TEAMS[b].upper()} {b_side.upper()}", 27, WHITE, 800, "end")
        for i, metric in enumerate(metrics):
            row_y = y + 100 + i * 60
            if i % 2 == 0:
                body += f'<rect x="52" y="{row_y}" width="1096" height="60" fill="#201929"/>'
            for x, team, side in [(75, a, a_side), (835, b, b_side)]:
                rank = ranks[side][team][metric.key]
                fill, ink = dna.rank_color(rank, True)
                body += text(x, row_y + 40, dna.format_value(units[side][team][metric.key], metric.format), 29, WHITE, 800)
                body += f'<rect x="{x + 198}" y="{row_y + 13}" width="86" height="35" rx="17" fill="{fill}"/>'
                body += text(x + 241, row_y + 38, f"#{rank}", 23, ink, 800, "middle")
            body += text(600, row_y + 39, metric.label.replace("Completion pct. over expected", "Completion over expected"), 23, WHITE, 700, "middle")
    body += text(50, 1440, "EPA = expected points added · Success = a play with positive EPA", 20, MUTED)
    body += text(50, 1471, "Explosive = 10+ rush yards / 20+ pass yards · Defense values are opponent production", 20, MUTED)
    desc = "League-ranked comparison through Week 3. " + " ".join(
        f"{dna.TEAMS[t]} {s}: " + "; ".join(f"{m.label} {dna.format_value(units[s][t][m.key], m.format)}, rank {ranks[s][t][m.key]}" for m in metrics)
        for s, t in [("offense", "BAL"), ("defense", "TEN"), ("offense", "TEN"), ("defense", "BAL")]
    )
    write("matchup-dna", frame("RAVENS × TITANS: MATCHUP DNA", "2026 through Week 3 · League ranks: #1 best · Gold = top eight", body, desc,
        "SOURCE: NFLVERSE PLAY-BY-PLAY · SAME FILTERS AS WEEK 2 PREVIEW · THREE-GAME SAMPLE", 1530))


def passing_opportunity(units):
    defense = units["defense"]["TEN"]
    body = card(50, 160, 1100, 285)
    body += text(80, 205, "TITANS DEFENSE: EPA ALLOWED PER PLAY", 26, WHITE, 800)
    body += text(80, 239, "Positive values favor the opposing offense; negative values favor the defense.", 22, MUTED)
    # Common signed axis. Negative is left of zero; positive is right of zero.
    baseline, scale = 660, 950
    body += f'<line x1="{baseline}" y1="263" x2="{baseline}" y2="410" stroke="#cfc8d5" stroke-width="2"/>'
    body += text(baseline, 431, "0", 20, MUTED, anchor="middle")
    for y, label, key, color in [(285, "Rush", "rush_epa", PURPLE), (362, "Pass", "pass_epa", GOLD)]:
        value = defense[key]
        end = baseline + value * scale
        body += text(80, y + 22, label, 29, WHITE, 800)
        body += f'<rect x="{min(baseline, end):.1f}" y="{y}" width="{abs(value * scale):.1f}" height="30" rx="4" fill="{color}"/>'
        body += text(1075, y + 25, f"{value:+.2f}", 32, color, 800, "end")
    for x, value, label, detail in [
        (50, "55%", "Ravens 2+ TE usage", "Sharp's all-play personnel table"),
        (615, "71.1%", "Completions allowed by TEN", "59 completions on 83 attempts"),
    ]:
        body += card(x, 480, 535, 170) + text(x + 25, 533, value, 44, GOLD, 800)
        body += text(x + 25, 578, label, 25, WHITE, 800) + text(x + 25, 617, detail, 22, MUTED)
    write("passing-opportunity-2026", frame("RUN THREAT. PASSING OPPORTUNITY.", "Why heavy personnel can matter even when Henry is not getting the ball", body,
        f"Titans EPA allowed per rush is {defense['rush_epa']:+.2f}, versus {defense['pass_epa']:+.2f} per pass. The Ravens use two or more tight ends on 55 percent of plays in Sharp's public table. Tennessee allows a 71.1 percent completion rate.",
        "SOURCES: NFLVERSE · SHARP PERSONNEL TABLE · TITANS GAME RELEASE · THROUGH WEEK 3"))


def key_matchups():
    body = ""
    for i, (heading, value, label, line1, line2) in enumerate([
        ("Ioane vs. Simmons", "15", "Simmons pressures", "Two sacks through three games.", "A rookie center faces the Titans' disruptor."),
        ("Make Ward win it", "5.7", "Ward yards / attempt", "504 passing yards on 88 attempts.", "Keep Tennessee in obvious passing downs."),
        ("Finish the coverage rep", "123", "Tate receiving yards", "13 catches on 20 targets through Week 3.", "Don't let short completions become explosives."),
    ]):
        y = 160 + i * 180
        body += card(50, y, 1100, 158)
        body += text(80, y + 61, value, 44, GOLD, 800)
        body += text(80, y + 101, label, 23, MUTED)
        body += text(455, y + 42, heading, 30, WHITE, 800)
        body += text(455, y + 86, line1, 24, MUTED)
        body += text(455, y + 127, line2, 23, WHITE)
    write("key-matchups-2026", frame("THREE MATCHUPS THAT DECIDE IT", "Protection inside · Difficult throws · Sound tackling", body,
        "Jeffery Simmons has 15 pressures and two sacks. Cam Ward averages 5.7 yards per attempt, with 504 yards on 88 attempts. Carnell Tate has 13 receptions for 123 yards on 20 targets.",
        "SOURCE: TITANS WEEK 4 GAME RELEASE · THROUGH WEEK 3 · THREE-GAME SAMPLE", 760))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pbp = pd.read_parquet(dna.PBP_URL.format(season=2026))
    plays = dna.eligible_plays(pbp, 3)
    assert plays["week"].max() == 3
    assert plays["posteam"].nunique() == 32
    for team in ("BAL", "TEN"):
        assert plays.loc[plays["posteam"] == team, "game_id"].nunique() == 3
    units = {side: dna.league_units(plays, side) for side in ("offense", "defense")}
    ranks = {side: dna.ranked_units(units[side], side) for side in units}
    dna.TEAMS = {"BAL": "Ravens", "TEN": "Titans"}
    overview()
    matchup(units, ranks)
    passing_opportunity(units)
    key_matchups()
    audit = {
        "season": 2026, "through_week": 3, "matchup_week": 4,
        "qualifying_plays": len(plays),
        "sources": {"play_by_play": dna.PBP_URL.format(season=2026), "game_release": GAME_RELEASE, "personnel": PERSONNEL},
        "definitions": {"explosive": "10+ yards rushing; 20+ yards passing", "success": "EPA > 0", "rank": "Minimum rank, #1 best; defense lower is better", "sample": "REG weeks 1–3, run/pass, no kneels/spikes/two-point attempts/deleted/aborted plays; EPA must exist"},
        "teams": {team: {side: {"values": units[side][team], "ranks": ranks[side][team]} for side in units} for team in ("BAL", "TEN")},
        "reported_stats": {"BAL": {"record": "2-1", "net_yards": 1196, "points": 92, "henry_rush_td": 6, "two_plus_te_pct": 55}, "TEN": {"record": "0-3", "net_yards": 748, "points": 37, "points_allowed": 59, "rush_ypc_allowed": 3.6, "completions_allowed": 59, "attempts_faced": 83, "simmons_pressures": 15, "simmons_sacks": 2, "ward_pass_yards": 504, "ward_attempts": 88, "tate_catches": 13, "tate_yards": 123, "tate_targets": 20}},
    }
    (OUT / "preview-stat-sources.json").write_text(json.dumps(audit, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Generated four graphics from {len(plays)} Week 1–3 qualifying plays.")
    print(json.dumps(audit["teams"], indent=2))


if __name__ == "__main__":
    main()
