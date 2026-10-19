"""Build an informational injury watchlist; never change DEPI or saved forecasts."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
from strength_beta_lab.team_strength_beta import TEAMS, TEAM_NAMES

POSITIONS={'OL':{'OL','T','OT','G','OG','C','LT','RT','LG','RG'},'REC':{'WR','TE'},
           'DB':{'CB','S','DB','FS','SS'},'FRONT':{'DE','DT','DL','NT','EDGE','ED','DI','IDL','OLB'},
           'LB':{'LB','ILB','MLB'},'RB':{'RB','FB','HB'}}

def group_for(position):
    return next((g for g,positions in POSITIONS.items() if str(position).upper() in positions),None)

def clean(value):
    return str(value) if pd.notna(value) else ''

def participation(value):
    value=clean(value).strip().lower()
    if value=='dnp' or value.startswith('did not'):return 'DNP'
    if value=='lp' or value.startswith('limited'):return 'LP'
    if value=='fp' or value.startswith('full'):return 'FP'
    return None

def non_injury(row):
    reason=' '.join(clean(row.get(k)) for k in ['report_primary_injury','practice_primary_injury']).lower()
    return any(term in reason for term in ['rest','not injury','non-injury','personal'])

def risk(row,history=(),on_ir=False):
    if on_ir:return 'Confirmed IR'
    if clean(row.get('report_status')).strip().lower()=='out':return 'Confirmed OUT'
    if non_injury(row):return None
    # A later LP/FP clears practice-based eligibility, including an undated feed update.
    if participation(row.get('practice_status')) in ['LP','FP']:return None
    if len(history)>=2 and all(p['status']=='DNP' and not p['non_injury'] for p in history[-2:]):
        if (pd.Timestamp(history[-1]['date'])-pd.Timestamp(history[-2]['date'])).days==1:
            return 'Two consecutive DNP reports'
    return None

def evidence_for(evidence,season,week,stamp,schedule):
    """Only explicitly dated, sourced reports count; retrievals are not practice days."""
    reports={};roster={}
    for kind in ['practice_reports','roster_status']:
        for record in evidence.get(kind,[]):
            if record.get('season')!=season or record.get('week')!=week:continue
            observed=pd.Timestamp(record['observed_at'])
            if observed.tzinfo is None:raise ValueError('Evidence observation time needs a timezone')
            if observed>stamp:continue
            if not record.get('source_url','').startswith('https://'):raise ValueError('Evidence requires an HTTPS source URL')
            team=record['team']
            if kind=='practice_reports':
                day=record['report_date'];date=pd.Timestamp(day)
                if date.strftime('%Y-%m-%d')!=day:raise ValueError('Practice report date must be YYYY-MM-DD')
                if date.date()>observed.tz_convert('America/New_York').date():raise ValueError('Practice report date is after its observation')
                games=schedule[schedule.season.eq(season)&schedule.week.eq(week)&(schedule.home_team.eq(team)|schedule.away_team.eq(team))]
                if 'gameday' in games and len(games):
                    kickoff=pd.Timestamp(games.iloc[0].gameday)
                    if not kickoff-pd.Timedelta(days=7)<=date<=kickoff:raise ValueError('Practice date is outside the game week')
                key=(team,day)
                if key not in reports or observed>pd.Timestamp(reports[key]['observed_at']):reports[key]=record
            else:
                # IR is explicit; generic RES, PUP, injury text or a return-to-practice window is insufficient.
                if record['status'] not in ['IR','Active']:raise ValueError('Roster evidence status must be IR or Active')
                effective=pd.Timestamp(record['effective_at'])
                if effective.tzinfo is None:raise ValueError('Roster effective time needs a timezone')
                if effective>stamp:continue
                key=(team,record['id']);order=(effective,observed)
                if key not in roster or order>(pd.Timestamp(roster[key]['effective_at']),pd.Timestamp(roster[key]['observed_at'])):roster[key]=record
    history={}
    for team in {key[0] for key in reports}:
        ordered=sorted((r for (t,_),r in reports.items() if t==team),key=lambda r:r['report_date'])
        identifiers={p['id'] for r in ordered for p in r['players']}
        for identifier in identifiers:
            days=[]
            for report in ordered:
                matches=[p for p in report['players'] if p['id']==identifier]
                if len(matches)>1:raise ValueError('Duplicate player in a daily report')
                player=matches[0] if matches else {}
                days.append({'date':report['report_date'],'status':participation(player.get('practice_status')),
                    'non_injury':non_injury(player),'source_url':report['source_url'],
                    'observed_at':report['observed_at'],**{'name':player.get('name',''),'position':player.get('position','')}})
            history[(team,identifier)]=days
    return history,roster,reports

def build(injuries,snaps,players,schedule,depth,season,week,as_of,baselines,reviews,source,evidence=None):
    if injuries.empty:
        injuries=injuries.reindex(columns=['season','week','team','gsis_id','full_name','position','report_status','practice_status'])
    ids=players[['pfr_id','gsis_id']].dropna().drop_duplicates('pfr_id',keep=False)
    snaps=snaps[snaps.season.eq(season)&snaps.week.lt(week)].merge(ids,left_on='pfr_player_id',right_on='pfr_id',how='left',validate='many_to_one')
    snaps['share']=snaps.offense_pct.fillna(0)+snaps.defense_pct.fillna(0)
    snaps['group']=snaps.position.map(group_for)
    # Top three prior-game shares retain healthy roles through a recent absence.
    roles=snaps.dropna(subset=['gsis_id']).groupby(['team','gsis_id']).agg(
        healthy_share=('share',lambda x:float(x.nlargest(3).median())),
        meaningful_games=('share',lambda x:int(x.ge(.4).sum())),
        last_week=('week','max'),position=('position','last')).to_dict('index')
    # Public player metadata distinguishes edge rushers listed generically as LB.
    precise=players.dropna(subset=['gsis_id']).drop_duplicates('gsis_id').set_index('gsis_id')
    for (team,identifier),role in roles.items():
        if role['position'] not in ['LB','OLB','DL']:continue
        if identifier in precise.index:
            position=clean(precise.loc[identifier].get('pff_position'))
            if position in ['ED','EDGE','DI','IDL','DL','LB']:role['position']=position
    stamp=pd.Timestamp(as_of)
    history,roster,daily_reports=evidence_for(evidence or {},season,week,stamp,schedule)
    if not depth.empty:
        depth=depth[pd.to_datetime(depth.dt,utc=True).le(stamp)].sort_values('dt').drop_duplicates(['team','gsis_id'],keep='last')
    starters={(r.team,r.gsis_id) for r in depth.itertuples() if r.pos_rank==1} if len(depth) else set()
    current=injuries[injuries.season.eq(season)&injuries.week.eq(week)].copy()
    upcoming=schedule[schedule.season.eq(season)&schedule.week.eq(week)&schedule.game_type.eq('REG')]
    playing=set(upcoming.home_team)|set(upcoming.away_team)
    teams=[];cards=[]
    for team in TEAMS:
        report=current[current.team.eq(team)];grouped={};unresolved=0
        candidates={r['gsis_id']:r for r in report.to_dict('records')}
        for (t,identifier),days in history.items():
            if t==team and identifier not in candidates:
                latest=next((d for d in reversed(days) if d['name']),days[-1])
                candidates[identifier]={'gsis_id':identifier,'full_name':latest['name'],'position':latest['position']}
        for (t,identifier),r in roster.items():
            if t==team and r['status']=='IR' and identifier not in candidates:
                candidates[identifier]={'gsis_id':identifier,'full_name':r['name'],'position':r['position']}
        for row in candidates.values():
            identifier=row.get('gsis_id');role=roles.get((team,identifier),{})
            if not role:unresolved+=1
            meaningful=(role.get('meaningful_games',0)>=2 and role.get('healthy_share',0)>=.4) or (team,identifier) in starters
            if not meaningful:continue
            group=group_for(role.get('position') or row.get('position'))
            if not group:continue
            days=history.get((team,identifier),[]);ir=roster.get((team,identifier),{})
            # A newly fetched old daily report must not override LP/FP in the latest feed.
            status=risk(row,days,ir.get('status')=='IR')
            if not status:continue
            sources=[]
            if status=='Confirmed IR':sources=[ir['source_url']]
            elif status=='Two consecutive DNP reports':sources=list(dict.fromkeys(d['source_url'] for d in days[-2:]))
            else:sources=[source['url']]
            grouped.setdefault(group,[]).append({'id':clean(identifier),'name':clean(row['full_name']),
                'position':role.get('position') or clean(row.get('position')),
                'healthy_share':role.get('healthy_share'),'status':status,
                'return_candidate':False,'report_status':clean(row.get('report_status')),'practice_status':clean(row.get('practice_status')),
                'observed_at':ir['observed_at'] if status=='Confirmed IR' else days[-1]['observed_at'] if status=='Two consecutive DNP reports' else source['fetched_at'],
                'practice_dates':[d['date'] for d in days[-2:]] if status=='Two consecutive DNP reports' else [],'source_urls':sources})
        for group,affected in grouped.items():
            if len(affected)<2:continue
            cards.append({'id':f'{season}-{week}-{team}-{group}','team':team,'group':group,'state':'Availability risk',
                'players':affected,'confidence':'Feed screening only; replacements and game status need review',
                'summary':'Multiple meaningful roles flagged. No automatic point adjustment.',
                'sources':[{'title':'Availability evidence','url':url} for url in dict.fromkeys(url for p in affected for url in p['source_urls'])],
                'observed_at':max((p['observed_at'] for p in affected if p['observed_at']),key=pd.Timestamp,default=None),'reviewed':False})
        reviewed=[r for r in reviews if r.get('team')==team and r.get('season')==season and r.get('week')==week]
        for r in reviewed:
            if r.get('group') not in POSITIONS:raise ValueError('Unknown reviewed position group')
            if not r.get('sources') or not r.get('observed_at'):raise ValueError('Reviewed cards require sources and observation time')
            if pd.Timestamp(r['observed_at'])>stamp:raise ValueError('Review uses future information')
            # Research commentary cannot bypass eligibility or reintroduce cleared players.
            for card in cards:
                if card['team']==team and card['group']==r['group']:
                    card.update({key:r[key] for key in ['summary','confidence','observed_at'] if key in r})
                    card['sources']+=r['sources'];card['reviewed']=True
        teams.append({'team':team,'name':TEAM_NAMES[team],
            'coverage':'Bye' if team not in playing else 'No current-week report' if report.empty else 'Latest report present; daily history / IR may be incomplete',
            'report_players':len(report),'unresolved_participation_ids':unresolved,
            'cards':sum(c['team']==team for c in cards)})
    return {'season':season,'week':week,'as_of':as_of,'source':source,
        'source_max_week':int(injuries.week.max()) if len(injuries) else None,
        'policy':'Only confirmed OUT/IR or two consecutive injury-related DNP daily reports in the game week qualify. Later LP/FP clears the DNP trigger. At least two meaningful players in a group are required. No automatic adjustments; returns remain manual scenarios.',
        'practice_history':{'team_daily_reports':len(daily_reports),'teams':len({t for t,_ in daily_reports}),
            'note':'The latest-status feed cannot establish consecutive DNPs. Dated source reports are required; missing days, players and repeated retrievals never count as DNPs.'},
        'baseline_policy':baselines,'teams':teams,'cards':cards,
        'mapping_coverage':{'snap_rows':len(snaps),'unmapped_snap_rows':int(snaps.gsis_id.isna().sum())}}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir',type=Path,required=True)
    parser.add_argument('--injury-dir',type=Path)
    parser.add_argument('--season',type=int,default=2026)
    parser.add_argument('--week',type=int,required=True)
    parser.add_argument('--refresh',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'_data/nfl_injury_watchlist.json')
    args=parser.parse_args();folder=args.injury_dir or args.cache_dir;folder.mkdir(parents=True,exist_ok=True)
    if args.refresh:
        for name,relative in [('injuries.parquet',f'injuries/injuries_{args.season}.parquet'),('players.parquet','players/players.parquet')]:
            url='https://github.com/nflverse/nflverse-data/releases/download/'+relative
            with urlopen(url,timeout=90) as response:raw=response.read()
            (folder/name).write_bytes(raw)
            (folder/(name+'.source.json')).write_text(json.dumps({'url':url,'fetched_at':datetime.now(timezone.utc).isoformat(),'sha256':hashlib.sha256(raw).hexdigest()}))
    source=json.loads((folder/'injuries.parquet.source.json').read_text())
    as_of=datetime.now(timezone.utc).isoformat()
    result=build(pd.read_parquet(folder/'injuries.parquet'),pd.read_parquet(args.cache_dir/'snap_counts.parquet'),
        pd.read_parquet(folder/'players.parquet'),pd.read_csv(args.cache_dir/'games.csv'),
        pd.read_parquet(args.cache_dir/'depth_charts.parquet'),args.season,args.week,as_of,
        json.loads((ROOT/'scripts/nfl_injury_baselines.json').read_text()),
        json.loads((ROOT/'scripts/nfl_injury_reviews.json').read_text())['reviews'],source,
        json.loads((ROOT/'scripts/nfl_injury_evidence.json').read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(f'Watchlist: {len(result["cards"])} candidate groups, {len(result["teams"])} team coverage records. No DEPI changes.')

if __name__=='__main__':main()
