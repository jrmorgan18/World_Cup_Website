"""Release-blocking checks for model metadata, scores and comparable snapshots."""
import json
import math
from pathlib import Path

from efficiency_model import COMPONENTS, PLAY_TYPES, VERSION, model_metadata


def validate(data):
    model = data["efficiency_model"]
    assert model["version"] == VERSION, "Wrong efficiency model version"
    calibration = model["calibration"]
    assert model == model_metadata(calibration), "Artifact settings differ from the implemented model"
    assert data["league_efficiency_rankings"]["model_version"] == VERSION
    assert calibration["season"] < data["season"], "Calibration uses future data"
    weights = calibration["phase_weights"]
    assert set(weights) == set(PLAY_TYPES)
    assert all(0 < w < 1 for w in weights.values())
    assert math.isclose(sum(weights.values()), 1), "Invalid play mix"
    assert all(math.isfinite(s) and s > 0 for s in calibration["scales"].values())
    for snapshot in data["snapshots"] + [data["benchmark_snapshot"]]:
        assert snapshot["model_version"] == VERSION, "Mixed model versions in history"
    for row in data["league_efficiency_rankings"]["teams"]:
        components = row["adjusted_components"]
        for component in COMPONENTS:
            expected = sum(weights[p] * components[f"{p}_{component}"] /
                           calibration["scales"][f"{p}_{component}"] for p in PLAY_TYPES)
            assert math.isclose(components[component], expected, abs_tol=1e-10)
        composite = sum(components[c] for c in COMPONENTS) / 4
        assert math.isclose(components["composite"], composite, abs_tol=1e-10)
        assert row["value"] == round(50 + 50 * math.tanh(composite / 2), 1), "Score cannot be reproduced"
    current = next(s for s in data["snapshots"] if s["id"] == data["current_snapshot"])
    if current["week"]:
        teams = data["league_efficiency_rankings"]["teams"]
        assert len(teams) == 32 and len({t["abbr"] for t in teams}) == 32
        for row in teams:
            expected = 1 + sum(t["adjusted_components"]["composite"] > row["adjusted_components"]["composite"] for t in teams)
            assert row["rank"] == expected, "Rank does not match unrounded score"
        ravens = next(t for t in teams if t["abbr"] == "BAL")
        assert current["metrics"]["overall_efficiency"]["value"] == ravens["value"]
        assert current["metrics"]["overall_efficiency"]["rank"] == ravens["rank"]


if __name__ == "__main__":
    path = Path(__file__).resolve().parents[1] / "_data/ravens_dashboard_stats.json"
    validate(json.loads(path.read_text(encoding="utf-8")))
    print("Efficiency model version, calibration, reproducible scores and snapshot checks passed.")
