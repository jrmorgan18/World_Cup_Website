"""Production wiring for the already-published Dual Eights v2.1 formula.

Raw dashboard rates are unchanged. Use the exact frozen 2025 calibration from
the Week 4 publication, and retain archived v1 snapshots as explicitly labeled.
"""
import json
from pathlib import Path

import efficiency_model as model
import special_teams as st

SOURCE = "Dual Eights v2.1 · opponent/venue adjustment + special teams"
METHOD_URL = "/ravens/dual-eights-efficiency-index-week-four-2026/"


def calibration(season):
    path = Path(__file__).with_name(f"efficiency_calibration_{season - 1}.json")
    result = json.loads(path.read_text(encoding="utf-8"))
    if result["season"] != season - 1:
        raise ValueError("Efficiency calibration must precede the current season")
    return result


def apply_model(table, pbp, games, eligible, anchors):
    if games.empty:
        return table
    rows = model.prepare_plays(eligible(pbp, set(games.game_id)), games)
    special = st.fit_special_teams(pbp, games, anchors["special_teams"])
    adjusted = model.score_units(model.fit_units(rows), anchors, special)
    if set(adjusted.index) != set(table.index):
        raise ValueError("Adjusted index does not cover all dashboard teams")
    table["overall_efficiency"] = adjusted.overall_efficiency
    table.attrs["model_version"] = model.VERSION
    table.attrs["adjusted_units"] = adjusted
    return table


def preserve_published_history(existing, published):
    # The sidebar's Week 4 article is the authoritative archived v2.1 ranking.
    # Do not silently compare its scale with earlier percentile-based scores.
    for snapshot in existing.get("snapshots", []):
        snapshot.setdefault("model_version", "1")
    if not published or published.get("model_version") != model.VERSION:
        return
    snapshot_id = f"{published['season']}-week-{published['through_week']:02d}"
    ravens = next((row for row in published["teams"] if row["abbr"] == "BAL"), None)
    for snapshot in existing.get("snapshots", []):
        if snapshot["id"] == snapshot_id and ravens:
            snapshot["model_version"] = model.VERSION
            snapshot["metrics"]["overall_efficiency"] = {
                "value": ravens["value"], "rank": ravens["rank"], "source": SOURCE,
            }


def sidebar_payload(rankings, season, week, as_of):
    return {
        "season": season, "through_week": week, "model_version": model.VERSION,
        "as_of": as_of.isoformat(), "label": f"Through available Week {week} games · v{model.VERSION}",
        "sample_note": "Completed games only · 45% offense / 45% defense / 10% special teams",
        "article_url": METHOD_URL, "article_link_label": "Read the v2.1 methodology",
        "teams": rankings["teams"],
    }
