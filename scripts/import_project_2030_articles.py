"""Import the two launch Project 2030 DOCX drafts as Jekyll posts.

The source documents remain untouched in articles/. This script performs the
mechanical DOCX-to-Markdown conversion and adds the site-specific front matter,
figures and prospect score table.
"""

from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "articles"
POSTS = ROOT / "_posts"


def inline_markdown(paragraph):
    pieces = []
    for run in paragraph.runs:
        text = run.text
        if not text:
            continue
        if run.bold and text.strip():
            leading = text[: len(text) - len(text.lstrip())]
            trailing = text[len(text.rstrip()) :]
            core = text.strip()
            pieces.append(f"{leading}**{core}**{trailing}")
        else:
            pieces.append(text)
    return "".join(pieces).strip()


def convert_docx(path):
    document = Document(path)
    blocks = []
    for paragraph in document.paragraphs:
        text = inline_markdown(paragraph)
        if not text:
            continue
        style = paragraph.style.name.lower()
        if style.startswith("heading 1"):
            blocks.append((1, paragraph.text.strip()))
        elif style.startswith("heading 2"):
            blocks.append((2, paragraph.text.strip()))
        elif style.startswith("heading 3"):
            blocks.append((3, paragraph.text.strip()))
        else:
            blocks.append((0, text))
    return blocks


PROSPECT_ROWS = [
    (1, "Zavier Gozo", 19, "Winger / wingback", 23, 18, 17, 13, 9, 10, 90),
    (2, "Noahkai Banks", 19, "Center back", 25, 17, 19, 14, 8, 4, 87),
    (3, "Julian Hall", 18, "Striker / wide forward", 22, 18, 18, 12, 9, 7, 86),
    (4, "Adri Mehmeti", 17, "Defensive / central midfielder", 20, 18, 16, 12, 9, 10, 85),
    (5, "Neil Pierre", 18, "Center back", 16, 17, 18, 14, 9, 10, 84),
    (6, "Chris Brady", 22, "Goalkeeper", 24, 14, 14, 12, 8, 10, 82),
    (7, "Rokas Pukštas", 21, "Box-to-box No. 8", 23, 16, 14, 11, 7, 10, 81),
    (8, "Cavan Sullivan", 16, "Attacking midfielder / winger", 14, 16, 20, 12, 9, 10, 81),
    (9, "Niko Tsakiris", 21, "No. 8 / No. 10", 20, 17, 16, 11, 6, 10, 80),
    (10, "Paxten Aaronson", 22, "Attacking midfielder / No. 8", 22, 15, 14, 10, 7, 10, 78),
    (11, "Mathis Albert", 17, "Winger", 7, 17, 20, 13, 10, 10, 77),
    (12, "Diego Kochen", 20, "Goalkeeper", 12, 14, 18, 14, 8, 10, 76),
    (13, "Benjamin Cremaschi", 21, "Box-to-box No. 8 / attacking midfielder", 19, 15, 14, 10, 8, 10, 76),
    (14, "Kevin Paredes", 23, "Wingback / winger", 15, 13, 17, 13, 7, 10, 75),
    (15, "Peyton Miller", 18, "Left back / wingback / winger", 16, 14, 15, 11, 8, 10, 74),
    (16, "Cooper Sanchez", 18, "Central / attacking midfielder", 18, 15, 14, 9, 7, 10, 73),
    (17, "Beau Leroux", 22, "Central / defensive midfielder", 20, 15, 12, 10, 5, 10, 72),
    (18, "Francis Westfield", 20, "Right back / left back", 20, 15, 11, 9, 6, 10, 71),
    (19, "Cole Campbell", 20, "Winger", 8, 12, 19, 11, 10, 10, 70),
    (20, "Luca Bombino", 20, "Left back", 20, 14, 11, 9, 5, 10, 69),
]


def prospect_table():
    rows = []
    for values in PROSPECT_ROWS:
        rank, player, age, position, *scores = values
        score_cells = "".join(f"<td>{score}</td>" for score in scores[:-1])
        rows.append(
            f"<tr><td>{rank}</td><th scope=\"row\">{player}</th><td>{age}</td>"
            f"<td>{position}</td>{score_cells}<td><strong>{scores[-1]}</strong></td></tr>"
        )
    return """<section class="prospect-score-section" aria-labelledby="prospect-score-heading">
<p class="de-kicker">Research snapshot</p>
<h2 id="prospect-score-heading">The 2030 Breakthrough Score</h2>
<p>This score balances first-team evidence with age, upside, positional opportunity, recent trajectory and—where relevant—the likelihood that a dual-national will represent the United States. The numbers are structured judgments, not measurements precise to a single point.</p>
<div class="project-data-table" id="prospect-score-table" role="region" aria-label="Twenty USMNT prospects ranked by the 2030 Breakthrough Score" tabindex="0">
<table>
<thead><tr><th scope="col">RK</th><th scope="col">Player</th><th scope="col">Age</th><th scope="col">Position</th><th scope="col"><abbr title="First-team proof">FTP</abbr><small>/25</small></th><th scope="col"><abbr title="Age-adjusted performance">AAP</abbr><small>/20</small></th><th scope="col"><abbr title="Long-term ceiling">CEIL</abbr><small>/20</small></th><th scope="col"><abbr title="USMNT pathway">PATH</abbr><small>/15</small></th><th scope="col"><abbr title="Development trajectory">TRAJ</abbr><small>/10</small></th><th scope="col"><abbr title="United States commitment probability">USA</abbr><small>/10</small></th><th scope="col">Score<small>/100</small></th></tr></thead>
<tbody>
""" + "\n".join(rows) + """
</tbody>
</table>
</div>
<details class="prospect-score-key"><summary>How to read the score</summary><div><p><strong>FTP</strong> measures senior minutes, responsibility and quality of competition. <strong>AAP</strong> evaluates production relative to age, position and league. <strong>CEIL</strong> captures technical, physical and tactical upside.</p><p><strong>PATH</strong> reflects positional need and competition for places. <strong>TRAJ</strong> tracks whether a role is expanding. <strong>USA</strong> adjusts for international commitment; it is why Noahkai Banks scores below where his club evidence and ceiling alone would place him.</p></div></details>
</section>"""


def markdown_body(blocks, kind):
    output = []
    for index, (level, text) in enumerate(blocks):
        if index == 0 and level == 1:
            continue

        if kind == "road" and level == 2 and text == "The first decision comes immediately":
            output.append("""<figure class="project-article-figure project-article-figure--timeline" id="roadmap-at-a-glance">
  <img src="{{ '/assets/images/usmnt-road-to-2030-checkpoints.png' | relative_url }}" alt="Timeline of major USMNT checkpoints from summer 2026 through the 2030 World Cup" loading="eager">
  <figcaption>The complete cycle at a glance. Summer 2028 is the central evaluation point, when qualifying, a possible Copa América and the home Olympics could collide.</figcaption>
</figure>""")

        if kind == "road" and level == 2 and text == "Summer 2028 is the critical checkpoint":
            output.append("## Summer 2028 is the critical checkpoint")
            output.append("""<figure class="project-article-figure project-article-figure--checkpoint" id="summer-2028-calendar">
  <img src="{{ '/assets/images/usmnt-summer-2028-checkpoint.png' | relative_url }}" alt="Calendar showing the possible overlap among World Cup qualifying, Copa América and the 2028 Los Angeles Olympics" loading="lazy">
  <figcaption>Three major events could occupy one compressed window. Copa América participation and its exact format remain unconfirmed.</figcaption>
</figure>""")
            continue

        if kind == "prospects" and level == 2 and text == "The Best Bets":
            output.append(prospect_table())

        if level:
            output.append(f"{'#' * level} {text}")
        else:
            output.append(text)

    body = "\n\n".join(output)
    if kind == "road":
        body = body.replace("candidates fo open spots", "candidates for open spots")
    return body + "\n"


def write_post(source_name, target_name, front_matter, kind):
    blocks = convert_docx(ARTICLES / source_name)
    post = f"---\n{front_matter.strip()}\n---\n\n{markdown_body(blocks, kind)}"
    (POSTS / target_name).write_text(post, encoding="utf-8")


write_post(
    "USMNT Prospects Who Could Break Through Before the 2030 World Cup (1).docx",
    "2026-07-26-20-usmnt-prospects-who-could-break-through-by-2030.md",
    """
layout: post
title: "20 USMNT Prospects Who Could Break Through Before the 2030 World Cup"
subtitle: "The best bets, the golden tickets and the long shots who could change the next American player pool."
excerpt: "Twenty young Americans with a plausible path to the 2030 roster, ranked by current evidence, upside and opportunity—and then sorted by the kind of bet each one represents."
date: 2026-07-26 22:30:00 -0400
categories: [project-2030, usmnt]
permalink: /usmnt/20-prospects-who-could-break-through-by-2030/
author: "Randy Morgan"
read_time: 18
section_theme: project
hero_image: /assets/images/usmnt-longform-part2-cavan-sullivan.jpg
hero_wide: true
hero_credit: "Bryan Berlin, CC BY-SA 4.0 / Wikimedia Commons"
hero_credit_url: "https://commons.wikimedia.org/wiki/File:Cavan_Sullivan_Philadelphia_Chicago_10.26.25-117.jpg"
prospect_feature: true
    """,
    "prospects",
)

write_post(
    "The Road to 2030.docx",
    "2026-07-26-road-to-2030-summer-2028.md",
    """
layout: post
title: "The Road to 2030: Why Summer 2028 Will Define the Next USMNT Cycle"
subtitle: "Qualifying pressure returns quickly, but one crowded summer could tell us more than any other stretch before the World Cup."
excerpt: "A four-year map of the coaching decisions, tournaments and qualifying windows that will shape the USMNT—with summer 2028 emerging as the cycle's defining test."
date: 2026-07-26 22:45:00 -0400
categories: [project-2030, usmnt]
permalink: /usmnt/road-to-2030-summer-2028/
author: "Randy Morgan"
read_time: 13
section_theme: project
thumbnail: /assets/images/usmnt-summer-2028-checkpoint.png
checkpoint_feature: true
    """,
    "road",
)
