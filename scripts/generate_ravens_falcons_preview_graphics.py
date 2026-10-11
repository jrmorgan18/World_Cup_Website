#!/usr/bin/env python3
"""Rebuild frozen Week 5 preview graphics; --capture freezes public Sumer tables.

Uses the existing previews' black, purple and gold design. Does not change the
dashboard. Column ranks use published rounded values; EPA/play ranks preserve
the source's ordering. See preview-stat-sources.json for provenance and inputs.
"""
import argparse
import json
import re
from html import escape, unescape
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/images/ravens/falcons-week-five-2026'
SNAPSHOT = OUT / 'preview-stat-sources.json'
WHITE, GOLD, MUTED, PURPLE = '#f7f4fb', '#e8bc55', '#cfc8d5', '#9b6ee6'
SHARP = 'https://www.sharpfootballanalysis.com/fantasy/ravens-falcons-week-5-fantasy-football-preview-nfl-worksheet-rich-hribar-2026/'
TEAM_NAMES = {'BAL':'Baltimore Ravens', 'ATL':'Atlanta Falcons'}

def text(x,y,value,size=24,fill=WHITE,weight=600,anchor='start'):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>'

def card(x,y,w,h):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="#17131d" stroke="#49315f" stroke-width="2"/>'

def frame(title,subtitle,body,description,footer,height=720):
    return '\n'.join([
      f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">',
      f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
      f'<rect width="1200" height="{height}" fill="#09080c"/>',
      '<rect width="1200" height="130" fill="#1d1427"/><rect width="1200" height="8" fill="#7c4dc4"/>',
      text(50,43,'DUAL EIGHTS · WEEK 5',18,PURPLE,800),
      text(50,85,title,36,WHITE,800),text(50,115,subtitle,21,MUTED),body,
      text(50,height-25,footer,17,MUTED),'</svg>\n'])

def write(name,svg):
    (OUT/f'ravens-falcons-{name}.svg').write_text(svg,encoding='utf-8')

def capture():
    tables={}
    for side in ('offensive','defensive'):
        url=f'https://sumersports.com/teams/{side}/'
        source=urlopen(url).read().decode()
        assert '10-09-2026' in source, 'Refuse to overwrite this historical sample with a different update date'
        table=re.search(r'<table.*?</table>',source,re.S).group()
        rows=[]
        for row in re.findall(r'<tr.*?</tr>',table,re.S):
            vals=[' '.join(unescape(re.sub('<[^>]+>',' ',cell)).split())
                  for cell in re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.S)]
            if vals:
                assert vals[1]=='2026'
                rows.append({'team':re.sub(r'^\d+\s*\.\s*','',vals[0]),
                  'epa_rank':int(re.match(r'^\d+',vals[0]).group()),
                  'epa':float(vals[2]),'success':float(vals[4].rstrip('%')),
                  'pass_epa':float(vals[5]),'rush_epa':float(vals[6])})
        assert len(rows)==32 and len({r['team'] for r in rows})==32
        tables[side]={'url':url,'updated':'2026-10-09 10:35 AM EST','teams':rows}
    data={'season':2026,'through_week':4,'matchup_week':5,'tables':tables,
      'rank_method':'EPA/play: published ordering. Other metrics: minimum rank from displayed rounded values; ties share rank. Higher is better on offense; lower opponent production is better on defense.',
      'sources':{'situational':SHARP,'official_matchup':'https://www.baltimoreravens.com/game-day/2026/reg-week5/ravens-at-falcons/media'},
      'reported':{
        'BAL':{'record':'3–1','points_per_game':29.0,'yards_per_play':6.6,'third_long_converted':2,'third_long_attempts':17},
        'ATL':{'record':'2–2','points_per_game':24.0,'yards_per_play':5.9,'rush_yards_allowed':193,'rush_ypc_allowed':2.72,'pressure_rate':46.3,'three_and_out_rate':29.5,'bijan_rush_yards':494,'bijan_rush_attempts':85},
        'Huntley_Week4':{'completions':8,'attempts':9,'yards':63,'offensive_possessions':5,'points':0}}}
    SNAPSHOT.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')

def overview(data):
    body=''
    for x,abbr,label in [(50,'BAL','THE RAVENS'),(615,'ATL','FALCONS')]:
        row=data['reported'][abbr]
        body+=card(x,160,535,225)+text(x+25,204,label,27,GOLD,800)+text(x+510,204,row['record'],30,WHITE,800,'end')
        body+=text(x+25,270,f"{row['points_per_game']:.1f}",44,WHITE,800)+text(x+280,270,f"{row['yards_per_play']:.1f}",44,WHITE,800)
        body+=text(x+25,310,'Points / game',24)+text(x+280,310,'Yards / play',24)
        body+=text(x+25,354,'OFFENSE · FIRST FOUR GAMES',18,PURPLE,800)
    for i,(value,label,line1,line2) in enumerate([
      ('8 / 9','Huntley vs. Tennessee','63 passing yards','No points on five possessions'),
      ('193','ATL rushing yards allowed','Fewest in the NFL','Through four games'),
      ('46.3%','ATL pressure rate','League-leading rate','Sharp Football charting')]):
        x=50+i*375
        body+=card(x,420,350,210)+text(x+25,478,value,44,GOLD,800)+text(x+25,522,label,22,WHITE,800)
        body+=text(x+25,567,line1,21,MUTED)+text(x+25,599,line2,20,MUTED)
    write('at-a-glance',frame('RAVENS at FALCONS','Sunday, October 11 · 8:20 PM ET · Mercedes-Benz Stadium · NBC / Peacock',body,
      'Through Week 4: Ravens 3–1, 29 points per game and 6.6 yards per play; Falcons 2–2, 24 points and 5.9 yards per play. Atlanta has allowed 193 rushing yards and generates pressure on 46.3 percent of dropbacks. Huntley completed eight of nine for 63 yards against Tennessee; the offense scored no points in five possessions.',
      'SOURCES: SHARP FOOTBALL ANALYSIS · SUMERSPORTS · THROUGH WEEK 4'))

def metric_rank(rows,team,key,defense):
    current=next(r for r in rows if r['team']==team)
    if key=='epa':return current['epa_rank']
    return 1+sum((r[key]<current[key]) if defense else (r[key]>current[key]) for r in rows)

def matchup(data):
    metrics=[('epa','EPA / play'),('success','Success rate'),('pass_epa','Pass EPA / play'),('rush_epa','Rush EPA / play')]
    body=''; desc=[]
    for y,kicker,left,right in [(160,'WHEN THE RAVENS HAVE THE BALL','BAL','ATL'),(595,'WHEN THE FALCONS HAVE THE BALL','ATL','BAL')]:
        body+=card(50,y,1100,405)+text(75,y+35,kicker,20,PURPLE,800)
        body+=text(75,y+75,('THE RAVENS' if left=='BAL' else 'FALCONS')+' OFFENSE',27,WHITE,800)
        body+=text(1125,y+75,('THE RAVENS' if right=='BAL' else 'FALCONS')+' DEFENSE',27,WHITE,800,'end')
        for i,(key,label) in enumerate(metrics):
            ry=y+110+i*67
            if i%2==0:body+=f'<rect x="52" y="{ry}" width="1096" height="67" fill="#201929"/>'
            body+=text(600,ry+43,label,25,WHITE,700,'middle')
            for x,side,team in [(75,'offensive',left),(835,'defensive',right)]:
                rows=data['tables'][side]['teams']; row=next(r for r in rows if r['team']==TEAM_NAMES[team])
                rank=metric_rank(rows,TEAM_NAMES[team],key,side=='defensive')
                value=f"{row[key]:.2f}%" if key=='success' else f"{row[key]:+.2f}"
                fill,ink=(GOLD,'#18121f') if rank<=8 else (('#7d58b3',WHITE) if rank<=16 else ('#394052','#dce0e8'))
                body+=text(x,ry+43,value,30,WHITE,800)+f'<rect x="{x+198}" y="{ry+18}" width="86" height="35" rx="17" fill="{fill}"/>'
                body+=text(x+241,ry+43,f'#{rank}',23,ink,800,'middle')
                desc.append(f'{team} {side} {label}: {value}, rank {rank}')
    body+=text(50,1038,'EPA = expected points added · Defense values are opponent production',20,MUTED)
    body+=text(50,1069,'Full team samples include Lamar / Rush starts; this is not a lineup projection.',20,MUTED)
    write('matchup-dna',frame('RAVENS × FALCONS: MATCHUP DNA','2026 through Week 4 · #1 best · Gold = top eight · Ties share rank',body,'; '.join(desc),
      'SOURCE: SUMERSPORTS PUBLIC TABLES · UPDATED OCTOBER 9 · UNADJUSTED EPA',1125))

def key_matchups(data):
    body=''
    for x,title,value1,label1,value2,label2,note in [
      (50,'HENRY vs. ATL RUN DEFENSE','193','Rush yards allowed','2.72','Yards / carry allowed','Fewest rushing yards in the NFL'),
      (615,'BIJAN vs. THE RAVENS','494','Bijan rushing yards','5.8','Bijan yards / carry','The Ravens allow 100 rush yards / game')]:
        body+=card(x,160,535,235)+text(x+25,201,title,24,GOLD,800)
        body+=text(x+25,263,value1,43,WHITE,800)+text(x+290,263,value2,43,WHITE,800)
        body+=text(x+25,305,label1,22)+text(x+290,305,label2,22)+text(x+25,365,note,21,MUTED)
    body+=card(50,430,1100,200)+text(80,470,'ATLANTA DEFENSE: EPA ALLOWED',25,WHITE,800)
    zero,scale=770,800
    body+=f'<line x1="{zero}" y1="485" x2="{zero}" y2="595" stroke="{MUTED}"/>'
    for y,label,value,color in [(492,'Rush',-.28,PURPLE),(552,'Pass',-.02,GOLD)]:
        end=zero+value*scale
        body+=text(80,y+23,label,27,WHITE,800)+f'<rect x="{end}" y="{y}" width="{abs(value*scale)}" height="30" rx="4" fill="{color}"/>'
        body+=text(1080,y+24,f'{value:+.2f}',30,color,800,'end')
    body+=text(80,612,'Negative EPA favors the defense.',19,MUTED)
    write('key-matchups',frame('TWO VERY DIFFERENT RUN-GAME TESTS','Stopping Henry is Atlanta’s strength. Containing Robinson is the Ravens’ challenge.',body,
      'Through four games, Atlanta has allowed 193 rushing yards and 2.72 yards per carry. Bijan Robinson has 494 yards on 85 carries, 5.8 per attempt. The Ravens allow 100 rushing yards per game. Atlanta allows -0.28 EPA per rush and -0.02 per pass.',
      'SOURCES: SUMERSPORTS · SHARP FOOTBALL ANALYSIS · THROUGH WEEK 4'))

def margin(data):
    body=card(50,160,1100,250)
    body+=text(80,204,'THE RAVENS ON THIRD-AND-LONG',26,WHITE,800)+text(80,263,'2 of 17',48,GOLD,800)
    body+=text(370,254,'11.8% converted',32,WHITE,800)+text(370,293,'Seven or more yards needed',23,MUTED)
    for i in range(17):
        body+=f'<rect x="{80+i*61}" y="330" width="49" height="42" rx="5" fill="{GOLD if i<2 else "#3d304c"}"/>'
    body+=text(80,398,'Gold = converted · Purple = failed',19,MUTED)
    body+=card(50,445,535,190)+text(80,503,'29.5%',46,GOLD,800)+text(80,547,'ATL defensive three-and-outs',25,WHITE,800)+text(80,595,'Fourth-highest rate in the NFL',23,MUTED)
    body+=card(615,445,535,190)+text(645,503,'32.5%',46,PURPLE,800)+text(645,547,'Ravens sets reaching third down',25,WHITE,800)+text(645,595,'Lowest rate in the NFL',23,MUTED)
    write('margin-for-error',frame('STAY OUT OF THIRD-AND-LONG','Early-down execution matters even more with a backup quarterback.',body,
      'The Ravens have converted two of 17 third downs needing seven or more yards, 11.8 percent. Atlanta forces three-and-outs on 29.5 percent of drives, fourth in the NFL. Only 32.5 percent of Ravens sets of downs reach third down, the lowest rate.',
      'SOURCE: SHARP FOOTBALL ANALYSIS · THROUGH WEEK 4 · THIRD-AND-LONG = 7+ YARDS'))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--capture',action='store_true'); args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.capture:capture()
    data=json.loads(SNAPSHOT.read_text(encoding='utf-8'))
    assert data['season']==2026 and data['through_week']==4
    for table in data['tables'].values():assert len(table['teams'])==32
    overview(data);matchup(data);key_matchups(data);margin(data)
    print('Generated four Week 5 preview graphics from the frozen Week 4 source snapshot.')

if __name__=='__main__':main()
