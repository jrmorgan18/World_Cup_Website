#!/usr/bin/env python3
"""Rebuild the frozen Week 6 First and Five game-summary graphic.

Sources: the author's Week 6 draft and the Ravens' official October 18 recap.
This historical graphic is deliberately independent of live dashboard updates.
"""
from pathlib import Path
from html import escape
from generate_ravens_falcons_preview_graphics import text, card, WHITE, GOLD, MUTED, PURPLE

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/images/ravens/week-six-browns-2026/ravens-browns-week-six-at-a-glance.svg"

def render():
    cards = [
        ("0", "Points after drive two", "Final nine drives · Seven punts"),
        ("235", "Total offensive yards", "87 rushing · 148 net passing"),
        ("165", "Huntley passing yards", "19/31 · 1 TD · 0 interceptions"),
        ("5", "Ravens defensive sacks", "237 total yards allowed"),
        ("58", "Henry rushing yards", "17 carries · 3.4 per carry"),
        ("84", "Cuevas + Lane rec. yards", "Eight combined catches"),
    ]
    desc = ("Browns 13, Ravens 10. The Ravens fall to 4-2. They scored no points "
            "after the first two drives, finished with 235 offensive yards, and "
            "sacked Watson five times. Huntley passed for 165 yards, Henry rushed "
            "for 58, and Cuevas and Lane combined for 84 receiving yards.")
    body = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="720" viewBox="0 0 1200 720" role="img" aria-labelledby="title desc">',
        '<title id="title">Week 6 at a glance: Browns 13, Ravens 10</title>',
        f'<desc id="desc">{escape(desc)}</desc>',
        '<rect width="1200" height="720" fill="#09080c"/>',
        '<rect width="1200" height="130" fill="#1d1427"/><rect width="1200" height="8" fill="#7c4dc4"/>',
        text(50,43,"DUAL EIGHTS · FIRST AND FIVE · WEEK 6",18,PURPLE,800),
        text(50,85,"RAVENS 10 · BROWNS 13",36,WHITE,800),
        text(50,115,"Final · October 18, 2026 · The Ravens fall to 4–2",21,MUTED),
    ]
    for i, (value, label, note) in enumerate(cards):
        x = 50 + (i % 3) * 375
        y = 160 + (i // 3) * 245
        body += [
            card(x,y,350,210),
            text(x+25,y+65,value,49,GOLD,800),
            text(x+25,y+110,label,23,WHITE,800),
            text(x+25,y+165,note,20,MUTED),
        ]
    body += [
        text(50,695,"SOURCES: AUTHOR’S WEEK 6 DRAFT · BALTIMORERAVENS.COM OFFICIAL RECAP / GAME CENTER",17,MUTED),
        "</svg>",
    ]
    return "\n".join(body) + "\n"

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")
    print(f"Generated {OUT.name}")
