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

def risk(row):
    if row.get('report_status') in ['Out','Doubtful']:return 'Likely absent'
    if row.get('report_status')=='Questionable':return 'Uncertain'
    reason=' '.join(clean(row.get(k)) for k in ['report_primary_injury','practice_primary_injury']).lower()
    if 'rest' in reason or 'not injury' in reason:return None
    if 'Did Not' in clean(row.get('practice_status')) or 'Limited' in clean(row.get('practice_status')):
        return 'Practice limitation; game status unconfirmed'
    return None

def build(injuries,snaps,players,schedule,depth,season,week,as_of,baselines,reviews,source):
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
    if not depth.empty:
        depth=depth[pd.to_datetime(depth.dt,utc=True).le(stamp)].sort_values('dt').drop_duplicates(['team','gsis_id'],keep='last')
    starters={(r.team,r.gsis_id) for r in depth.itertuples() if r.pos_rank==1} if len(depth) else set()
    current=injuries[injuries.season.eq(season)&injuries.week.eq(week)].copy()
    prior=injuries[injuries.season.eq(season)&injuries.week.eq(week-1)].drop_duplicates(['team','gsis_id'],keep='last')
    previous={(r.team,r.gsis_id):r._asdict() for r in prior.itertuples()}
    upcoming=schedule[schedule.season.eq(season)&schedule.week.eq(week)&schedule.game_type.eq('REG')]
    playing=set(upcoming.home_team)|set(upcoming.away_team)
    teams=[];cards=[]
    for team in TEAMS:
        report=current[current.team.eq(team)];grouped={};unresolved=0
        for row in report.to_dict('records'):
            identifier=row.get('gsis_id');role=roles.get((team,identifier),{})
            if not role:unresolved+=1
            meaningful=(role.get('meaningful_games',0)>=2 and role.get('healthy_share',0)>=.4) or (team,identifier) in starters
            if not meaningful:continue
            group=group_for(role.get('position') or row.get('position'))
            if not group:continue
            status=risk(row);old=previous.get((team,identifier),{})
            returning=old.get('report_status') in ['Out','Doubtful'] and not status
            if not status and not returning:continue
            grouped.setdefault(group,[]).append({'id':clean(identifier),'name':clean(row['full_name']),
                'position':role.get('position') or clean(row.get('position')),
                'healthy_share':role.get('healthy_share'),'status':status or 'Possible return; verify game availability',
                'return_candidate':returning,'report_status':clean(row.get('report_status')),'practice_status':clean(row.get('practice_status'))})
        for group,affected in grouped.items():
            if len(affected)<2:continue
            returns=sum(p['return_candidate'] for p in affected)
            trend='Potential improvement' if returns==len(affected) else 'Mixed losses / possible returns' if returns else 'Availability risk'
            cards.append({'id':f'{season}-{week}-{team}-{group}','team':team,'group':group,'state':trend,
                'players':affected,'confidence':'Feed screening only; replacements and game status need review',
                'summary':'Multiple meaningful roles flagged. No automatic point adjustment.',
                'sources':[{'title':'nflverse weekly reports','url':source['url']}],
                'observed_at':source['fetched_at'],'reviewed':False})
        reviewed=[r for r in reviews if r.get('team')==team and r.get('season')==season and r.get('week')==week]
        for r in reviewed:
            if r.get('group') not in POSITIONS:raise ValueError('Unknown reviewed position group')
            if not r.get('sources') or not r.get('observed_at'):raise ValueError('Reviewed cards require sources and observation time')
            if pd.Timestamp(r['observed_at'])>stamp:raise ValueError('Review uses future information')
            cards=[c for c in cards if not(c['team']==team and c['group']==r['group'])]
            cards.append({**r,'reviewed':True,'id':f'{season}-{week}-{team}-{r["group"]}'})
        teams.append({'team':team,'name':TEAM_NAMES[team],
            'coverage':'Bye' if team not in playing else 'No current-week report' if report.empty else 'Report present; IR/depth review pending',
            'report_players':len(report),'unresolved_participation_ids':unresolved,
            'cards':sum(c['team']==team for c in cards)})
    return {'season':season,'week':week,'as_of':as_of,'source':source,
        'source_max_week':int(injuries.week.max()) if len(injuries) else None,
        'policy':'Informational watchlist. No automatic adjustments. Missing reports are not evidence of health; IR/PUP and depth chains require sourced review.',
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
        json.loads((ROOT/'scripts/nfl_injury_reviews.json').read_text())['reviews'],source)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(f'Watchlist: {len(result["cards"])} candidate groups, {len(result["teams"])} team coverage records. No DEPI changes.')

if __name__=='__main__':main()
