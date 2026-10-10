"""Validate NFL coverage, immutable-forecast timing and additive model output."""
import json
import math
from datetime import datetime
from pathlib import Path


def validate(data):
    assert data['season']==2026
    assert len(data['teams'])==32 and len({t['abbr'] for t in data['teams']})==32
    assert sorted(t['rank'] for t in data['teams'])==list(range(1,33))
    assert abs(sum(t['strength'] for t in data['teams']))<1e-7
    for t in data['teams']:
        assert math.isfinite(t['strength']) and 0<=t['efficiency']<=100
        assert abs(t['strength']-sum(t[k] for k in ['offense_points','defense_points','st_points','qb_points']))<1e-7
        assert 1<=t['efficiency_rank']<=32
        assert any(q['id']==t['expected_qb']['id'] for q in t['qb_options'])
    games=data['games']
    assert len({g['game_id'] for g in games})==len(games)
    assert sum(g['status']=='Final' and g['week']<=data['rating_week'] for g in games)==data['rating_games']
    for g in games:
        assert g['game_id'].startswith('2026_')
        if g['forecast_home_margin'] is not None:assert math.isfinite(g['forecast_home_margin'])
        if g['forecast_kind']=='saved':
            assert datetime.fromisoformat(g['forecast_generated_at'])<datetime.fromisoformat(g['kickoff_utc'])
            assert g['forecast_rating_week']<g['week']
        if 'display_home_margin' in g and g['forecast_home_margin'] is not None:
            assert abs(g['display_home_margin']-g['forecast_home_margin']-g['lineup_adjustment'])<1e-7
            if g['status']!='Final':assert not g['lineup_changed'] and g['lineup_adjustment']==0
        if g['status']=='Final':assert g['actual_home_margin']==g['home_score']-g['away_score']
    public=json.dumps(data)
    assert '0.3-beta' not in public and 'beta 0.3' not in public.lower()


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    data=json.loads((root/'_data/nfl_dashboard.json').read_text())
    validate(data)
    assert data==json.loads((root/'assets/data/nfl-dashboard.json').read_text())
    print('NFL coverage, additive points, pregame timing, public labels and data copies verified.')
