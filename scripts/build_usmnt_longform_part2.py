"""Build Part 2 of the flagship USMNT long read from its Word manuscript."""

from pathlib import Path
import math
import re

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "articles" / "Why the USMNT Will Never be Argentina (but could maybe be France) - Part 2.docx"
OUTPUT = ROOT / "_posts" / "2026-07-21-why-the-usmnt-will-never-be-argentina-part-2.md"


def citation(number: int, suffix: str = "") -> str:
    ref_id = f"ref-{number}{suffix}"
    return f'<sup id="{ref_id}"><a href="#note-{number}" aria-label="See note {number}">{number}</a></sup>'


CITATIONS = {
    7: citation(1),
    11: citation(2),
    15: citation(3, "a"),
    22: citation(4),
    39: citation(5),
    40: citation(6),
    47: citation(7),
    57: citation(8),
    72: citation(9, "a"),
    73: citation(9, "b"),
    74: citation(9, "c"),
    76: citation(10),
    87: citation(11, "a"),
    89: citation(11, "b"),
    94: citation(12),
    96: citation(13),
    99: citation(14),
    109: citation(15),
    110: citation(16, "a"),
    113: citation(17),
    131: citation(18),
    136: citation(19),
    139: citation(20),
    142: citation(21),
    148: citation(22),
    157: citation(23),
    158: citation(24),
    173: citation(25, "a"),
    174: citation(26),
    175: citation(27),
    178: citation(25, "b"),
    181: citation(28),
    184: citation(29),
    189: citation(30),
    194: citation(31),
    195: citation(32),
    198: citation(33, "a"),
    199: citation(33, "b"),
    203: citation(34),
    205: citation(16, "b"),
    206: citation(3, "b"),
    208: citation(33, "c"),
}


REWRITES = {
    15: "For the 2024–25 season the federation evaluated the academies of thirty-three professional clubs, all eighteen Ligue 1 sides plus eleven from Ligue 2 and a handful from the third tier. It did not rank them on their facilities. It did not rank them on how many under-15 tournaments they won. It ranked them on how many players signed professional contracts, how many minutes academy graduates played for the first team, how many reached national teams, how many completed their schooling and how many appeared in Europe’s five biggest leagues.",
    39: "A season of youth soccer at a French amateur club typically runs somewhere around a hundred to a hundred and sixty euros, all in. That is the federation’s cut plus the club’s dues. For an eligible teenager, the state’s seventy-euro Pass’Sport voucher can cover much of it.",
    47: "Of the 99 players across this World Cup’s national-team rosters who were born in France, 54 were born in Île-de-France.",
    158: "Spain did not need to invent soccer knowledge. It needed to let girls in on the knowledge it already had. England did not need to build a football culture. It needed to stop banning half its population from the one it built first. And France, of course, is running the full program. Record numbers of registered girls, a professional women’s league structure stood up in 2024, the same federation apparatus I described in the last part, now being aimed at a new population. Women are still barely a tenth of French licenses, which tells you how early in the process they are, and the team is already ranked sixth in the world. The machine works on whoever it is pointed at. That was always the point of the machine.",
    195: "American families already spend billions of dollars a year on youth sports, and soccer is among the most expensive mass-participation games in that economy, much of it flowing into the exact pay-to-play machine this essay has been taking apart. That is before you count a thirty-club MLS whose revenues and franchise values now run into the billions. Two hundred million dollars is a serious public commitment. Against the scale of the industry it would repair, it is not a fantasy number.",
}


HEADINGS = {
    3: ("01", "the-french-model", "The French Model"),
    70: ("02", "the-missing-rung", "The Missing Rung"),
    130: ("03", "the-head-start", "The Head Start"),
    166: ("04", "the-build", "The Build"),
    214: ("05", "growing-into-it", "Growing Into It"),
}


PULLS = {
    18: ("France built the form.", False),
    26: ("There is no search. There is a market.", True),
    54: ("The trouble is the hallway that leads to it.", False),
    63: ("The gap between the building and the harvest is the whole ballgame.", True),
    83: ("That is the rung.", False),
    119: ("The most complete American pathway still depends on another country’s league for the final stages.", True),
    143: ("In the women’s game everybody started at once, and we started with a system already built.", False),
    163: ("The women were handed a head start. The men are going to have to build one by hand.", True),
    180: ("Hire the American three hundred.", False),
    204: ("Eighteen months of litigation between American soccer’s federation and the only institution building free soccer fields in poor neighborhoods.", True),
    211: ("The build is not a mystery. It is the accident, made deliberate.", False),
    226: ("Children grow because time passes. Institutions do not.", True),
    244: ("Inheritance is not the only way to leave something behind.", False),
}


AFTER = {
    8: """
<figure class="longform-figure">
  <img src="{{ '/assets/images/usmnt-longform-part2-clairefontaine.jpg' | relative_url }}" alt="The Château de Montjoye at France's national football center in Clairefontaine" loading="lazy">
  <figcaption><strong>The postcard—and the decoy</strong>The Château de Montjoye at Clairefontaine is the image most often used to explain French development. The real machine is the national system operating far beyond its gates. Photo: Xavoun, CC BY-SA 3.0 / <a href="https://commons.wikimedia.org/wiki/File:Ch%C3%A2teau_de_Montjoye.jpg" target="_blank" rel="noopener">Wikimedia Commons</a>.</figcaption>
</figure>
""",
    22: """
<aside class="longform-stat">
  <div class="longform-stat-grid">
    <div class="longform-stat-item"><strong>33</strong><span>professional academies evaluated on long-term player outcomes</span></div>
    <span class="longform-stat-divider" aria-hidden="true"></span>
    <div class="longform-stat-item"><strong>300+</strong><span>technical advisers embedded across France’s football map</span></div>
  </div>
  <p>The academy is the building. The search network is the system.</p>
</aside>
""",
    40: """
<aside class="longform-stat">
  <div class="longform-stat-grid">
    <div class="longform-stat-item"><strong>€100–160</strong><span>typical annual entry at a French amateur club</span></div>
    <span class="longform-stat-divider" aria-hidden="true"></span>
    <div class="longform-stat-item"><strong>$1,188</strong><span>average annual U.S. family spend on a child’s primary soccer participation</span></div>
  </div>
  <p>Before anyone evaluates talent, America has already evaluated the family’s wallet.</p>
</aside>
""",
    77: """
<div class="longform-archive" role="group" aria-label="Cavan Sullivan and Freddy Adu, American prodigies twenty years apart">
  <div class="longform-archive-grid">
    <figure><img src="{{ '/assets/images/usmnt-longform-part2-cavan-sullivan.jpg' | relative_url }}" alt="Cavan Sullivan dribbling for the Philadelphia Union in 2025" loading="lazy"><span>Cavan Sullivan · 2025</span></figure>
    <figure><img src="{{ '/assets/images/usmnt-longform-part2-freddy-adu.jpg' | relative_url }}" alt="Freddy Adu playing for the United States in 2011" loading="lazy"><span>Freddy Adu · 2011</span></figure>
  </div>
  <p><strong>Two prodigies, two systems.</strong> Sullivan entered a genuine academy with a mapped route to Europe. Adu entered a league that knew how to debut a fourteen-year-old but not yet how to finish one. Photos: Bryan Berlin, CC BY-SA 4.0 (<a href="https://commons.wikimedia.org/wiki/File:Cavan_Sullivan_Philadelphia_Chicago_10.26.25-117.jpg" target="_blank" rel="noopener">Sullivan</a>); 2O, CC BY-SA 3.0 (<a href="https://commons.wikimedia.org/wiki/File:Freddy_Adu_20110622.jpg" target="_blank" rel="noopener">Adu</a>).</p>
</div>
""",
    91: """
<aside class="longform-stat">
  <div class="longform-stat-grid">
    <div class="longform-stat-item"><strong>7.8%</strong><span>of Ligue 1 minutes to France-eligible under-21 players</span></div>
    <span class="longform-stat-divider" aria-hidden="true"></span>
    <div class="longform-stat-item"><strong>2.4%</strong><span>of Premier League minutes to England-eligible under-21 players</span></div>
  </div>
  <p>A development league does not have to be the richest league. It has to make room.</p>
</aside>
""",
    143: """
<div class="longform-archive longform-archive--history" role="group" aria-label="Women's soccer in Europe in 1920 and the United States in 1999">
  <div class="longform-archive-grid">
    <figure><img src="{{ '/assets/images/usmnt-longform-part2-dick-kerr-ladies.jpg' | relative_url }}" alt="The captains of England's Dick, Kerr Ladies and France greet before a 1920 international" loading="lazy"><span>Europe · 1920</span></figure>
    <figure><img src="{{ '/assets/images/usmnt-longform-part2-uswnt-1999.jpg' | relative_url }}" alt="The 1999 World Cup-winning USWNT presents President Bill Clinton with a jersey at the White House" loading="lazy"><span>United States · 1999</span></figure>
  </div>
  <p><strong>While America built, Europe banned.</strong> A women’s international drew 53,000 at Goodison Park in 1920; the English FA barred women from affiliated grounds a year later. By 1999, an American system opened by Title IX had produced its second world champion. Photos: Nationaal Archief, public domain (<a href="https://commons.wikimedia.org/wiki/File:Dick,_Kerr%27s_Ladies_kiss.jpg" target="_blank" rel="noopener">1920</a>); Ralph Alswang / White House Photograph Office, public domain via the <a href="https://commons.wikimedia.org/wiki/File:The_U._S._A._Women%27s_Soccer_Team_presents_President_Clinton_a_%22CLINTON_99%22_soccer_shirt_-_DPLA_-_23f4de7d4c003aa7fbe63c6845daaac5.jpg" target="_blank" rel="noopener">National Archives</a>.</p>
</div>
""",
    199: """
<figure class="longform-figure">
  <img src="{{ '/assets/images/usmnt-longform-part2-mini-pitch-night.jpg' | relative_url }}" alt="Two neighborhood mini-pitches illuminated at night" loading="lazy">
  <figcaption><strong>Manufacturing Wednesday</strong>Lights turn a small court into hours of additional play after school and work. The Foundation reports that lighting adds an average of 2.75 playing hours per pitch per day. Photo: Courtesy of the <a href="https://ussoccerfoundation.org/programs/safe-places-to-play/" target="_blank" rel="noopener">U.S. Soccer Foundation</a>.</figcaption>
</figure>
""",
    200: """
<figure class="longform-figure">
  <img src="{{ '/assets/images/usmnt-longform-part2-mini-pitch-play.jpg' | relative_url }}" alt="Children, including a power-wheelchair player, play together on an accessible mini-pitch" loading="lazy">
  <figcaption><strong>A field that admits everyone</strong>A hard-court mini-pitch with accessible gates creates the kind of ordinary, repeatable opportunity the market fails to deliver. Photo: Courtesy of the <a href="https://ussoccerfoundation.org/programs/safe-places-to-play/" target="_blank" rel="noopener">U.S. Soccer Foundation</a>.</figcaption>
</figure>
""",
    242: """
<figure class="longform-figure">
  <img src="{{ '/assets/images/usmnt-longform-part2-mini-pitch-community.jpg' | relative_url }}" alt="A coach lifts a young player as families celebrate around a neighborhood mini-pitch" loading="lazy">
  <figcaption><strong>The accident, made ordinary</strong>The point is not to promise every child a professional career. It is to stop making knowledge, a field and a way into the game depend on luck. Photo: Courtesy of the <a href="https://ussoccerfoundation.org/programs/safe-places-to-play/" target="_blank" rel="noopener">U.S. Soccer Foundation</a>.</figcaption>
</figure>
""",
}


NOTES = [
    "Clairefontaine’s history and role are documented by the <a href=\"https://www.fff.fr/article/1098-11-juin-1988-centre-decisif-a-clairefontaine.html\" target=\"_blank\" rel=\"noopener\">French Football Federation</a>. The INF’s small, regional intake, weekday boarding and weekend return to home clubs are described in the federation’s academy materials.",
    "France’s approved professional training centers operate under a state-and-federation framework covering schooling, sport, medical care, housing and staffing; approval can be withdrawn. See the <a href=\"https://www.sports.gouv.fr/formation-au-sein-des-clubs-professionnels-779\" target=\"_blank\" rel=\"noopener\">French Ministry of Sport</a>.",
    "The FFF’s <a href=\"https://www.fff.fr/article/14929-l-evaluation-2024-2025-des-centres-de-formation.html\" target=\"_blank\" rel=\"noopener\">2024–25 academy evaluation</a> covers 33 clubs and scores professionalization, first-team minutes, national-team selections, schooling and European representation.",
    "The FFF describes a network of 13 regional technical directorates, 90 departmental commissions and more than 300 advisers across roughly 13,000 clubs: <a href=\"https://www.fff.fr/article/11669-le-made-in-france-c-est-du-solide.html\" target=\"_blank\" rel=\"noopener\">“Le Made in France, c’est du solide”</a>.",
    "French club fees vary; the range here reflects representative amateur-club schedules. The national <a href=\"https://www.sports.gouv.fr/le-pass-sport-reconduit-pour-la-saison-2025-2026-295\" target=\"_blank\" rel=\"noopener\">Pass’Sport program</a> offered a €70 voucher in 2025–26, primarily for eligible 14–17-year-olds receiving the school-year allowance, as well as certain students and young people with disabilities.",
    "The Aspen Institute’s Project Play reports $1,188 as the average annual family spending on a child’s primary soccer participation: <a href=\"https://projectplay.org/youth-sports/facts/challenges\" target=\"_blank\" rel=\"noopener\">Project Play, participation-cost facts</a>. The comparison with French fees is approximate.",
    "Opta’s 2026 birthplace analysis counted 99 World Cup players born in France and 54 born in Île-de-France: <a href=\"https://www.lequipe.fr/Football/Actualites/Des-joueurs-nes-en-ile-de-france-representes-dans-onze-selections-a-la-coupe-du-monde/1681455\" target=\"_blank\" rel=\"noopener\">L’Équipe</a>.",
    "The FFF traces the national center from planning in the 1970s to its 1988 inauguration: <a href=\"https://www.fff.fr/article/1098-11-juin-1988-centre-decisif-a-clairefontaine.html\" target=\"_blank\" rel=\"noopener\">FFF history</a>. France then missed the 1990 and 1994 World Cups before winning in 1998.",
    "The <a href=\"https://www.philadelphiaunion.com/news/cavan-sullivan-stays-home\" target=\"_blank\" rel=\"noopener\">Philadelphia Union</a> documents Sullivan’s family and Homegrown deal. His planned move to Manchester City and reported terms were reported by <a href=\"https://www.reuters.com/sports/soccer/union-sign-cavan-sullivan-14-record-homegrown-deal-2024-05-09/\" target=\"_blank\" rel=\"noopener\">Reuters</a>; because he was a minor, the clubs did not publish full transfer terms.",
    "Adu’s 2004 debut record and the pressure surrounding his career are revisited in <a href=\"https://www.mlssoccer.com/news/freddy-adu-exclusive-interview-mls-debut-dc-united\" target=\"_blank\" rel=\"noopener\">MLS’s retrospective interview</a>.",
    "CIES found that in 2024–25 France-eligible under-21 players received 7.8% of Ligue 1 minutes, versus 2.4% in the Premier League and 1.9% in Serie A. Argentina led the 50 leagues studied in the raw number of eligible U21 players and minutes: <a href=\"https://football-observatory.com/IMG/sites/b5wp/2025/wp522/en/\" target=\"_blank\" rel=\"noopener\">CIES Weekly Post 522</a>.",
    "FIFA’s <a href=\"https://inside.fifa.com/legal/news/fifa-publishes-professional-football-report-2023\" target=\"_blank\" rel=\"noopener\">Professional Football Report 2023</a> counted 9,464 male professionals and 244 professional clubs in Mexico, both global highs.",
    "CIES’s Latin American league comparison found the lowest club-trained share in Mexico and a substantially higher share in Argentina. See <a href=\"https://football-observatory.com/IMG/pdf/mr62en.pdf\" target=\"_blank\" rel=\"noopener\">CIES Monthly Report 62</a> (PDF). “Club-trained” is not the same as nationality; it measures players who spent at least three seasons with their employer between ages 15 and 21.",
    "The Mexican federation approved a 1,170-minute youth requirement for 2025–26: <a href=\"https://fmf.mx/noticia/asamblea-de-duenos-aprueba-el-plan-deportivo-de-javier-aguirre_2204\" target=\"_blank\" rel=\"noopener\">FMF owners’ assembly</a>. The <a href=\"https://cldrsrcs.apilmx.com/v1/docs/Reglamentos/Competencia/1_LIGA_MX/24_LIGA_MX_1_20250717190909.pdf\" target=\"_blank\" rel=\"noopener\">Liga MX rules</a> define eligibility and sanctions (PDF).",
    "MLS’s current rules govern salary budgets, transfer-revenue conversion, General Allocation Money, Designated Players and Homegrowns: <a href=\"https://www.mlssoccer.com/about/roster-rules-and-regulations\" target=\"_blank\" rel=\"noopener\">MLS Roster Rules and Regulations</a>.",
    "MLS clubs began pursuing FIFA training compensation and solidarity payments in 2019: <a href=\"https://www.mlssoccer.com/news/mls-clubs-seek-training-compensation-and-solidarity-payments\" target=\"_blank\" rel=\"noopener\">MLS</a>. The later <a href=\"https://www.mlssoccer.com/news/mls-next-development-grant-program\" target=\"_blank\" rel=\"noopener\">MLS NEXT Development Grant</a> compensates eligible independent academies in a narrower set of cases.",
    "MLS details Philadelphia’s development-and-sale model in <a href=\"https://www.mlssoccer.com/news/how-philadelphia-union-set-standard-for-youth-development-mls-sullivan-aaronson\" target=\"_blank\" rel=\"noopener\">this academy profile</a>. Orlando City announced Alex Freeman’s club-record Homegrown transfer to Villarreal in <a href=\"https://www.orlandocitysc.com/news/orlando-city-sc-transfers-defender-alex-freeman-to-villarreal-cf-in-club-record-homegrown-move\" target=\"_blank\" rel=\"noopener\">January 2026</a>.",
    "U.S. Soccer records four Women’s World Cups and five Olympic gold medals, including Paris 2024: <a href=\"https://www.ussoccer.com/stories/2024/08/us-womens-national-team-paris-olympics-highlights-by-the-numbers-stats\" target=\"_blank\" rel=\"noopener\">USWNT Paris highlights and program totals</a>.",
    "NFHS reports 3,666,917 boys and 294,015 girls in high-school sports in 1971–72 and more than an elevenfold rise in girls’ participation since: <a href=\"https://nfhs.org/stories/nfhs-begins-building-leaders-for-next-50-years-with-women-and-sport-leadership-summit\" target=\"_blank\" rel=\"noopener\">NFHS</a>. Current soccer totals are rounded from the latest NFHS and NCAA participation reports.",
    "Timeline: Title IX became law in 1972; the NCAA held its first women’s soccer championship in 1982; the United States won the inaugural Women’s World Cup in 1991. WUSA played from 2001–03, WPS from 2009–11 and the NWSL began in 2013.",
    "The English FA’s heritage material documents the 1921 ban and its 1971 repeal; the <a href=\"https://www.dfb.de/historie\" target=\"_blank\" rel=\"noopener\">DFB’s official history</a> records Germany’s 1955–70 ban. Brazil’s federal government traces the restriction from <a href=\"https://www.planalto.gov.br/ccivil_03/decreto-lei/1937-1946/del3199.htm\" target=\"_blank\" rel=\"noopener\">Decree-Law 3.199</a> in 1941 to its 1979 repeal.",
    "The June 2026 FIFA rankings list Argentina’s men first and its women 27th. The women’s league began professionalization in 2019. In 2024, national-team players left camp over pay, food and conditions: <a href=\"https://apnews.com/article/c51fd5b55383018f297bf954a9b3242a\" target=\"_blank\" rel=\"noopener\">Associated Press</a>.",
    "The June 16, 2026 FIFA women’s ranking placed Spain first, the United States second, England fourth and France sixth: <a href=\"https://inside.fifa.com/fifa-world-ranking/women/news/spain-scale-new-heights-summit-coca-cola-womens-world-ranking\" target=\"_blank\" rel=\"noopener\">FIFA</a>. Tournament results are from FIFA and UEFA competition records.",
    "The FFF reported a record 251,299 female registrations in 2023–24—10.5% of all licenses—and the launch of its professional women’s league organization in 2024: <a href=\"https://www.fff.fr/article/12662-pres-de-2-4-millions-de-licences-en-2023-2024.html\" target=\"_blank\" rel=\"noopener\">FFF registration report</a>.",
    "U.S. Soccer describes its regional managers, scouts, Talent ID Centers and selection process on its <a href=\"https://www.ussoccer.com/talent-identification\" target=\"_blank\" rel=\"noopener\">Talent Identification pages</a> and <a href=\"https://www.ussoccer.com/talent-identification/frequently-asked-questions\" target=\"_blank\" rel=\"noopener\">FAQ</a>. Players cannot sign themselves up; scouts and club staff identify them.",
    "US Club Soccer’s <a href=\"https://usclubsoccer.org/id2/\" target=\"_blank\" rel=\"noopener\">id2 program</a> is free to be scouted and to participate in, regardless of federation affiliation, and begins evaluation in a player’s home environment.",
    "Batson’s comments about expanding the pool and tracking more than 10,000 players came in a June 2026 talkSPORT interview, summarized by <a href=\"https://sports.yahoo.com/articles/us-soccer-turns-ai-scouting-164404260.html\" target=\"_blank\" rel=\"noopener\">Yahoo Sports</a>.",
    "Author’s calculation: about 300 French advisers for roughly 68 million people is one per 227,000. The equivalent for a U.S. population near 342 million is approximately 1,500.",
    "U.S. Soccer introduced <a href=\"https://www.ussoccer.com/stories/2021/06/us-soccer-announces-one-nation-initiatives-during-us-womens-national-team-summer-series-in-hartford\" target=\"_blank\" rel=\"noopener\">Coach for Community</a> as a free, hosted clinic for new coaches, with a voucher for an online Grassroots course and an emphasis on underserved areas.",
    "Course prices and schedules vary by host. Grassroots modules are short and often online; the D course commonly costs several hundred dollars and takes multiple weeks. Upper licenses are professional credentials whose fees can run into the thousands. Current offerings are published in the <a href=\"https://learning.ussoccer.com/coach\" target=\"_blank\" rel=\"noopener\">U.S. Soccer Learning Center</a>.",
    "Author’s estimate: 1,500 advisers at roughly $130,000 each in salary, benefits, travel, equipment and administration produces an annual cost near $200 million. It is an order-of-magnitude estimate, not a federation proposal.",
    "The larger comparison is intentionally broad. The Aspen Institute and Associated Press describe U.S. youth sports as a multibillion-dollar family economy and document soccer fees reaching five figures for some families: <a href=\"https://apnews.com/article/e8a0d22d05b99b5b84c61c09bf86686a\" target=\"_blank\" rel=\"noopener\">Associated Press, July 2026</a>.",
    "The U.S. Soccer Foundation traces its origin to the 1994 World Cup surplus. Its <a href=\"https://ussoccerfoundation.org/programs/safe-places-to-play/\" target=\"_blank\" rel=\"noopener\">Safe Places to Play</a> program reports more than 900 mini-pitches, 6.5 million children living within a half mile of one and a goal of 1,000 by the end of 2026. The Foundation’s <a href=\"https://ussoccerfoundation.org/wp-content/uploads/2025/06/Safe-Places-to-PLay-Mini-Pitch-Study.pdf\" target=\"_blank\" rel=\"noopener\">mini-pitch study</a> covers location, use and lighting (PDF).",
    "The Foundation filed its complaint in December 2018 after the federation demanded it stop using the U.S. Soccer name and marks: <a href=\"https://ussoccerfoundation.org/press/u-s-soccer-foundation-files-lawsuit-against-u-s-soccer-federation-to-protect-its-brand-marks-and-preserve-its-mission-of-growing-the-sport-in-urban-underserved-communities/\" target=\"_blank\" rel=\"noopener\">Foundation statement and complaint summary</a>. The parties settled and dismissed the case in May 2020.",
]


FIRST_REF = {
    3: "3a",
    9: "9a",
    11: "11a",
    16: "16a",
    25: "25a",
    33: "33a",
}


def clean(text: str, index: int) -> str:
    text = REWRITES.get(index, text)
    return (
        text.replace("\u00a0", " ")
        .replace("For this past season", "For the 2024–25 season")
        .replace("three hundred technical advisers", "more than three hundred technical advisers")
        .replace("roughly thirteen thousand clubs", "roughly thirteen thousand clubs")
        .replace("two and three quarter hours", "two and three-quarter hours")
        .replace("warmup", "warm-up")
        .replace("under-twenty-one", "under-21")
        .strip()
    )


def pullquote(text: str, light: bool) -> str:
    modifier = " longform-pullquote--light" if light else ""
    return f'<blockquote class="longform-pullquote{modifier}"><p>{text}</p></blockquote>'


document = Document(SOURCE)
paragraphs = [paragraph.text for paragraph in document.paragraphs]
word_count = len(re.findall(r"\b[\w’'-]+\b", " ".join(paragraphs[3:249])))
read_time = max(1, math.ceil(word_count / 215))

front_matter = f"""---
layout: longform
title: "Why the USMNT Will Never Be Argentina (But Could Maybe Be France): Part 2"
title_primary: "Why the USMNT Will Never Be Argentina"
title_secondary: "(But Could Maybe Be France)"
subtitle: "France did not inherit a soccer culture like Argentina’s. It built the machinery to find talent, develop it and wait for the harvest. Here is what America could build—and why it still has not."
excerpt: "Part 2 of The American Soccer Question: the French development machine, America’s missing professional rung, the lesson of the USWNT and an honest blueprint for what comes next."
date: 2026-07-21 23:00:00 -0400
categories: [usmnt, analysis]
permalink: /usmnt/why-the-usmnt-will-never-be-argentina-part-2/
author: "Randy Morgan"
series: "The American Soccer Question"
part: "Part 2 of 2"
read_time: {read_time}
word_count: {word_count}
start_id: the-french-model
hero_image: /assets/images/usmnt-longform-part2-clairefontaine.jpg
thumbnail: /assets/images/usmnt-longform-part2-cavan-sullivan.jpg
hero_us: /assets/images/usmnt-longform-part2-cavan-sullivan.jpg
hero_us_label: The Prospect
hero_argentina: /assets/images/usmnt-longform-part2-clairefontaine.jpg
hero_argentina_label: The Model
hero_france: /assets/images/usmnt-longform-part2-mini-pitch-night.jpg
hero_france_label: The Build
series_link_url: /usmnt/why-the-usmnt-will-never-be-argentina/
series_link_kicker: Start with Part 1
series_link_title: Why America cannot become Argentina
donation_cta: true
donation_cta_inline: true
newsletter_cta: true
newsletter_kicker: Keep reading deeply
newsletter_heading: More longform, after the final whistle.
newsletter_text: Subscribe for future essays and the next chapter of The World Cup Guide.
newsletter_button: Subscribe
newsletter_source: USMNT longform Part 2
toc_items:
  - id: the-french-model
    label: The French Model
  - id: the-missing-rung
    label: The Missing Rung
  - id: the-head-start
    label: The Head Start
  - id: the-build
    label: The Build
  - id: growing-into-it
    label: Growing Into It
---
"""

chunks = [front_matter]

for index in range(3, 249):
    if index in HEADINGS:
        number, anchor, title = HEADINGS[index]
        chunks.append(f'<h2 id="{anchor}"><span class="longform-chapter-number">{number}</span><span>{title}</span></h2>')
        continue
    if index in PULLS:
        text, light = PULLS[index]
        chunks.append(pullquote(text, light))
    else:
        text = clean(paragraphs[index], index)
        if not text:
            continue
        if index in CITATIONS:
            text += CITATIONS[index]
        chunks.append(text)
    if index in AFTER:
        chunks.append(AFTER[index].strip())

chunks.append("""<aside class="longform-next longform-next--series">
  <span class="longform-next-kicker">The complete argument</span>
  <h3>Start where the question began.</h3>
  <p>Part I explains why America cannot copy Argentina’s inherited soccer culture—and why the usual explanations for the USMNT’s ceiling miss the real constraint.</p>
  <a class="longform-next-cta" href="{{ '/usmnt/why-the-usmnt-will-never-be-argentina/' | relative_url }}">Read Part I <span aria-hidden="true">→</span></a>
</aside>""")

chunks.append("""{% if page.donation_cta and page.donation_cta_inline %}
  {% include donation-cta.html %}
{% endif %}""")

notes_html = ['<section class="longform-notes" id="notes">', '<h2>Notes &amp; sources</h2>', '<ol>']
for number, note in enumerate(NOTES, start=1):
    ref = FIRST_REF.get(number, str(number))
    notes_html.append(f'<li id="note-{number}">{note} <a class="longform-backref" href="#ref-{ref}" aria-label="Back to note {number} in the essay">↩</a></li>')
notes_html.extend([
    '</ol>',
    '<div class="longform-photo-credits">',
    '<h3>Photography &amp; licensing</h3>',
    '<p>Clairefontaine: Xavoun, CC BY-SA 3.0. Cavan Sullivan: Bryan Berlin, CC BY-SA 4.0. Freddy Adu: 2O, CC BY-SA 3.0. Dick, Kerr Ladies: Nationaal Archief, public domain. 1999 USWNT: Ralph Alswang / White House Photograph Office / National Archives, public domain.</p>',
    '<p>Mini-pitch photography appears courtesy of the U.S. Soccer Foundation and is linked to its original program page in each caption.</p>',
    '</div>',
    '</section>',
])
chunks.append("\n".join(notes_html))

OUTPUT.write_text("\n\n".join(chunks).rstrip() + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT.relative_to(ROOT)} ({word_count:,} words, {read_time} min read)")
