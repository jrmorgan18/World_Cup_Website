"""Retain timestamped pregame quotes without inventing an opening/best-week line."""
from datetime import datetime, timezone
import math

SOURCE = 'https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv'


def stamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (TypeError, ValueError, AttributeError):
        return None


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def observations_from_dashboard(data, recorded_at=None, revision=None):
    """Git recovery uses commit time so a late-published old snapshot cannot qualify."""
    recorded_at = recorded_at or data.get('generated_at')
    recorded = stamp(recorded_at)
    if not recorded:
        return []
    result = []
    for game in data.get('games', []):
        quote = game.get('market_home_margin')
        observed = stamp(game.get('market_retrieved_at'))
        forecast = stamp(game.get('forecast_generated_at'))
        kickoff = stamp(game.get('kickoff_utc'))
        if (game.get('status') != 'Upcoming' or game.get('forecast_kind') != 'saved'
                or not finite(quote) or not finite(game.get('forecast_home_margin'))
                or not all([observed, forecast, kickoff])
                or not observed <= recorded < kickoff or not forecast <= recorded):
            continue
        result.append({'game_id': game['game_id'], 'observed_at': game['market_retrieved_at'],
            'recorded_at': recorded_at, 'home_margin': quote,
            'forecast_generated_at': game['forecast_generated_at'],
            'forecast_home_margin': game['forecast_home_margin'], 'source': SOURCE,
            **({'recovered_from_revision': revision} if revision else {})})
    return result


def merge_observations(existing, additions):
    """Keep the earliest verifiable recording of each quote/forecast pair."""
    unique = {}
    for row in sorted(existing + additions, key=lambda r: stamp(r['recorded_at'])):
        key = (row['game_id'], row['observed_at'], row['home_margin'], row['forecast_generated_at'])
        unique.setdefault(key, row)
    return sorted(unique.values(), key=lambda r: (r['game_id'], stamp(r['recorded_at']), stamp(r['observed_at'])))


def eligible_observations(game, observations):
    if game.get('forecast_kind') != 'saved' or not finite(game.get('forecast_home_margin')):
        return []
    forecast, kickoff = stamp(game.get('forecast_generated_at')), stamp(game.get('kickoff_utc'))
    if not forecast or not kickoff:
        return []
    result = []
    for row in observations:
        observed, recorded = stamp(row.get('observed_at')), stamp(row.get('recorded_at'))
        if (row.get('game_id') == game['game_id']
                and stamp(row.get('forecast_generated_at')) == forecast
                and finite(row.get('home_margin')) and finite(row.get('forecast_home_margin'))
                and abs(row['forecast_home_margin'] - game['forecast_home_margin']) < 1e-9
                and observed and recorded and observed <= recorded < kickoff and forecast <= recorded):
            result.append(row)
    return sorted(result, key=lambda r: (stamp(r['recorded_at']), stamp(r['observed_at'])))


def attach_market_history(data, observations):
    for game in data['games']:
        game['market_history'] = eligible_observations(game, observations)
    data['market_history_policy'] = {
        'source': SOURCE,
        'coverage': 'Snapshots captured by Dual Eights, not every bookmaker or every price during the week.',
        'forecast': 'First/best recorded lines use the original saved forecast, without retrospective QB corrections.',
        'best': 'Largest absolute gap to the frozen saved model; ties use the earliest recording. No final scores enter selection.',
        'timing': 'Only quotes recorded before kickoff while the same saved forecast was available qualify.'}
    return data
