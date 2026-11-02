"""Select the late-season projection scale for frozen DEPI strengths.

Rankings are unchanged: the scale multiplies only the team-strength difference in
a projected margin. Home advantage is never scaled. Selection uses 2019-2023
rolling pregame features; 2024-2026 are reported as previously inspected
retrospective diagnostics, not untouched validation. Week 18 is excluded from
selection because resting starters are information the play-by-play cannot see.

    python -m strength_beta_lab.calibrate_projection --records PATH/feature-records.pkl [--write]
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

CONFIG = Path(__file__).resolve().parents[1] / 'nfl_model_config.json'
LATE_WEEKS = (14, 17)
GRID = np.round(np.arange(.80, 2.001, .02), 2)


def frame(records, coefficients):
    features = [k for k in coefficients if k != 'home_advantage']
    weights = np.array([coefficients[k] for k in features])
    rows = records[records.market.notna()].copy()
    rows['strength'] = np.array([[f[k] for k in features] for f in rows.features]) @ weights
    rows['home_field'] = coefficients['home_advantage'] * rows.home_venue
    return rows


def mae(rows, scale):
    return float(np.abs(rows.actual - scale * rows.strength - rows.home_field).mean())


def select_scale(rows):
    late = rows[(rows.season <= 2023) & rows.week.between(*LATE_WEEKS)]
    return float(min(GRID, key=lambda scale: (mae(late, scale), abs(scale - 1.))))


def diagnostics(rows, scale):
    result = {}
    for season, group in rows.groupby('season'):
        late = group[group.week.between(*LATE_WEEKS)]
        if late.empty:
            continue
        market = float(np.abs(late.actual - late.market).mean())
        result[str(int(season))] = {'games': int(len(late)), 'mae_before': mae(late, 1.), 'mae_after': mae(late, scale),
                                    'market_mae': market}
    for label, group in [('2019-2023', rows[rows.season <= 2023]), ('2024-2026', rows[rows.season >= 2024])]:
        late = group[group.week.between(*LATE_WEEKS)]
        result[label] = {'games': int(len(late)), 'mae_before': mae(late, 1.), 'mae_after': mae(late, scale),
                         'market_mae': float(np.abs(late.actual - late.market).mean())}
    return result


def week18(rows):
    late = rows[rows.week == 18]
    return {label: {'games': int(len(g)), 'model_mae': mae(g, 1.), 'market_mae': float(np.abs(g.actual - g.market).mean())}
            for label, g in [('2019-2023', late[late.season <= 2023]), ('2024-2026', late[late.season >= 2024])]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=Path, required=True)
    parser.add_argument('--write', action='store_true', help='Store the selection in nfl_model_config.json')
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text())
    rows = frame(pd.read_pickle(args.records), config['coefficients'])
    scale = select_scale(rows)
    calibration = {
        'id': 'late-season-v1',
        'model_id': config['model_id'],
        'activation': {'season': 2026, 'rating_week': 8},
        'default_scale': 1.,
        'strength_scale_by_week': [{'first_week': LATE_WEEKS[0], 'last_week': LATE_WEEKS[1], 'scale': scale}],
        'selection': 'Grid-searched MAE on 2019-2023 Weeks 14-17 rolling pregame features; home advantage unscaled; Week 18 excluded.',
        'note': ('Weeks 1-13 stay at 1.0. A Weeks 1-8 scale selected on 2019-2023 (1.22) and a Weeks 9-13 scale (1.04) '
                 'did not improve the previously inspected 2024-2026 seasons, so neither was adopted.'),
        'late_season': diagnostics(rows, scale),
        'week_18': week18(rows),
        'research_snapshot_sha256': hashlib.sha256(args.records.read_bytes()).hexdigest(),
    }
    print(json.dumps(calibration, indent=2))
    if args.write:
        config['projection_calibration'] = calibration
        CONFIG.write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
