#!/usr/bin/env python3
"""Render the Week 6 preview's frozen article statistics in the existing design."""
import json
from html import escape
from pathlib import Path
from generate_ravens_falcons_preview_graphics import text, card, WHITE, GOLD, MUTED, PURPLE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/images/ravens/browns-week-six-2026"


def frame(title, subtitle, body, desc, footer, height=720):
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>',
        f'<rect width="1200" height="{height}" fill="#09080c"/>',
        '<rect width="1200" height="130" fill="#1d1427"/><rect width="1200" height="8" fill="#7c4dc4"/>',
        text(50,43,"DUAL EIGHTS · WEEK 6",18,PURPLE,800),
        text(50,85,title,36,WHITE,800), text(50,115,subtitle,21,MUTED), body,
        text(50,height-25,footer,17,MUTED), "</svg>\n"
    ])


def overview(data):
    body = ""
    for x, team, label in [(50,"BAL","THE RAVENS"), (615,"CLE","BROWNS")]:
        row = data["overview"][team]
        body += card(x,160,535,350) + text(x+25,204,label,27,GOLD,800)
        body += text(x+510,204,row["record"],30,WHITE,800,"end")
        for dx, key, label in [(25,"ppg","Points / game"),(285,"ypp","Yards / play")]:
            body += text(x+dx,277,f'{row[key]:.1f}',46,WHITE,800)
            body += text(x+dx,318,label,23,WHITE,700)
        body += f'<path d="M{x+25} 348 H{x+510}" stroke="#493555"/>'
        for dx, key, label, color in [(25,"efficiency_rank","Efficiency Index",PURPLE),
                                      (285,"depi_rank","DEPI",GOLD)]:
            body += text(x+dx,412,f'#{row[key]}',43,color,800)
            body += text(x+dx,450,label,23,WHITE,800)
        body += text(x+25,484,"LEAGUE RANKS · THROUGH WEEK 5",18,MUTED,700)
    for i,(number,label,line1,line2) in enumerate([
        ("2nd","Huntley start in a row","Lamar Jackson ruled out","Backup won in Atlanta"),
        ("476","Henry rushing yards","113 carries · 4.2 per carry","A different run-defense test"),
        ("19","Cleveland sacks allowed","Eight against the Jets","An opening for Hendrickson")
    ]):
        x=50+i*375
        body += card(x,545,350,200)+text(x+25,600,number,43,GOLD,800)
        body += text(x+25,640,label,23,WHITE,800)+text(x+25,683,line1,20,MUTED)+text(x+25,717,line2,20,MUTED)
    return frame("RAVENS at BROWNS","Sunday, October 18 · 1 PM ET · Huntington Bank Field · FOX",body,
                 f'The Ravens are 4-1, score 29.2 points per game with 6.4 yards per play, and rank No. {data["overview"]["BAL"]["efficiency_rank"]} in the Efficiency Index and No. {data["overview"]["BAL"]["depi_rank"]} in DEPI. Cleveland is 3-2, scores 18.6 points per game with 4.7 yards per play, and ranks No. {data["overview"]["CLE"]["efficiency_rank"]} in Efficiency and No. {data["overview"]["CLE"]["depi_rank"]} in DEPI. Team ranks are through completed Week 5. Huntley starts again with Jackson out.',
                 "SOURCES: DUAL EIGHTS RANKINGS · SHARP FOOTBALL · AUTHOR’S PREVIEW · OFFICIAL GAME INFO",850)


def ground(data):
    bal,cle=data["article_reported"]["BAL"],data["article_reported"]["CLE"]
    body=card(50,160,1100,300)+text(80,206,"EXPLOSIVE DESIGNED RUNS · GAINS OF 10+ YARDS",25,WHITE,800)
    for y,label,value,rank,color in [
        (248,"THE RAVENS OFFENSE",bal["rush_explosive_pct"],bal["rush_explosive_rank"],GOLD),
        (345,"BROWNS DEFENSE · ALLOWED",cle["rush_explosive_allowed_pct"],cle["rush_explosive_allowed_rank"],PURPLE)
    ]:
        body+=text(80,y,label,21,WHITE,800)+text(1115,y,f"{value:.1f}% · #{rank}",29,color,800,"end")
        body+=f'<rect x="80" y="{y+20}" width="1035" height="28" rx="5" fill="#30253b"/>'
        body+=f'<rect x="80" y="{y+20}" width="{1035*value/20:.1f}" height="28" rx="5" fill="{color}"/>'
    for x,label,rank,note in [(50,"RAVENS RUSHING EPA",bal["rush_epa_rank"],"Offensive rank"),
                               (615,"BROWNS RUSHING EPA ALLOWED",cle["rush_def_epa_rank"],"Defensive rank")]:
        body+=card(x,490,535,145)+text(x+25,530,label,23,WHITE,800)
        body+=text(x+25,598,f"#{rank}",47,GOLD,800)+text(x+150,590,note,23,MUTED)
    return frame("THE GROUND-GAME OPENING","A productive rushing offense meets Cleveland’s explosive-run problem.",body,
                 "As reported in the preview: the Ravens generate explosive runs on 13.3 percent of designed rushes, fifth in the league. Cleveland allows them on 15.7 percent, last. Rushing EPA ranks: Ravens offense fifth; Browns defense 28th.",
                 "SOURCE: FIGURES AND RANKS REPORTED IN THE AUTHOR’S PREVIEW · THROUGH FIVE GAMES")


def pressure(data):
    bal,cle=data["article_reported"]["BAL"],data["article_reported"]["CLE"]
    body=""
    for x,label,value,note in [
        (50,"BROWNS SACK RATE ALLOWED",f'{cle["sack_rate_allowed"]:.1f}%',"32nd in the NFL · Lower is better"),
        (615,"RAVENS DEFENSIVE SACK RATE",f'{bal["sack_rate"]:.1f}%',"21st in the NFL · Higher is better")
    ]:
        body+=card(x,160,535,215)+text(x+25,203,label,23,WHITE,800)
        body+=text(x+25,279,value,53,GOLD,800)+text(x+25,342,note,22,MUTED)
    for i,(value,label,note) in enumerate([
        (str(cle["sacks_allowed"]),"Sacks allowed","Eight in last week’s loss"),
        (f'{cle["third_down_pct"]:.1f}%',"Third-down conversions","30th in the NFL"),
        (f'{cle["red_zone_td_pct"]:.1f}%',"Red-zone TD rate","31st in the NFL")
    ]):
        x=50+i*375
        body+=card(x,420,350,210)+text(x+25,480,value,45,GOLD,800)
        body+=text(x+25,529,label,23,WHITE,800)+text(x+25,589,note,21,MUTED)
    return frame("HENDRICKSON’S OPENING","Cleveland’s protection and drive-finishing problems create an opportunity.",body,
                 "Cleveland has allowed 19 sacks, with a league-worst 10.3 percent sack rate allowed. The Ravens sack opponents on 5.1 percent of dropbacks. Cleveland converts 30.6 percent of third downs and scores touchdowns on 45.5 percent of red-zone trips.",
                 "SOURCES: AUTHOR’S PREVIEW · SHARP FOOTBALL (THIRD DOWNS) · THROUGH FIVE GAMES")


def injuries():
    body=""
    for x,label,out,questionable in [
        (50,"THE RAVENS",["Lamar Jackson · Ankle","Cam Jurgens · Concussion","Matthew Hibner · Hand","Broderick Washington · Ankle"],
         ["Andrew Vorhees · Foot","Emery Jones Jr. · Ankle","Ja’Kobi Lane · Wrist"]),
        (615,"BROWNS",["Mike Hall Jr. · Ankle","Kalia Davis · Quad","Teven Jenkins · Back"],
         ["Mason Graham · Knee / ankle","Carson Schwesinger · Ankle","Quinshon Judkins · Ankle","Derek Barnett · Ankle"])
    ]:
        body+=card(x,160,535,550)+text(x+25,205,label,28,GOLD,800)
        body+=text(x+25,250,"OUT",20,"#f3badc",800)
        for i,line in enumerate(out): body+=text(x+25,290+i*35,line,24)
        body+=text(x+25,425,"QUESTIONABLE",20,GOLD,800)
        for i,line in enumerate(questionable): body+=text(x+25,466+i*35,line,24)
    body+=text(50,755,"Hendrickson has no game designation after a full practice week.",23,MUTED)
    body+=text(50,790,"Selected matchup-relevant players · Check Sunday’s inactive lists for final availability.",20,MUTED)
    return frame("FRIDAY AVAILABILITY CHECK","Official game designations · October 16, 2026",body,
                 "Selected Friday statuses: Ravens Jackson, Jurgens, Hibner and Washington out; Vorhees, Jones and Lane questionable. Browns Hall, Davis and Jenkins out; Graham, Schwesinger, Judkins and Barnett questionable. Hendrickson has no designation.",
                 "SOURCES: RAVENS AND BROWNS OFFICIAL FRIDAY INJURY REPORTS",850)


def main():
    data=json.loads((OUT/"preview-stat-sources.json").read_text(encoding="utf-8"))
    assert data["season"]==2026 and data["through_week"]==5
    assert data["ranking_snapshot"]["rating_week"] == data["through_week"]
    assert data["ranking_snapshot"]["rating_week_complete"] is True
    for name,svg in [("at-a-glance",overview(data)),("ground-game",ground(data)),
                     ("pressure",pressure(data)),("injuries",injuries())]:
        (OUT/f"ravens-browns-{name}.svg").write_text(svg,encoding="utf-8")
    print("Generated four Ravens–Browns preview graphics from the frozen source snapshot.")


if __name__=="__main__":
    main()
