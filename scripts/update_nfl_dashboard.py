#!/usr/bin/env python3
"""Build the NFL hub with the reviewed, frozen TSI formula and production Efficiency.

No subjective rankings or market lines enter the model. Public data is written
only after coverage, temporal and numerical checks succeed. Existing forecasts
are immutable; games without an archived pregame forecast are retrospective.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts' / 'strength_beta_lab'))
from fetch_strength_beta_inputs import fetch, COLUMNS
from fetch_refinement_inputs import EXTRAS
from refine_strength_beta import (RefinedBuilder, Experiment, model_payload, correct_venues, metrics, skill_for)
from update_ravens_dashboard import compute_league_metrics

BASE = 'https://github.com/nflverse/nflverse-data/releases/download/'


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    temporary.replace(path)


def refresh_inputs(cache, season):
    cache.mkdir(parents=True, exist_ok=True)
    extra = cache / 'refinement'; extra.mkdir(exist_ok=True)
    def old_year(year):
        return (fetch(cache, f'pbp-{year}.parquet', f'pbp/play_by_play_{year}.parquet', columns=COLUMNS),
                fetch(extra, f'pbp-extra-{year}.parquet', f'pbp/play_by_play_{year}.parquet', columns=EXTRAS))
    with ThreadPoolExecutor(max_workers=4) as pool:
        historical = list(pool.map(old_year, range(2016, season)))
    # Current PBP is downloaded once: both models consume the same source revision.
    url = BASE + f'pbp/play_by_play_{season}.parquet'
    with urlopen(url, timeout=120) as response:
        modified = response.headers.get('Last-Modified'); raw = response.read()
    frame = pd.read_parquet(io.BytesIO(raw))
    current = []
    for folder, name, columns in [(cache, f'pbp-{season}.parquet', COLUMNS),
                                   (extra, f'pbp-extra-{season}.parquet', EXTRAS)]:
        path = folder / name; frame[columns].to_parquet(path, index=False)
        record = {'file': name, 'url': url, 'fetched_at': datetime.now(timezone.utc).isoformat(),
                  'http_last_modified': modified, 'source_sha256': hashlib.sha256(raw).hexdigest(),
                  'cache_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        atomic_json(folder / (name+'.source.json'), record); current.append(record)
    core = [pair[0] for pair in historical] + [current[0]]
    supplement = [pair[1] for pair in historical] + [current[1]]
    for name, relative in [('games.csv','schedules/games.csv'),
                           ('depth_charts.parquet',f'depth_charts/depth_charts_{season}.parquet'),
                           ('snap_counts.parquet',f'snap_counts/snap_counts_{season}.parquet')]:
        core.append(fetch(cache, name, relative, refresh=True))
    try:
        core.append(fetch(cache, 'injuries.parquet', f'injuries/injuries_{season}.parquet', refresh=True))
    except Exception as error:
        # Injury context is optional; it never supplies team EPA or changes model coefficients.
        print(f'Injury refresh unavailable: {error}', flush=True)
        metadata = cache / 'injuries.parquet.source.json'
        if metadata.exists(): core.append(json.loads(metadata.read_text()))
        else:
            path = cache / 'injuries.parquet'
            pd.DataFrame(columns=['team','week','gsis_id','position','report_status']).to_parquet(path,index=False)
            core.append({'file':path.name,'url':None,'fetched_at':None,'cache_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    supplement.append(fetch(extra, 'draft_picks.parquet', 'draft_picks/draft_picks.parquet',
                            columns=['season','round','pick','gsis_id','position']))
    atomic_json(cache/'manifest.json',core); atomic_json(extra/'manifest.json',supplement)


def completed_cutoff(schedule, season, requested=None, allow_partial=False):
    regular = schedule[(schedule.season==season)&(schedule.game_type=='REG')]
    if requested is None:
        complete = [int(w) for w,g in regular.groupby('week') if g.home_score.notna().all() and g.away_score.notna().all()]
        if not complete: raise ValueError('No fully completed regular-season week')
        requested = max(complete)
    through = regular[regular.week<=requested]
    if allow_partial:
        earlier=through[through.week<requested]
        if earlier.home_score.isna().any() or earlier.away_score.isna().any():
            raise ValueError('Partial cutoff requires all earlier weeks to be complete')
        through=through[through.home_score.notna()&through.away_score.notna()]
    if through.empty or through.home_score.isna().any() or through.away_score.isna().any():
        raise ValueError('Rating cutoff contains missing or unfinished games')
    if set(through.week.astype(int)) != set(range(1,requested+1)):
        raise ValueError('Rating cutoff has missing weeks')
    return requested, through


def kickoff_utc(game):
    # nflverse gametime is Eastern. Convert before checking forecast timestamps.
    raw = f"{game.gameday}T{game.gametime if pd.notna(game.gametime) else '00:00'}"
    return datetime.fromisoformat(raw).replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc)


def archived_before_game(archive, game):
    stamp = datetime.fromisoformat(archive['generated_at'].replace('Z','+00:00'))
    return stamp < kickoff_utc(game) and archive['rating_week'] < int(game.week)


def add_forecasts(archive, upcoming, teams, home_advantage, rating_week, generated_at, cutoff_context=None):
    preserved = list(archive)
    existing = {f['game_id']:f for f in sorted(archive,key=lambda f:f['generated_at'])}
    now = datetime.fromisoformat(generated_at)
    for game in upcoming.itertuples():
        if now >= kickoff_utc(game): continue
        h,a = teams[game.home_team], teams[game.away_team]
        margin=h['strength']-a['strength']+(home_advantage if game.location=='Home' else 0.)
        old=existing.get(game.game_id)
        if old and abs(old['home_margin']-margin)<1e-9 and old['home_qb_id']==h['expected_qb']['id'] and old['away_qb_id']==a['expected_qb']['id']:continue
        preserved.append({'game_id':game.game_id,'season':int(game.season),'week':int(game.week),
            'generated_at':generated_at,'rating_week':rating_week,
            'home_margin':margin,
            'home_qb':h['expected_qb']['name'],'away_qb':a['expected_qb']['name'],
            'home_qb_id':h['expected_qb']['id'],'away_qb_id':a['expected_qb']['id'],
            'provenance':'Saved research forecast','published_before_kickoff':False,**(cutoff_context or {})})
    return preserved


def number(value):
    return float(value) if pd.notna(value) and np.isfinite(float(value)) else None


def reconcile_completed_qbs(schedule, pbp, quarterback_names):
    """Use the first recorded QB dropback when a final game's schedule identity disagrees.

    This avoids counting a backup who relieved the starter later as the starter.
    Only known quarterbacks qualify, so trick-play passers cannot replace a QB.
    Games without a recorded QB dropback retain their schedule assumption.
    """
    output=schedule.copy()
    plays=pbp[pbp.qb_dropback.eq(1)&pbp.passer_player_id.isin(quarterback_names)&pbp.posteam.notna()]
    first=plays.sort_values(['game_id','play_id']).drop_duplicates(['game_id','posteam'])
    recorded={(r.game_id,r.posteam):r.passer_player_id for r in first.itertuples()}
    changes=[]
    for index,game in output.iterrows():
        if pd.isna(game.home_score) or pd.isna(game.away_score):continue
        for side in ['home','away']:
            qb=recorded.get((game.game_id,game[side+'_team']))
            if not qb:continue
            if qb!=game[side+'_qb_id']:
                changes.append({'game_id':game.game_id,'team':game[side+'_team'],
                    'schedule_qb':game[side+'_qb_name'],'recorded_qb':quarterback_names[qb]})
            output.loc[index,side+'_qb_id']=qb
            output.loc[index,side+'_qb_name']=quarterback_names[qb]
    return output,changes


def actual_starter_adjustment(game, assumed, snapshot, features, coefficients):
    """Replace assumed QB skill with actual starter skill, using the pregame cutoff only."""
    adjustment = 0.
    changed = False
    for side, sign in [('home', 1.), ('away', -1.)]:
        actual_id = getattr(game, side+'_qb_id', None)
        assumed_id = assumed.get(getattr(game, side+'_team'), {}).get('id')
        if not assumed_id or pd.isna(actual_id) or not actual_id or actual_id == assumed_id:
            continue
        changed = True
        actual = skill_for(snapshot['skills'], actual_id, snapshot['priors'])
        original = skill_for(snapshot['skills'], assumed_id, snapshot['priors'])
        for metric in ['epa', 'cpoe', 'rush']:
            feature = 'qb_'+metric+'_delta'
            if feature in features:
                adjustment += sign*(actual.get(metric, 0.)-original.get(metric, 0.))*coefficients[features.index(feature)]
    return float(adjustment), changed


def build(cache, season, requested, audit=False, allow_partial=False):
    config = json.loads((ROOT/'scripts/nfl_model_config.json').read_text())
    seed = json.loads((ROOT/'scripts/nfl_model_seed.json').read_text())
    schedule = pd.read_csv(cache/'games.csv')
    cutoff, completed = completed_cutoff(schedule,season,requested,allow_partial)
    current_pbp=pd.read_parquet(cache/f'pbp-{season}.parquet')
    missing=set(completed.game_id)-set(current_pbp.game_id)
    if missing:raise ValueError('Missing play-by-play for completed games: '+', '.join(sorted(missing)))
    rating_schedule=schedule[(schedule.season==season)&(schedule.game_type=='REG')&(schedule.week==cutoff)]
    pending=rating_schedule[rating_schedule.home_score.isna()|rating_schedule.away_score.isna()]
    builder = RefinedBuilder(cache,season,cutoff)
    qb_depth=builder.depth_all[(builder.depth_all.pos_abb=='QB')&builder.depth_all.gsis_id.notna()].sort_values('dt').drop_duplicates('gsis_id',keep='last')
    qb_names=dict(zip(qb_depth.gsis_id,qb_depth.player_name))
    current_schedule=builder.all_schedule[builder.all_schedule.season==season]
    for side in ['home','away']:
        for q,n in zip(current_schedule[side+'_qb_id'],current_schedule[side+'_qb_name']):
            if pd.notna(q) and pd.notna(n):qb_names.setdefault(q,n)
    corrected,qb_corrections=reconcile_completed_qbs(current_schedule,current_pbp,qb_names)
    builder.all_schedule.loc[corrected.index,['home_qb_id','home_qb_name','away_qb_id','away_qb_name']]=corrected[['home_qb_id','home_qb_name','away_qb_id','away_qb_name']]
    builder.games[season]=corrected[corrected.game_type.eq('REG')&corrected.home_score.notna()&corrected.away_score.notna()&corrected.week.le(cutoff)].copy()
    if qb_corrections:print('QB schedule/PBP corrections: '+json.dumps(qb_corrections),flush=True)
    parameters = {k:v for k,v in config['experiment'].items() if k in Experiment.__dataclass_fields__}
    exp = Experiment(**parameters)
    coef = np.array([config['coefficients'][k] for k in exp.features+['home_advantage']])
    # Historical year-end snapshots initialize identical priors. Only 2026 is replayed.
    rows,details = builder.generate_refined(exp,evaluate_from=season)
    model = model_payload(builder,exp,details,coef,config['validation'],seed)
    records,efficiency = compute_league_metrics(completed,current_pbp)
    _,previous_efficiency = compute_league_metrics(completed[completed.week<cutoff],current_pbp)
    efficiency_ranks = efficiency.overall_efficiency.rank(method='min',ascending=False)
    previous_efficiency_ranks = previous_efficiency.overall_efficiency.rank(method='min',ascending=False)
    teams=[]
    injury_week = cutoff+1
    for t in model['teams']:
        abbr=t['abbr']; record=records.loc[abbr]
        wins,losses,ties = [int(record[k]) for k in ['wins','losses','ties']]
        injury = builder.injuries[(builder.injuries.team==abbr)&(builder.injuries.week==injury_week)]
        option_rows=[]
        for q in t['qb_options']:
            matched=injury[injury.gsis_id==q['id']]
            status=matched.report_status.dropna().iloc[-1] if len(matched) and len(matched.report_status.dropna()) else None
            option_rows.append({**q,'injury_status':status})
        teams.append({k:t[k] for k in ['abbr','name','rank','strength','offense_points','defense_points','st_points','qb_points','components','previous_week_beta_rank','weekly_rank_change','expected_qb','historical_context']})
        teams[-1].update({'record':f'{wins}-{losses}'+(f'-{ties}' if ties else ''),'games':wins+losses+ties,
            'qb_options':option_rows,'efficiency':float(efficiency.loc[abbr,'overall_efficiency']),
            'efficiency_rank':int(efficiency_ranks[abbr]),
            'efficiency_change':int(previous_efficiency_ranks.get(abbr,efficiency_ranks[abbr])-efficiency_ranks[abbr]),
            'offense_epa':float(efficiency.loc[abbr,'offensive_epa_per_play']),
            'defense_epa':float(efficiency.loc[abbr,'defensive_epa_per_play']),
            'offense_success':float(efficiency.loc[abbr,'offensive_success_rate']),
            'defense_success':float(efficiency.loc[abbr,'defensive_success_rate'])})
    generated_at=datetime.now(timezone.utc).isoformat()
    current_week=cutoff+1
    upcoming=builder.all_schedule[(builder.all_schedule.season==season)&(builder.all_schedule.week==current_week)&(builder.all_schedule.game_type=='REG')]
    archive_path=ROOT/'_data/nfl_forecast_archive.json'
    archive=json.loads(archive_path.read_text()).get('forecasts',[]) if archive_path.exists() else []
    by_team={t['abbr']:t for t in teams}
    archive=add_forecasts(archive,upcoming,by_team,model['home_advantage'],cutoff,generated_at,{'rating_week_complete':pending.empty,'rating_games':len(completed)})
    saved={f['game_id']:f for f in sorted(archive,key=lambda f:f['generated_at']) if f['season']==season}
    historical_rows={r.game_id:r for r in rows.itertuples() if r.season==season}
    replay_coef=coef.copy()
    # Efficiency-only margin benchmark is calibrated solely on prior historical training.
    # The constant 3.125 percentiles are displayed as an index, never treated as spread points.
    games_out=[]
    relevant=builder.all_schedule[(builder.all_schedule.season==season)&(builder.all_schedule.game_type=='REG')&(builder.all_schedule.week<=current_week)]
    for g in relevant.itertuples():
        final=pd.notna(g.home_score) and pd.notna(g.away_score)
        if g.week==current_week and g.game_id not in saved and not final: continue
        forecast=saved.get(g.game_id)
        if forecast and not archived_before_game(forecast,g): raise ValueError('Post-kickoff forecast in saved archive')
        replay=historical_rows.get(g.game_id)
        prediction=forecast['home_margin'] if forecast else float(np.array(replay.features)@replay_coef) if replay else None
        kind='saved' if forecast else 'retrospective' if replay else 'unavailable'
        snapshot=details.get(forecast['rating_week'] if forecast else int(g.week)-1,{})
        assumed=dict(snapshot.get('starters',{}))
        if forecast:
            assumed[g.home_team]={'id':forecast['home_qb_id'],'name':forecast['home_qb']}
            assumed[g.away_team]={'id':forecast['away_qb_id'],'name':forecast['away_qb']}
        adjustment,changed=actual_starter_adjustment(g,assumed,snapshot,exp.features,coef) if final and snapshot and prediction is not None else (0.,False)
        games_out.append({'game_id':g.game_id,'week':int(g.week),'date':str(g.gameday),'time_et':str(g.gametime),
            'kickoff_utc':kickoff_utc(g).isoformat(),'home':g.home_team,'away':g.away_team,'neutral':g.location=='Neutral',
            'stadium':str(g.stadium),'status':'Final' if final else 'Upcoming',
            'home_score':int(g.home_score) if final else None,'away_score':int(g.away_score) if final else None,
            'actual_home_margin':int(g.home_score-g.away_score) if final else None,
            'forecast_home_margin':prediction,'forecast_kind':kind,
            'display_home_margin':prediction+adjustment if prediction is not None else None,
            'lineup_adjustment':adjustment,'lineup_changed':changed,
            'forecast_generated_at':forecast['generated_at'] if forecast else generated_at,
            'forecast_rating_week':forecast['rating_week'] if forecast else int(g.week)-1,
            'home_qb':forecast['home_qb'] if forecast else assumed.get(g.home_team,{}).get('name'),
            'away_qb':forecast['away_qb'] if forecast else assumed.get(g.away_team,{}).get('name'),
            'home_qb_id':assumed.get(g.home_team,{}).get('id'),'away_qb_id':assumed.get(g.away_team,{}).get('id'),
            'market_home_margin':number(g.spread_line),'market_kind':'Closing line' if final else 'Market snapshot',
            'market_retrieved_at':next(s['fetched_at'] for s in json.loads((cache/'manifest.json').read_text()) if s['file']=='games.csv'),
            'actual_home_qb':str(g.home_qb_name) if final and pd.notna(g.home_qb_name) else None,
            'actual_away_qb':str(g.away_qb_name) if final and pd.notna(g.away_qb_name) else None,
            'home_field':model['home_advantage'] if g.location=='Home' else 0.})
    def summary(kind):
        sample=[g for g in games_out if g['status']=='Final' and g['forecast_kind']==kind and g['forecast_home_margin'] is not None]
        if not sample:return {'games':0,'mae':None,'market_mae':None,'home_baseline_mae':None}
        actual=np.array([g['actual_home_margin'] for g in sample])
        market=[g for g in sample if g['market_home_margin'] is not None]
        return {**metrics(actual,[g['forecast_home_margin'] for g in sample]),
            'market_mae':metrics([g['actual_home_margin'] for g in market],[g['market_home_margin'] for g in market])['mae'] if market else None,
            'market_games':len(market),'home_baseline_mae':metrics(actual,[g['home_field'] for g in sample])['mae'],
            'winner_correct':sum((g['forecast_home_margin']>0)==(g['actual_home_margin']>0) for g in sample if g['actual_home_margin']!=0),
            'decisive_games':sum(g['actual_home_margin']!=0 for g in sample)}
    sources=json.loads((cache/'manifest.json').read_text())+builder.extra_sources
    payload={'season':season,'rating_week':cutoff,'projection_week':current_week,'rating_games':len(completed),
        'generated_at':generated_at,'data_through':str(completed.gameday.max()),
        'rating_week_complete':pending.empty,'rating_week_completed_games':int((completed.week==cutoff).sum()),
        'rating_week_scheduled_games':len(rating_schedule),
        'completed_qb_corrections':qb_corrections,
        'actual_qb_policy':'First recorded known-quarterback dropback in completed-game play-by-play; schedule fallback if unavailable',
        'rating_pending_games':[{'away':g.away_team,'home':g.home_team,'date':str(g.gameday),'time_et':str(g.gametime)} for g in pending.itertuples()],
        'depth_chart_as_of':str(builder.depth_all.dt.max()),'home_advantage':model['home_advantage'],
        'teams':teams,'games':games_out,'results_summary':{'saved':summary('saved'),'retrospective':summary('retrospective')},
        'sources':[{'file':s['file'],'url':s.get('url'),'retrieved_at':s.get('fetched_at'),'last_modified':s.get('http_last_modified')} for s in sources if s['file'] in [f'pbp-{season}.parquet','games.csv','depth_charts.parquet','injuries.parquet']],
        'methodology':{'offense_carry':exp.offense_carry,'defense_carry':exp.defense_carry,'history_share':exp.history_share,
            'half_life':exp.half_life,'coach_multiplier':.65,'new_qb_multiplier':.60}}
    from check_nfl_dashboard import validate
    validate(payload)
    if audit:
        alternate=Experiment(**{**parameters,'key':'continuity_audit','label':'Continuity audit','continuity_adjustment':False})
        alt_rows,alt_details=builder.generate_refined(alternate,evaluate_from=2024)
        alt_model=model_payload(builder,alternate,alt_details,coef,config['validation'],seed)
        original={t['abbr']:t for t in model['teams']}
        result={'note':'Whole-league sensitivity with frozen production coefficients. No coefficient refit or team-specific tuning.',
            'current':[{'team':t['abbr'],'default_rank':original[t['abbr']]['rank'],'default_points':original[t['abbr']]['strength'],
                        'without_transition_rank':t['rank'],'without_transition_points':t['strength']} for t in alt_model['teams']],
            'without_transition_validation':{str(y):metrics(part.actual,np.stack(part.features)@coef) for y in [2024,2025] if len(part:=alt_rows[alt_rows.season==y])},
            'default_validation':{y:config['validation']['seasons'][y]['beta'] for y in ['2024','2025']}}
        atomic_json(ROOT/'scripts/nfl_continuity_audit.json',result)
    atomic_json(archive_path,{'forecasts':archive})
    atomic_json(ROOT/'_data/nfl_dashboard.json',payload)
    atomic_json(ROOT/'assets/data/nfl-dashboard.json',payload)
    pd.DataFrame([{k:v for k,v in t.items() if not isinstance(v,(dict,list))} for t in teams]).to_csv(ROOT/'assets/data/nfl-rankings.csv',index=False)
    pd.DataFrame([g for g in games_out if g['status']=='Final']).to_csv(ROOT/'assets/data/nfl-results.csv',index=False)
    print(f'NFL ready: {len(teams)} teams, {len(completed)} rating games, {len(games_out)} scheduled/results games.',flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--season',type=int,default=2026)
    parser.add_argument('--ratings-week',type=int)
    parser.add_argument('--cache-dir',type=Path,default=Path(os.environ.get('NFL_CACHE_DIR',str(ROOT/'.nfl-cache'))))
    parser.add_argument('--no-refresh',action='store_true')
    parser.add_argument('--allow-partial-week',action='store_true',help='Manual interim update using only completed games in the requested week')
    parser.add_argument('--audit-continuity',action='store_true')
    args=parser.parse_args()
    if args.allow_partial_week and args.ratings_week is None:raise ValueError('Partial updates require an explicit ratings week')
    if args.season!=2026:raise ValueError('The public beta results page currently supports 2026 only')
    if not args.no_refresh:refresh_inputs(args.cache_dir,args.season)
    build(args.cache_dir,args.season,args.ratings_week,args.audit_continuity,args.allow_partial_week)


if __name__=='__main__':main()
