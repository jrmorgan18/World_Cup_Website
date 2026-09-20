#!/usr/bin/env python3
"""Generate the Ravens–Saints Week 2 matchup graphic from nflverse play-by-play.

The visual intentionally uses a different layout and design language from the
editorial reference. Values and league ranks are calculated from completed
Week 1 games in the free nflverse 2026 play-by-play release.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pandas as pd


PBP_URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.parquet"
DEFAULT_OUTPUT = Path("assets/images/ravens/saints-week-two-2026/ravens-saints-matchup-dna.svg")
TEAMS = {"BAL": "Ravens", "NO": "Saints"}


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    format: str
    performance: bool = True


METRICS = [
    Metric("epa", "EPA / play", "signed2"),
    Metric("success", "Success rate", "pct1"),
    Metric("early_epa", "Early-down EPA / play", "signed2"),
    Metric("pass_epa", "Pass EPA / play", "signed2"),
    Metric("rush_epa", "Rush EPA / play", "signed2"),
    Metric("explosive", "Explosive-play rate", "pct1"),
    Metric("cpoe", "Completion pct. over expected", "signed_pct1"),
    Metric("third_down", "Third-down conversion", "pct1"),
    Metric("pass_oe", "Pass rate over expected", "signed_pct1", False),
    Metric("no_huddle", "No-huddle rate", "pct1", False),
]


def eligible_plays(pbp: pd.DataFrame, week: int) -> pd.DataFrame:
    plays = pbp[
        (pbp["season_type"] == "REG")
        & (pbp["week"] <= week)
        & pbp["play_type"].isin(["run", "pass"])
        & pbp["epa"].notna()
        & (pbp["qb_kneel"].fillna(0) != 1)
        & (pbp["qb_spike"].fillna(0) != 1)
        & (pbp["two_point_attempt"].fillna(0) != 1)
        & (pbp["play_deleted"].fillna(0) != 1)
        & (pbp["aborted_play"].fillna(0) != 1)
    ].copy()
    plays["explosive"] = (
        ((plays["play_type"] == "run") & (plays["yards_gained"] >= 10))
        | ((plays["play_type"] == "pass") & (plays["yards_gained"] >= 20))
    )
    return plays


def unit_values(rows: pd.DataFrame) -> dict[str, float]:
    early = rows[rows["down"].isin([1, 2])]
    passes = rows[rows["play_type"] == "pass"]
    rushes = rows[rows["play_type"] == "run"]
    third = rows[(rows["third_down_converted"].fillna(0) == 1) | (rows["third_down_failed"].fillna(0) == 1)]
    return {
        "epa": rows["epa"].mean(),
        "success": rows["success"].mean() * 100,
        "early_epa": early["epa"].mean(),
        "pass_epa": passes["epa"].mean(),
        "rush_epa": rushes["epa"].mean(),
        "explosive": rows["explosive"].mean() * 100,
        "cpoe": passes["cpoe"].mean(),
        "third_down": third["third_down_converted"].mean() * 100,
        "pass_oe": rows["pass_oe"].mean(),
        "no_huddle": rows["no_huddle"].mean() * 100,
    }


def league_units(plays: pd.DataFrame, side: str) -> dict[str, dict[str, float]]:
    column = "posteam" if side == "offense" else "defteam"
    return {team: unit_values(rows) for team, rows in plays.groupby(column) if pd.notna(team)}


def ranked_units(units: dict[str, dict[str, float]], side: str) -> dict[str, dict[str, int]]:
    rankings: dict[str, dict[str, int]] = {team: {} for team in units}
    for metric in METRICS:
        values = pd.Series({team: row[metric.key] for team, row in units.items()}).dropna()
        if metric.performance:
            ascending = side == "defense"
        else:
            ascending = False
        ranks = values.rank(method="min", ascending=ascending)
        for team, rank in ranks.items():
            rankings[team][metric.key] = int(rank)
    return rankings


def format_value(value: float, style: str) -> str:
    if pd.isna(value):
        return "—"
    if style == "signed2":
        return f"{value:+.2f}"
    if style == "signed_pct1":
        return f"{value:+.1f}%"
    if style == "pct1":
        return f"{value:.1f}%"
    return f"{value:.1f}"


def rank_color(rank: int, performance: bool) -> tuple[str, str]:
    if not performance:
        return "#2e2440", "#c8b1ed"
    if rank <= 8:
        return "#e8bc55", "#18121f"
    if rank <= 16:
        return "#7d58b3", "#ffffff"
    if rank <= 24:
        return "#394052", "#dce0e8"
    return "#4a223f", "#f3badc"


def text(x: int, y: int, value: str, size: int, fill: str = "#ffffff", *,
         anchor: str = "start", weight: int = 500, spacing: float = 0,
         family: str = "Arial, Helvetica, sans-serif") -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-family="{family}" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" '
        f'letter-spacing="{spacing}">{escape(value)}</text>'
    )


def unit_cell(x: int, y: int, width: int, value: str, rank: int, performance: bool,
              *, align: str) -> list[str]:
    bg, fg = rank_color(rank, performance)
    if align == "left":
        value_x = x + 24
        pill_x = x + width - 78
        anchor = "start"
    else:
        value_x = x + width - 24
        pill_x = x + 18
        anchor = "end"
    return [
        text(value_x, y + 32, value, 25, "#f7f4fb", anchor=anchor, weight=700),
        f'<rect x="{pill_x}" y="{y + 9}" width="60" height="31" rx="15" fill="{bg}"/>',
        text(pill_x + 30, y + 31, f"#{rank}", 17, fg, anchor="middle", weight=800),
    ]


def matchup_panel(y: int, kicker: str, left_team: str, left_side: str,
                  right_team: str, right_side: str, units: dict, ranks: dict,
                  accent: str) -> list[str]:
    x = 58
    width = 1084
    metric_width = 402
    side_width = (width - metric_width) // 2
    header_h = 94
    section_h = 38
    row_h = 51
    panel_h = header_h + section_h * 2 + row_h * len(METRICS) + 14
    out = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{panel_h}" rx="18" fill="#121019" stroke="#332940" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="10" height="{panel_h}" rx="5" fill="{accent}"/>',
        text(x + 30, y + 31, kicker.upper(), 18, accent, weight=800, spacing=1.6),
        text(x + 30, y + 70, f"{TEAMS[left_team].upper()} {left_side.upper()}", 26, "#ffffff", weight=800),
        text(x + width - 30, y + 70, f"{TEAMS[right_team].upper()} {right_side.upper()}", 26, "#ffffff", anchor="end", weight=800),
        text(x + width // 2, y + 68, "VS", 17, "#756b80", anchor="middle", weight=800),
        f'<line x1="{x + 22}" y1="{y + header_h}" x2="{x + width - 18}" y2="{y + header_h}" stroke="#332940" stroke-width="2"/>',
    ]

    current_y = y + header_h
    left_x = x + 18
    metric_x = left_x + side_width
    right_x = metric_x + metric_width
    metric_groups = [("EFFICIENCY & EXECUTION", METRICS[:8]), ("TENDENCY", METRICS[8:])]
    for section_label, metrics in metric_groups:
        out.append(f'<rect x="{x + 10}" y="{current_y}" width="{width - 10}" height="{section_h}" fill="#1b1722"/>')
        out.append(text(x + width // 2, current_y + 26, section_label, 16, "#a99db4", anchor="middle", weight=800, spacing=1.2))
        current_y += section_h
        for idx, metric in enumerate(metrics):
            if idx % 2 == 1:
                out.append(f'<rect x="{x + 10}" y="{current_y}" width="{width - 10}" height="{row_h}" fill="#17131d"/>')
            out.extend(unit_cell(
                left_x, current_y, side_width,
                format_value(units[left_side][left_team][metric.key], metric.format),
                ranks[left_side][left_team][metric.key], metric.performance,
                align="left",
            ))
            out.append(text(metric_x + metric_width // 2, current_y + 32, metric.label, 20, "#cfc8d5", anchor="middle", weight=600))
            out.extend(unit_cell(
                right_x, current_y, side_width,
                format_value(units[right_side][right_team][metric.key], metric.format),
                ranks[right_side][right_team][metric.key], metric.performance,
                align="right",
            ))
            out.append(f'<line x1="{x + 26}" y1="{current_y + row_h}" x2="{x + width - 18}" y2="{current_y + row_h}" stroke="#26202f" stroke-width="1"/>')
            current_y += row_h
    return out


def build_svg(season: int, week: int, plays: pd.DataFrame) -> str:
    units = {
        "offense": league_units(plays, "offense"),
        "defense": league_units(plays, "defense"),
    }
    ranks = {
        "offense": ranked_units(units["offense"], "offense"),
        "defense": ranked_units(units["defense"], "defense"),
    }
    for team in TEAMS:
        if team not in units["offense"] or team not in units["defense"]:
            raise RuntimeError(f"Missing {team} Week {week} data")

    width, height = 1200, 1705
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Ravens versus Saints Week 2 matchup data</title>',
        '<desc id="desc">League-ranked offensive and defensive efficiency comparison through Week 1 of the 2026 NFL season.</desc>',
        '<rect width="1200" height="1705" fill="#09080c"/>',
        '<path d="M0 0H1200V205H0Z" fill="#15101d"/>',
        '<path d="M0 0H1200V12H0Z" fill="#7c4dc4"/>',
        '<circle cx="78" cy="74" r="30" fill="#7c4dc4"/>',
        text(78, 84, "DE", 24, "#ffffff", anchor="middle", weight=900),
        text(124, 65, "DUAL EIGHTS", 22, "#bda4e5", weight=800, spacing=2.5),
        text(58, 132, "RAVENS × SAINTS", 48, "#ffffff", weight=900, spacing=0.5),
        text(58, 178, "MATCHUP DNA", 33, "#e8bc55", weight=800, spacing=3.2),
        text(1142, 70, f"WEEK 2 · {season}", 20, "#d9d2df", anchor="end", weight=800, spacing=1.2),
        text(1142, 104, f"League ranks through Week {week}", 18, "#8f8499", anchor="end", weight=500),
        text(1142, 142, "PERFORMANCE: #1 BEST", 14, "#e8bc55", anchor="end", weight=800, spacing=1.1),
        text(1142, 169, "TENDENCY: #1 MOST FREQUENT", 14, "#c8b1ed", anchor="end", weight=800, spacing=1.1),
    ]
    elements.extend(matchup_panel(
        230, "When the Ravens have the ball", "BAL", "offense", "NO", "defense",
        units, ranks, "#9b6ee6",
    ))
    elements.extend(matchup_panel(
        944, "When the Saints have the ball", "NO", "offense", "BAL", "defense",
        units, ranks, "#e8bc55",
    ))
    elements.extend([
        text(58, 1680, "SOURCE: NFLVERSE PLAY-BY-PLAY · REGULAR SEASON THROUGH WEEK 1 · EARLY-SEASON SAMPLE", 15, "#7f7588", weight=700, spacing=0.8),
        text(1142, 1680, "DUALEIGHTS.COM", 15, "#9b6ee6", anchor="end", weight=800, spacing=1.1),
        '</svg>',
    ])
    return "\n".join(elements)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--week", type=int, default=1)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    pbp = pd.read_parquet(PBP_URL.format(season=args.season))
    plays = eligible_plays(pbp, args.week)
    svg = build_svg(args.season, args.week, plays)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8")
    print(f"Wrote {args.output} from {len(plays)} qualifying plays; generated {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
