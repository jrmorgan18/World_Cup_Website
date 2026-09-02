---
layout: post
title: "European Power Rankings: Roma Surges, PSG Wobbles and Leverkusen Falls Out"
subtitle: "The first in-season update keeps PSG at No. 1, lifts Roma three places and sends Bayer Leverkusen out of the Top 20."
excerpt: "PSG hold the top spot despite another draw, Roma make the week’s biggest move and Aston Villa enter as Bayer Leverkusen fall out."
date: 2026-09-01 19:00:00 -0400
categories: [analysis]
thumbnail: /assets/images/psg-celebration.jpg
hero_image: /assets/images/psg-celebration.jpg
hero_alt: "PSG players celebrating a Champions League title"
newsletter_cta: true
power_rankings_feature: true
power_rankings_edition: "2026-27-week-1"
source_docx: "articles/European Power Rankings 9_1_ Roma Surges, PSG Wobbles and Leverkusen Falls Out.docx"
home_recent: true
home_recent_position: 2
home_recent_label: "European Power Rankings"
home_recent_theme: soccer
feature_label: "European Power Rankings"
feature_badge: "Week 1"
feature_kicker: "Europe"
feature_topic: "Top 20"
---

The European season is still young enough that one result can dramatically change the conversation around a team, but it probably should not dramatically change the power rankings.

These rankings are not simply a list of who won over the weekend. They are an attempt to answer a slightly different question: if these teams played tomorrow on a neutral field, who would I trust the most?

That means PSG can survive another disappointing draw at No. 1. Liverpool can remain relatively high despite failing to win either of its Premier League games. Aston Villa can somehow enter the rankings while sitting on zero points.

Still, the results are beginning to provide real evidence.

Bayern finally opened its Bundesliga season by scoring five. Real Madrid scored eight goals in two games. Manchester City looked considerably more comfortable in its second match under Enzo Maresca. Roma followed one 4-0 win with another and suddenly looks like one of the most interesting teams in Italy.

At the opposite end, Bayer Leverkusen managed to lose its Bundesliga opener to newly promoted Elversberg.

That one will cost you.

{% assign ranking_edition = site.data.european_club_power_rankings.editions | where: "id", page.power_rankings_edition | first %}
{% if ranking_edition %}
<div class="power-rankings-board" aria-label="European Club Power Rankings Top 20">
{% for ranking_tier in ranking_edition.tiers %}
  <section class="power-rankings-tier-card power-rankings-tier-card--{{ ranking_tier.id }}">
    <header>
      <p>Tier {{ ranking_tier.id }}</p>
      <h2>{{ ranking_tier.label }}</h2>
      <span>{{ ranking_tier.range }}</span>
    </header>
    <ol>
    {% for ranked_team in ranking_edition.rankings %}
      {% if ranked_team.tier == ranking_tier.id %}
      <li>
        <a href="#rank-{{ ranked_team.rank }}">
          <b>{{ ranked_team.rank }}</b>
          <span class="power-rankings-club-mark"><img src="{{ ranked_team.logo | relative_url }}" alt="" width="42" height="42" loading="lazy"></span>
          <span class="power-rankings-club-name">{{ ranked_team.team }}</span>
          <small><span>Prev.</span>{% if ranked_team.previous %}{{ ranked_team.previous }}{% else %}&mdash;{% endif %}</small>
        </a>
      </li>
      {% endif %}
    {% endfor %}
    </ol>
  </section>
{% endfor %}
</div>
{% endif %}

{% include power-ranking-tier-heading.html tier=1 %}

These are the teams best positioned to compete for both their domestic league and the Champions League.

{% include power-ranking-team-heading.html rank=1 %}

PSG remains No. 1, although the grip on the spot is getting considerably weaker.

For the second straight Ligue 1 game, Paris needed a comeback just to earn a 2-2 draw. Lille went up 2-0 on Friday before PSG scored twice in stoppage time, with Marquinhos finally rescuing the point deep into added time.

There is something impressive about having enough quality and belief to repeatedly rescue games that appear lost. There is also a point where constantly needing to rescue them becomes the problem.

PSG stays first because a power ranking should not completely reset after two league games. But another performance like this and someone else is going to have to take the top spot almost by default.

{% include power-ranking-team-heading.html rank=2 %}

Arsenal did not exactly overwhelm Aston Villa, but winning 1-0 on the road is the type of result defending champions happily take and move on from.

Bukayo Saka supplied the winner in the second half, while Arsenal again gave up very little defensively. Villa hit the crossbar in the first half but failed to put a shot on target for the second consecutive game.

The attack was much less fluid than it was in the 3-0 opener against Coventry. The larger point remains the same.

Arsenal already knows how it wants to play. The press, defensive spacing and basic possession structure do not need to be rebuilt around a new coach. When the attack is not particularly sharp, the defense gives them a chance to win 1-0 anyway.

They remain the safest challenger to PSG.

{% include power-ranking-team-heading.html rank=3 %}

Barcelona had a busy week and came out of it with six points and seven goals.

They first handled Athletic Club 2-0 in the delayed Matchday 1 fixture, then beat Rayo Vallecano 5-2 Monday. Raphinha scored three times across the two games, while Lamine Yamal added two against Rayo.

Barcelona has now scored 12 goals through its first three league matches.

The striker question from the preseason has not disappeared, but Barcelona is demonstrating why it may not need a traditional replacement for Robert Lewandowski to maintain an elite attack. The movement of Raphinha, Yamal, Dani Olmo and the other attacking midfielders creates enough uncertainty that opponents cannot simply defend one central reference point.

There will be stronger tests than Elche, Athletic and Rayo. So far, however, Barcelona looks a lot like the team that started these rankings at No. 3.

{% include power-ranking-team-heading.html rank=4 %}

The Bundesliga finally started and Bayern apparently got tired of waiting.

They beat Stuttgart 5-1, with Michael Olise again among the scorers after his excellent Supercup performance. Dayot Upamecano, Aleksandar Pavlović and Luis Díaz also scored as Bayern turned a 1-1 game early in the second half into a rout.

Bayern has enough attacking variety that Harry Kane does not need to score every week for the offense to overwhelm teams. Olise is becoming especially difficult to deal with because he can create from wide areas, move centrally and finish attacks himself.

Nobody above Bayern did enough wrong to justify a move this week.

Bayern did enough to make No. 4 look increasingly conservative.

{% include power-ranking-team-heading.html rank=5 %}

Real Madrid may have the strongest argument for moving up without actually moving.

José Mourinho's team beat Real Sociedad 4-1 in its delayed opener and followed it with a 4-0 demolition of Málaga. Madrid has now won its first three league games under Mourinho.

Jude Bellingham opened the scoring against Málaga with an excellent individual goal, Kylian Mbappé added another and Arda Güler finished the rout.

The more encouraging development is that Madrid is beginning to look less like a collection of ridiculous individual talent and more like a team with an idea of how to use it.

We knew the transition attack would be terrifying. If Mourinho can also create enough structure around Bellingham and the deeper midfielders to control games when opponents sit back, Madrid has as much upside as anyone on this list.

{% include power-ranking-tier-heading.html tier=2 %}

Each of these teams has the quality to challenge at home and make a serious Champions League run.

{% include power-ranking-team-heading.html rank=6 %}

Inter followed its 4-1 opening win over Monza with a much less spectacular but equally useful 1-0 victory at Cagliari.

Hakan Çalhanoğlu scored after only ten minutes and Inter spent much of the first half creating opportunities to put the game away before ultimately having to protect the one-goal margin.

The reigning Serie A champions have now shown two different routes to three points. They overwhelmed Monza. They controlled Cagliari without finishing enough of their chances and survived anyway.

Roma is suddenly generating more excitement further down the rankings, but Inter remains the top team in Serie A..

{% include power-ranking-team-heading.html rank=7 %}

This looked considerably more like the Manchester City we know.

After needing two late goals from center backs to escape Bournemouth, City went to Crystal Palace and won 4-1 behind braces from Erling Haaland and Rayan Cherki.

Cherki is becoming particularly interesting in Maresca's version of the team. Against Bournemouth his introduction changed the match. Against Palace he started and became the most influential attacking player on the field.

City still looks different without Pep Guardiola and Rodri. Maresca is moving pieces around the midfield and fullback areas searching for his preferred structure.

Having Cherki and Haaland deciding games gives him a little time to figure it out.

{% include power-ranking-team-heading.html rank=8 %}

Chelsea has played two Premier League games under Xabi Alonso and won them by scores of 3-2 and 4-3. They have been anything but boring.

The latest win came against Brighton, with Chelsea racing to a 3-0 advantage before allowing the game to become considerably more uncomfortable. Cole Palmer eventually scored the fourth to secure another three points.

The attack already looks dangerous. Palmer, João Pedro and the surrounding pieces are finding space and rotating well enough that Chelsea can create chances in several different ways.

The five goals conceded across two matches tell the other side of the story. Chelsea has not demonstrated anywhere near the defensive control of Arsenal or Inter.

There is a very good team in here. Alonso is still figuring out how chaotic it needs to be.

{% include power-ranking-team-heading.html rank=9 %}

Manchester United got the response they desperately needed with a 5-2 win over Ipswich to rebound from their opening week loss.

United actually fell behind again before Bruno Fernandes took over, scoring a hat trick as Michael Carrick's team turned what briefly threatened to become another embarrassing afternoon into a comfortable win.

The difference from the Hull game was not merely better finishing. United played with more movement around Fernandes and gave him more opportunities to arrive in dangerous areas rather than asking him to manufacture everything from deeper positions.

One good performance against a promoted side does not erase the opener.

It does at least offer evidence that the new midfield and attack may eventually become considerably better than what we saw at Hull.

{% include power-ranking-team-heading.html rank=10 %}

Atlético has quietly started very well, beating Málaga 2-0 in their delayed opener, drawing 2-2 with Villarreal, then going to Sevilla and winning 3-1 without Julián Álvarez. Alex Baena scored twice in the first 33 minutes and Ademola Lookman added another as Atlético took control early.

That is encouraging because the biggest preseason question was whether all the summer additions would actually fit together. The early signs are positive. Baena and Kang-in Lee add technical quality around the attack, while Simeone has enough midfield and defensive options to change the shape depending on the opponent.

They have not done enough to crack the top nine yet, but they are getting closer.

{% include power-ranking-team-heading.html rank=11 %}

Liverpool remains one of the toughest teams to rank. They have enough talent to beat nearly anyone on this list. They also have two points from their first two Premier League games after following the 2-2 draw at Newcastle with another 2-2 draw against Nottingham Forest at Anfield.

Once again, they had to come from behind twice. Alexander Isak scored his first league goal of the season and Victor Muñoz rescued the point late, but Forest repeatedly exposed Liverpool when possession changed. Despite Liverpool holding 70 percent of the ball, Forest created several of the better opportunities.

Andoni Iraola's attacking ideas are already visible.

So are the spaces behind them.

Liverpool is too talented to drop much farther yet, but eventually the ranking has to reflect the results.

{% include power-ranking-tier-heading.html tier=3 %}

These clubs remain capable of forcing their way into a domestic title conversation or making Europe uncomfortable.

{% include power-ranking-team-heading.html rank=12 %}

Napoli lost 2-1 at home to Como on Sunday, with Cesc Fàbregas's team becoming the latest reminder that it is no longer useful to treat Como like some cute little promotion story. They are capable of beating major Serie A teams.

Napoli entered the season with legitimate expectations of competing near the top of Serie A and should not be losing these games at home. For now, the larger body of talent keeps them at 12.

Roma is coming quickly from behind.

{% include power-ranking-team-heading.html rank=13 %}

Dortmund recovered nicely from the Supercup loss to Bayern by beating Hamburg 2-0 in its Bundesliga opener, with Serhou Guirassy and Giannis Konstantelias supplying the goals in a relatively comfortable start to the league campaign.

There is still a sizeable distance between what Bayern showed against Stuttgart and Dortmund showed against Hamburg. That does not make Dortmund bad. It simply makes the Bundesliga hierarchy fairly obvious at the moment.

{% include power-ranking-team-heading.html rank=14 %}

Brighton's opening 4-0 demolition of Aston Villa was never going to be reproduced every week.

Their follow-up was much stranger, falling behind Chelsea 3-0 but refusing to disappear and eventually turning the game into a 4-3 loss that forced Chelsea to keep playing until the final whistle.

The defensive problems were obvious. Chelsea repeatedly found spaces before Brighton could organize itself. The response was encouraging enough to keep them from falling.

Brighton remains aggressive, technically capable and willing to commit numbers forward. Against weaker teams, that approach should produce plenty of points. Against the best teams, they may have to find a better balance between attacking pressure and leaving the back line exposed.

{% include power-ranking-team-heading.html rank=15 %}

Here comes Roma.

After opening the Serie A season by destroying Fiorentina 4-0, Roma went to Lecce and won by the exact same score.

Donyell Malen scored twice more, giving him five goals through two games, while Matías Soulé and Rodrigo Mora added the others.

Gian Piero Gasperini has quickly created an attack where the forwards interchange, players aggressively attack the spaces opened by teammates and Roma looks to punish teams before they can reorganize.

Malen has been the perfect beneficiary. He does not need the ball constantly. He needs someone to pull a defender away and enough space to attack the opening.

Dybala, Soulé and the rest of Roma's creators are giving him plenty.

Two matches against Fiorentina and Lecce do not make Roma a Scudetto favorite.

{% include power-ranking-team-heading.html rank=16 %}

Juventus is also perfect through two matches, although the performances have been considerably less explosive than Roma's.

They beat Parma 2-0 after substitutes Nico González and Teun Koopmeiners finally broke through in the second half.

Juventus has now started with two wins and two clean sheets.

There is value in that, particularly while Luciano Spalletti continues sorting through his attacking options. The defense looks dependable enough to keep Juventus in matches even when the possession and chance creation are not particularly convincing.

Roma jumps them because the early ceiling looks higher.

Juventus remains directly behind because its floor may be safer.

{% include power-ranking-team-heading.html rank=17 %}

Brentford's 3-0 win over Tottenham was one of the performances of opening weekend, but they could not quite reproduce it against Leeds.

Kevin Schade gave Brentford the lead, but Leeds changed its shape and added another midfielder after halftime, gradually taking greater control before Dominic Calvert-Lewin equalized. The game finished 1-1.

This was not a bad performance. Brentford was the better team for significant stretches and remains unbeaten.

The drop is mostly about what happened around them.

Roma forced its way upward. Juventus keeps winning. Brentford had a chance to back up the Tottenham result with another three points and could not finish the job.

{% include power-ranking-team-heading.html rank=18 %}

Bournemouth has played well enough to have more than one point.

They pushed Manchester City to the final minutes in the opener and then led Everton before James Tarkowski's late equalizer produced a 1-1 draw.

The structure still looks good. Bournemouth can press, defend compactly and make opponents uncomfortable moving through midfield.

Eventually those encouraging performances need to become wins.

For now they slide one place, more because Roma and PSV are making stronger cases than because Bournemouth suddenly looks bad.

{% include power-ranking-tier-heading.html tier=4 %}

The final two places belong to teams still building their case against Europe’s deepest fields.

{% include power-ranking-team-heading.html rank=19 %}

PSV probably deserves more attention after this weekend.

Going to Utrecht and winning 6-1 is not a normal road result.

PSV finished with 30 shots, 14 on target and six different scoring sequences after initially falling behind in the sixth minute. Sergiño Dest assisted Guus Til before halftime and then scored the sixth himself in stoppage time.

PSV has the disadvantage of being evaluated against teams from stronger leagues, which limits how quickly an Eredivisie blowout can move them up this list.

But they are doing essentially everything possible to make the argument.

Another few performances like this and No. 19 will look silly.

{% include power-ranking-team-heading.html rank=20 %}

Yes, Aston Villa has zero points.

Yes, Aston Villa has zero goals.

And yes, they somehow enter the power rankings.

This is mostly about what happened to Bayer Leverkusen.

Villa at least looked much more organized in the 1-0 loss to Arsenal than it did while conceding four goals in 31 minutes against Brighton. They made Arsenal work, hit the crossbar through Emi Buendía and remained in the game until the end.

There are still major problems. The summer turnover has left Unai Emery rebuilding a roster that looks considerably weaker than last season's version, and an attack that has failed to put a shot on target through two games is difficult to excuse.

But Leverkusen opened its Bundesliga season by losing 3-2 to newly promoted Elversberg, falling behind 2-0 inside ten minutes.

Someone has to be No. 20.

For now, Villa gets the benefit of the doubt.

## Out: Bayer Leverkusen

Losing on the road happens.

Losing to Bayern happens.

Losing your Bundesliga opener to a club playing the first top-flight match in its history is a little harder to wave away.

Elversberg beat Leverkusen 3-2 after scoring twice in the opening ten minutes. Leverkusen had plenty of time to recover and never completely did.

One game does not mean the season is doomed.

It is enough to lose your spot in the Power Rankings.

