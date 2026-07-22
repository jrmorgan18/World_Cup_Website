"""Build the flagship USMNT long read from its Word manuscript."""

from pathlib import Path
import math
import re

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "articles" / "Why the USMNT Will Never be Argentina (but could maybe be France).docx"
OUTPUT = ROOT / "_posts" / "2026-07-13-why-the-usmnt-will-never-be-argentina.md"


def citation(number: int, suffix: str = "") -> str:
    ref_id = f"ref-{number}{suffix}"
    return f'<sup id="{ref_id}"><a href="#note-{number}" aria-label="See note {number}">{number}</a></sup>'


CITATIONS = {
    12: citation(1),
    15: citation(2),
    18: citation(3, "a"),
    22: citation(4, "a"),
    26: citation(3, "b"),
    42: citation(5),
    44: citation(6),
    48: citation(7),
    54: citation(8),
    55: citation(9),
    56: citation(4, "b"),
    67: citation(10, "a"),
    69: citation(10, "b"),
    71: citation(11),
    93: citation(12),
    106: citation(13),
    128: citation(14),
    129: citation(15),
    130: citation(16, "a"),
    131: citation(16, "b"),
    143: citation(17),
    156: citation(19),
    178: citation(20),
    187: citation(21),
    188: citation(22),
    193: citation(23),
    200: citation(24),
    207: citation(25),
    212: citation(26),
    219: citation(27),
    228: citation(28),
}


REWRITES = {}


HEADINGS = {
    2: ("01", "the-hangover", "The Hangover"),
    40: ("02", "two-models", "Two Models"),
    98: ("03", "the-excuse", "The Excuse"),
    161: ("04", "what-cant-be-built", "What Can't Be Built"),
    238: ("05", "the-way-through", "The Way Through"),
}


SKIP = {38}


PULLS = {
    16: ("We threw the party and got thrown out of it.", False),
    28: ("Thirty-six years. One quarterfinal.", True),
    37: ("We are never going to be Argentina. France, though. France we might be able to be.", False),
    51: ("Argentina hopes. France restocks.", True),
    61: ("The oil was already in the ground. France had to drill.", False),
    97: ("If only our best athletes played soccer. Imagine if LeBron had chosen soccer instead of basketball.", True),
    119: ("That body is the greatest soccer player who has ever lived.", False),
    177: ("Two hours. In Germany.", True),
    223: ("That is not a heartwarming coincidence. It is a diagnostic.", False),
}


AFTER = {
    42: """
<figure class="longform-figure">
  <img src="{{ '/assets/images/usmnt-longform-argentina-celebration.jpg' | relative_url }}" alt="A vast crowd fills the streets around the Obelisk in Buenos Aires after Argentina's 2022 World Cup victory" loading="lazy">
  <figcaption><strong>A country in the street</strong>An estimated four million people poured into Buenos Aires after Argentina won the 2022 World Cup. Photo: Gobierno de la Ciudad de Buenos Aires / <a href="https://commons.wikimedia.org/wiki/File:Festejos_en_el_Obelisco_de_Buenos_Aires_por_la_obtenci%C3%B3n_de_la_Copa_del_Mundo_de_F%C3%BAtbol_2022.jpg" target="_blank" rel="noopener">Wikimedia Commons</a>.</figcaption>
</figure>
""",
    50: """
<div class="longform-triptych" role="group" aria-label="France's next generation: Désiré Doué, Michael Olise, and Kylian Mbappé">
  <div class="longform-triptych-grid">
    <figure><img src="{{ '/assets/images/doue-france.jpg' | relative_url }}" alt="Désiré Doué playing for France" loading="lazy"><span>Désiré Doué</span></figure>
    <figure><img src="{{ '/assets/images/olise-france.jpg' | relative_url }}" alt="Michael Olise playing for France" loading="lazy"><span>Michael Olise</span></figure>
    <figure><img src="{{ '/assets/images/mbappe-france.jpg' | relative_url }}" alt="Kylian Mbappé playing for France" loading="lazy"><span>Kylian Mbappé</span></figure>
  </div>
  <p>The point is not one superstar. It is the line behind him. Photos: site archive.</p>
</div>
""",
    116: """
<figure class="longform-figure">
  <img src="{{ '/assets/images/usmnt-longform-free-play.jpg' | relative_url }}" alt="Children playing an informal game of soccer in a sunny public park" loading="lazy">
  <figcaption><strong>Before the system</strong>The decisive question is not which sport an athlete chooses at fifteen. It is whether the ball is already part of life at four. Photo: <a href="https://unsplash.com/photos/children-playing-soccer-in-a-sunny-park-y_sf8j3K2ZY" target="_blank" rel="noopener">Simone Franchina / Unsplash</a>.</figcaption>
</figure>
""",
    170: """
<figure class="longform-figure">
  <img src="{{ '/assets/images/usmnt-longform-baby-futbol-argentina.jpg' | relative_url }}" alt="Young children playing baby fútbol on a hard indoor court at Polideportivo 3 de Febrero in Dock Sud, Buenos Aires" loading="lazy">
  <figcaption><strong>The organized layer</strong>Baby fútbol in Dock Sud: five-a-side, a hard court, real goals, parents against the wall and a neighborhood watching. Photo: Roberto Fiadone / <a href="https://commons.wikimedia.org/wiki/File:Ni%C3%B1os_jugando_f%C3%BAtbol,_Polideportivo_3_De_Febrero,_Dock_Sud.jpg" target="_blank" rel="noopener">Wikimedia Commons</a>.</figcaption>
</figure>
""",
    172: """
<figure class="longform-figure">
  <img src="{{ '/assets/images/usmnt-longform-potrero.jpg' | relative_url }}" alt="Players contesting the ball on a dirt potrero in Buenos Aires, with apartment blocks beyond the field" loading="lazy">
  <figcaption><strong>The other classroom</strong>Fútbol de potrero on a dirt field in Buenos Aires. The space is imperfect, the game continuous and nobody stops play to explain it. Photo: Roblespepe / <a href="https://commons.wikimedia.org/wiki/File:Potrero_(2).jpg" target="_blank" rel="noopener">Wikimedia Commons</a>.</figcaption>
</figure>
""",
    228: """
<div class="longform-archive" role="group" aria-label="Archival portraits of Baltimore Blast figures Mike Stankovic and Kenny Cooper Sr.">
  <div class="longform-archive-grid">
    <figure><img src="{{ '/assets/images/usmnt-longform-mike-stankovic-blast.jpg' | relative_url }}" alt="Mike Stankovic in a Baltimore Blast portrait from the 1984–85 MISL media guide" loading="lazy"><span>Mike Stankovic</span></figure>
    <figure><img src="{{ '/assets/images/usmnt-longform-kenny-cooper-sr-blast.jpg' | relative_url }}" alt="Kenny Cooper Sr. in a Baltimore Blast portrait from the 1984–85 MISL media guide" loading="lazy"><span>Kenny Cooper Sr.</span></figure>
  </div>
  <p><strong>Knowledge, imported.</strong> A star defender and a championship coach helped make elite soccer expertise an ordinary part of childhood in one corner of Baltimore County. Portraits: 1984–85 MISL media guide / Wikimedia Commons (<a href="https://commons.wikimedia.org/wiki/File:Mike_Stankovic,_MISL_1984-85_media_guide_page_012.tif" target="_blank" rel="noopener">Stankovic</a>, <a href="https://commons.wikimedia.org/wiki/File:Kenny_Cooper,_MISL_1984-85_media_guide_page_013.tif" target="_blank" rel="noopener">Cooper</a>).</p>
</div>
""",
}


NOTES = [
    "Match figures are from <a href=\"{{ '/usmnt/usmnt-vs-belgium-instant-reaction/' | relative_url }}\">The World Cup Guide's instant reaction to USA–Belgium</a>, using the match data available at publication.",
    "FIFA confirmed the 2026 final for July 19 at New York New Jersey Stadium (MetLife): <a href=\"https://www.fifa.com/en/articles/new-york-new-jersey-stadium-host-world-cup-2026-final\" target=\"_blank\" rel=\"noopener\">FIFA, tournament final announcement</a>.",
    "Tournament-by-tournament U.S. results and the 1994 loss to Brazil: <a href=\"https://www.fifa.com/en/articles/usa-team-profile-history\" target=\"_blank\" rel=\"noopener\">FIFA, United States team profile and World Cup history</a>.",
    "Pre-tournament positions come from the June 2026 FIFA men's ranking table: <a href=\"https://www.thefa.com/-/media/files/thefaportal/governance-docs/registrations/mens-fifa-rankings-june-2026-24-months.ashx\" target=\"_blank\" rel=\"noopener\">FIFA rankings, June 2026</a> (PDF hosted by The FA).",
    "The crowd estimate, halted bus route and helicopter evacuation were reported from Buenos Aires: <a href=\"https://www.reutersconnect.com/item/fifa-world-cup-qatar-2022-argentina-victory-parade-after-winning-the-world-cup/dGFnOnJldXRlcnMuY29tLDIwMjI6bmV3c21sX1VQMUVJQ0sxSE9JNkg\" target=\"_blank\" rel=\"noopener\">Reuters, Argentina victory parade</a>.",
    "Match sequence and Mbappé's hat trick: <a href=\"https://www.fifa.com/en/articles/world-cup-qatar-2022-tournament-review-argentina-messi-mbappe-morocco-croatia-japan\" target=\"_blank\" rel=\"noopener\">FIFA, 2022 World Cup tournament review</a>.",
    "Argentina's titles, finals and 36-year wait between 1986 and 2022: <a href=\"https://www.fifa.com/en/articles/argentina-team-profile-history\" target=\"_blank\" rel=\"noopener\">FIFA, Argentina team profile and World Cup history</a>.",
    "River Plate won the 2018 Libertadores; the champions since have all been Brazilian clubs: <a href=\"https://gol.conmebol.com/libertadores/en/news/los-campeones-de-la-conmebol-libertadores-que-iran-por-una-nueva-corona\" target=\"_blank\" rel=\"noopener\">CONMEBOL, Libertadores champions</a>.",
    "CIES counted 2,171 Argentine expatriate footballers, behind Brazil (3,020) and France (2,293): <a href=\"https://football-observatory.com/IMG/sites/b5wp/2024/wp505/en/\" target=\"_blank\" rel=\"noopener\">CIES Football Observatory Weekly Post 505</a>, May 2025.",
    "France's tournament record, including the missed World Cups and four finals through 2022: <a href=\"https://www.fifa.com/en/articles/france-world-cup-team-profile-history\" target=\"_blank\" rel=\"noopener\">FIFA, France team profile and World Cup history</a>.",
    "Opta's 2026 birthplace analysis counted 99 France-born players—23 for France and 76 for other teams—and traced 54 to Île-de-France: <a href=\"https://www.lequipe.fr/Football/Actualites/99-joueurs-selectionnes-pour-la-coupe-du-monde-sont-nes-en-france/1681433\" target=\"_blank\" rel=\"noopener\">L'Équipe</a>. Pre-tournament roster estimates put France at €1.53 billion and Argentina at €818.5 million: <a href=\"https://www.sportingpedia.com/2026/06/03/2026-world-cup-team-values-and-group-rankings/\" target=\"_blank\" rel=\"noopener\">SportingPedia's Transfermarkt-based comparison</a>.",
    "Birthplaces and development paths are listed in U.S. Soccer's official <a href=\"https://www.ussoccer.com/stories/2026/05/usmnt/us-mens-national-team-head-coach-mauricio-pochettino-names-26-player-roster-for-fifa-world-cup-2026\" target=\"_blank\" rel=\"noopener\">2026 World Cup roster notes</a> and player biographies.",
    "Inter Miami lists Messi at 5'7\" and 148 pounds: <a href=\"https://www.intermiamicf.com/players/lionel-messi/\" target=\"_blank\" rel=\"noopener\">Inter Miami CF, Lionel Messi player profile</a>.",
    "World Cup records and population context: <a href=\"https://www.fifa.com/en/tournaments/mens/worldcup/articles/uruguay-team-profile-history\" target=\"_blank\" rel=\"noopener\">FIFA on Uruguay</a> and <a href=\"https://www.fifa.com/en/articles/croatia-team-profile-history\" target=\"_blank\" rel=\"noopener\">FIFA on Croatia</a>. China's June 2026 position is in the ranking table cited in note 4.",
    "A recent cross-country analysis finds population and GDP far weaker than football-specific history and experience: <a href=\"https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6928238\" target=\"_blank\" rel=\"noopener\">“What Predicts World Cup Success?”</a>, SSRN working paper, May 2026.",
    "FIFA's 2023 professional football report counted 9,464 male professionals and 244 professional clubs in Mexico: <a href=\"https://inside.fifa.com/legal/news/fifa-publishes-professional-football-report-2023\" target=\"_blank\" rel=\"noopener\">FIFA, Professional Football Report 2023</a>. World Cup finishes are from FIFA's tournament archive.",
    "The 10 a.m. kickoff, college-football television constraint, 54,032 crowd, 3–2 result and end of the United States' 16-year home qualifying streak are documented by <a href=\"https://www.frontrowsoccer.com/2017/03/22/looking-back-honduras-beat-u-s-wcq-2001/\" target=\"_blank\" rel=\"noopener\">Michael Lewis</a>. <a href=\"https://www.washingtonpost.com/archive/local/2002/07/27/fan-alleges-ticket-bias-at-rfk-soccer-match/acb99334-d399-4f44-b661-029e6f931abb/\" target=\"_blank\" rel=\"noopener\">The Washington Post</a> documented the overwhelmingly pro-Honduran atmosphere and Bruce Arena's reaction; <a href=\"https://www.soccerwire.com/resources/mayhem-at-rfk-the-usa-honduras-game-that-lives-in-infamy/\" target=\"_blank\" rel=\"noopener\">SoccerWire's oral history</a> preserves the Associated Press description of RFK as having been taken over by a Central American country.",
    "Participation estimates: <a href=\"https://sfia.org/resources/soccer-participation-in-the-u-s-hits-an-all-time-high-ahead-of-world-cup/\" target=\"_blank\" rel=\"noopener\">SFIA, 2025 soccer participation report</a> and <a href=\"https://sfia.org/resources/the-world-cup-is-here-and-america-is-already-playing/\" target=\"_blank\" rel=\"noopener\">SFIA, June 2026 World Cup survey</a>.",
    "The American Academy of Pediatrics reports that roughly 70% of children drop out of organized sports by age 13: <a href=\"https://publications.aap.org/pediatrics/article/138/3/e20162148/52612/Sports-Specialization-and-Intensive-Training-in\" target=\"_blank\" rel=\"noopener\">AAP, “Sports Specialization and Intensive Training in Young Athletes”</a>.",
    "The retrospective German study found more childhood peer-led play among later professionals and about two hours per week of organized practice through age ten: <a href=\"https://doi.org/10.1080/17461391.2014.982204\" target=\"_blank\" rel=\"noopener\">Hornig, Aust and Güllich, European Journal of Sport Science</a>.",
    "On federation age and persistent first-mover advantage: <a href=\"https://onlinelibrary.wiley.com/doi/full/10.1002/mde.3758\" target=\"_blank\" rel=\"noopener\">Daumann et al., “The early bird catches the worm,” Managerial and Decision Economics</a> (2023).",
    "Founding dates: <a href=\"https://www.ussoccer.com/history/timeline\" target=\"_blank\" rel=\"noopener\">U.S. Soccer history timeline</a> and <a href=\"https://www.fff.fr/121-notre-histoire.html\" target=\"_blank\" rel=\"noopener\">French Football Federation history</a>.",
    "Messi's first game at Grandoli and his grandmother Celia's insistence are recounted in <a href=\"https://apnews.com/article/2c6fd62146a2e4de22bee75f1ea3c9c0\" target=\"_blank\" rel=\"noopener\">Associated Press, “Where Messi's story began”</a>.",
    "The <a href=\"https://baltimoreblast.com/about-the-baltimore-blast/\" target=\"_blank\" rel=\"noopener\">Baltimore Blast</a> identifies Stankovic as a six-time MISL All-Star and a member of its championship team; the <a href=\"https://www.ghanafa.org/stankovic-awal-salifu-join-black-stars-technical-team-for-2021-africa-cup-of-nations?amp=1\" target=\"_blank\" rel=\"noopener\">Ghana Football Association</a> documents his later return to the Black Stars staff, and <a href=\"https://www.modernghana.com/sports/1129791/mike-stankovic-joins-black-stars-technical-team.html\" target=\"_blank\" rel=\"noopener\">Modern Ghana</a> records his role as Milovan Rajevac's assistant at the 2010 World Cup. <a href=\"https://1982.gnkdinamo.hr/players/emil-dragicevic/\" target=\"_blank\" rel=\"noopener\">GNK Dinamo's historical archive</a> documents Emil Dragičević's years at the club and its 1982 league and 1983 cup-winning era.",
    "Dan Wang, <a href=\"https://www.penguin.co.uk/books/465161/breakneck-by-wang-dan/9781837312283\" target=\"_blank\" rel=\"noopener\"><em>Breakneck: China's Quest to Engineer the Future</em></a> (Penguin, 2025).",
    "Grant Wahl reported the $75,000 U.S. Soccer pilot and the dispute over metrics: <a href=\"https://www.si.com/soccer/2018/05/24/tom-byer-us-soccer-pilot-program-canceled\" target=\"_blank\" rel=\"noopener\">Sports Illustrated, “Tom Byer, U.S. Soccer and Soccer Starts at Home”</a> (2018).",
    "Family backgrounds are documented in official U.S. Soccer player biographies and its 2026 feature <a href=\"https://www.ussoccer.com/stories/2026/06/usmnt/hosting-fifa-world-cup-friends-family-atmosphere\" target=\"_blank\" rel=\"noopener\">“A Friends and Family Atmosphere”</a>.",
    "The <a href=\"https://www.indoorsoccerhall.com/kenny-cooper\" target=\"_blank\" rel=\"noopener\">Indoor Soccer Hall of Fame</a> recounts Kenny Cooper Sr.'s championship run with the Baltimore Blast. <a href=\"https://kennycooperjr.com/about\" target=\"_blank\" rel=\"noopener\">Kenny Cooper Jr.'s official biography</a> traces his path to Manchester United and a twelve-year professional career; his ten U.S. appearances are recorded by <a href=\"https://www.national-football-teams.com/player/20708/Kenny_Cooper.html\" target=\"_blank\" rel=\"noopener\">National Football Teams</a>.",
]


def clean(text: str, index: int) -> str:
    text = REWRITES.get(index, text)
    return (
        text.replace("\u00a0", " ")
        .replace("talent deficient squads", "talent-deficient squads")
        .replace("non-descript European", "nondescript European")
        .replace("Bringing the games stars", "Bringing the game's stars")
        .replace("jump starting", "jump-starting")
        .replace("a real effective tactical identity", "a real, effective tactical identity")
        .replace("Pogba, Kante and Griezmann", "Pogba, Kanté and Griezmann")
        .replace("some many", "so many")
        .replace("by the time they are fourteen", "by the time they are thirteen")
        .replace("Stankovic and Dragisovic", "Stankovic and Dragicevic")
        .replace("a five-time All-Star", "a six-time MISL All-Star")
        .strip()
    )


def pullquote(text: str, light: bool) -> str:
    modifier = " longform-pullquote--light" if light else ""
    return f'<blockquote class="longform-pullquote{modifier}"><p>{text}</p></blockquote>'


document = Document(SOURCE)
paragraphs = [paragraph.text for paragraph in document.paragraphs]
word_count = len(re.findall(r"\b[\w’'-]+\b", " ".join(paragraphs[3:247])))
read_time = max(1, math.ceil(word_count / 215))

front_matter = f"""---
layout: longform
title: "Why the USMNT Will Never Be Argentina (But Could Maybe Be France)"
title_primary: "Why the USMNT Will Never Be Argentina"
title_secondary: "(But Could Maybe Be France)"
subtitle: "America can’t recreate the conditions and culture that spawn a Messi or Maradona. It must build its own soccer culture and institutions, and France provides a blueprint."
excerpt: "The USMNT's World Cup ended, but the argument it exposed is much larger: why Argentina's soccer culture cannot be copied, what France deliberately built, and where that leaves America."
date: 2026-07-13 08:00:00 -0400
categories: [usmnt, analysis]
permalink: /usmnt/why-the-usmnt-will-never-be-argentina/
author: "Randy Morgan"
series: "The American Soccer Question"
part: "Part 1 of 2"
read_time: {read_time}
word_count: {word_count}
hero_image: /assets/images/usmnt-longform-argentina-celebration.jpg
thumbnail: /assets/images/pulisic-usmnt-2026.jpg
hero_us: /assets/images/pulisic-usmnt-2026.jpg
hero_argentina: /assets/images/messi-argentina-2026.jpg
hero_france: /assets/images/mbappe-france.jpg
start_id: the-hangover
series_link_url: /usmnt/why-the-usmnt-will-never-be-argentina-part-2/
series_link_kicker: Continue with Part 2
series_link_title: What America can actually build
donation_cta: true
donation_cta_inline: true
newsletter_cta: true
newsletter_kicker: Keep reading deeply
newsletter_heading: The argument continues in Part 2.
newsletter_text: Read the conclusion now, then subscribe for future longform essays and coverage.
newsletter_button: Subscribe
newsletter_source: USMNT longform Part 1
toc_items:
  - id: the-hangover
    label: The Hangover
  - id: two-models
    label: Two Models
  - id: the-excuse
    label: The Excuse
  - id: what-cant-be-built
    label: What Can't Be Built
  - id: the-way-through
    label: The Way Through
---
"""

chunks = [front_matter]

for index in range(2, 240):
    if index in SKIP:
        continue
    if index in HEADINGS:
        number, anchor, title = HEADINGS[index]
        chunks.append(f'<h2 id="{anchor}"><span class="longform-chapter-number">{number}</span><span>{title}</span></h2>')
        continue
    if index == 239:
        chunks.append(
            """<aside class="longform-next">
  <span class="longform-next-kicker">Continue in Part II</span>
  <h3>The United States cannot build a potrero.</h3>
  <p>It cannot manufacture a century of accumulated knowledge, make soccer the only game in town, or give every American kid a grandmother who argues about the lineup at baby fútbol. It cannot become Argentina by spending more money, hiring a better coach, or finding a few more athletes.</p>
  <p><strong>That is the bad news. The good news is that Argentina is not the only way to build a world power.</strong></p>
  <p>France did not inherit everything it needed. It identified the places where soccer culture already existed, built a system capable of finding the players growing inside it, and made sure poverty did not keep them outside the gates. It turned scattered talent into an assembly line.</p>
  <p><strong>The United States will never be Argentina.<br>But could it become France?</strong></p>
  <p>Part II looks at what France proved can be built—and why America still has not built it.</p>
  <a class="longform-next-cta" href="{{ '/usmnt/why-the-usmnt-will-never-be-argentina-part-2/' | relative_url }}">Read Part II <span aria-hidden="true">→</span></a>
</aside>"""
        )
        continue
    if index == 149:
        chunks.append(
            f"""<aside class="longform-stat">
  <div class="longform-stat-grid">
    <div class="longform-stat-item"><strong>25M</strong><span>Americans playing some version of soccer during this World Cup{citation(18)}</span></div>
    <span class="longform-stat-divider" aria-hidden="true"></span>
    <div class="longform-stat-item"><strong>26</strong><span>places on the national-team roster</span></div>
  </div>
  <p>The pool is not the problem. The pipe is.</p>
</aside>"""
        )
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

chunks.append("""{% if page.donation_cta and page.donation_cta_inline %}
  {% include donation-cta.html %}
{% endif %}""")

notes_html = ['<section class="longform-notes" id="notes">', '<h2>Notes &amp; sources</h2>', '<ol>']
first_ref_suffix = {3: "a", 4: "a", 10: "a", 16: "a"}
for number, note in enumerate(NOTES, start=1):
    ref = f"{number}{first_ref_suffix.get(number, '')}"
    notes_html.append(f'<li id="note-{number}">{note} <a class="longform-backref" href="#ref-{ref}" aria-label="Back to note {number} in the essay">↩</a></li>')
notes_html.extend([
    '</ol>',
    '<div class="longform-photo-credits">',
    '<h3>Photography &amp; licensing</h3>',
    '<p>Buenos Aires celebration: Gobierno de la Ciudad Autónoma de Buenos Aires, CC BY 2.5 AR. Dock Sud baby fútbol: Roberto Fiadone, CC BY-SA 4.0. Buenos Aires potrero: Roblespepe, CC BY-SA 4.0. Informal park game: Simone Franchina, Unsplash License. Baltimore Blast portraits: Major Indoor Soccer League, 1984–85 media guide, public domain.</p>',
    '<p>Player imagery in the opening and France triptych is drawn from The World Cup Guide site archive.</p>',
    '</div>',
    '</section>',
])
chunks.append("\n".join(notes_html))

OUTPUT.write_text("\n\n".join(chunks).rstrip() + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT.relative_to(ROOT)} ({word_count:,} words, {read_time} min read)")
