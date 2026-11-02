"""Explicit editorial defense reviews, applied only to the named team.

These are judgments, not fitted coefficients. A game's correction dilutes with
new defensive exposure. Other teams' points and the raw model remain untouched.
"""
from datetime import datetime
import math


def exposure_at(exposure, team, cutoff, half_life):
    return sum(weight * .5 ** ((cutoff - week) / half_life)
        for (abbr, week), weight in exposure.items() if abbr == team and week <= cutoff)


def apply_rating_reviews(teams, document, season, rating_week, completed_ids, exposure, generated_at):
    built = datetime.fromisoformat(generated_at)
    by_team = {t['abbr']:t for t in teams}
    # Restore the raw values if called again on a reviewed payload.
    for t in teams:
        if 'rating_review_points' in t:
            t['strength'] = t.pop('unreviewed_strength')
            t['defense_points'] -= t.pop('rating_review_points')
            t['components'].pop('review_defense',None)
            t.pop('rating_reviews',None)
    seen = set()
    for review in document.get('reviews',[]):
        if review['season'] != season or rating_week < review['reference_week']:
            continue
        if review['id'] in seen:
            raise ValueError('Duplicate rating review: '+review['id'])
        seen.add(review['id'])
        t = by_team.get(review['team'])
        points, half_life = review['points'], review['half_life_weeks']
        observed = datetime.fromisoformat(review['observed_at'])
        if (t is None or review['component'] != 'defense' or review['game_id'] not in completed_ids
                or not review['game_id'].startswith(str(season)+'_') or review['team'] not in review['game_id'].split('_')[2:]
                or int(review['game_id'].split('_')[1]) > review['reference_week']
                or not math.isfinite(points) or abs(points)>2 or not math.isfinite(half_life) or half_life<=0
                or observed.tzinfo is None or observed>built or not review.get('summary')
                or not review.get('sources') or not all(s.get('title') and str(s.get('url','')).startswith('https://') for s in review['sources'])):
            raise ValueError('Invalid reviewed defense adjustment: '+review['id'])
        reference = exposure_at(exposure,review['team'],review['reference_week'],half_life)
        current = exposure_at(exposure,review['team'],rating_week,half_life)
        if reference<=0 or current<=0:
            raise ValueError('Missing defensive exposure for review: '+review['id'])
        factor = min(1.,reference * .5 ** ((rating_week-review['reference_week'])/half_life) / current)
        adjustment = points*factor
        t.setdefault('unreviewed_strength',t['strength'])
        t['rating_review_points'] = t.get('rating_review_points',0.)+adjustment
        t['strength'] += adjustment
        t['defense_points'] += adjustment
        t['components']['review_defense'] = t['rating_review_points']
        t.setdefault('rating_reviews',[]).append({**review,'effective_points':adjustment,
            'exposure_factor':factor,'kind':'Editorial review; not a fitted coefficient'})
    teams.sort(key=lambda t:-t['strength'])
    for rank,t in enumerate(teams,1):
        t['rank'] = rank
        t['weekly_rank_change'] = t['previous_week_beta_rank']-rank
    return teams
