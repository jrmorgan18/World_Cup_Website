---
layout: post
title: "European Club Power Rankings: The Preseason Top 20"
subtitle: "PSG remain the standard, Arsenal lead the challengers and a summer of major change reshapes Europe's elite."
excerpt: "The first European Club Power Rankings of 2026-27, weighing recent results, summer transfers, injuries, coaching changes and continuity."
date: 2026-08-13 09:00:00 -0400
categories: [analysis]
thumbnail: /assets/images/psg-celebration.jpg
hero_image: /assets/images/psg-celebration.jpg
hero_alt: "PSG players celebrating their 2026 Champions League title"
newsletter_cta: true
power_rankings_feature: true
power_rankings_edition: "2026-27-preseason"
source_docx: "articles/European Club Preseason Power Rankings.docx"
---

The European club season is getting underway, which means it is time for the preseason edition of my European Top 20 Power Rankings.

These are power rankings, not a prediction of the final Premier League table, Champions League finish or some attempt to objectively determine the 20 biggest clubs in Europe. Recent results establish the baseline, but the rankings also account for summer transfers, injuries, coaching changes and how much of last season's team remains intact.

That last part is especially important this year. Several of Europe's biggest clubs made significant changes over the summer, while others largely brought back teams that were already competing for the biggest trophies.

The transfer window is also still open, so consider this a snapshot as of August 13. A major signing, departure or injury could move some of these teams before September.

For now, though, one club remains at the top until somebody actually knocks them off.

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

These are the five teams that should enter the season believing they can win both their domestic league and the Champions League.

{% include power-ranking-team-heading.html rank=1 %}

There isn't much of an argument for putting anyone else first.

PSG have won the Champions League in back-to-back seasons and opened this campaign by beating Aston Villa 2-1 in the UEFA Super Cup. At some point another club will take the European crown away from them, but until that happens the two-time defending champions remain the standard.

More importantly, this isn't a champion being dismantled after reaching the summit. Most of the core remains together, while Maghnes Akliouche and Lucas Digne add even more quality and depth.

There are teams below them that may have made flashier additions, but PSG don't need to win the transfer window. They already won the Champions League. Twice.

{% include power-ranking-team-heading.html rank=2 %}

If anyone has a legitimate argument that they are already PSG's equal, it is Arsenal.

The reigning Premier League champions came within a penalty shootout of winning the Champions League as well. They were already one of the two or three best teams in Europe last season and then added Bruno Guimarães to an excellent midfield.

Arsenal also made Piero Hincapié's move permanent and added Christos Tzolis, giving them even more options in a squad that did not have many obvious weaknesses to begin with.

The major preseason concern is William Saliba's back injury. Arsenal's defensive reliability has been central to their rise, and Saliba is one of the players they would least want to lose for an extended stretch.

If he returns healthy, this may be the strongest Arsenal team of the current era. They have moved beyond simply hoping to win the Premier League. The expectation should now be to challenge for everything.

{% include power-ranking-team-heading.html rank=3 %}

Bayern retained the Bundesliga in dominant fashion last season and added the DFB-Pokal to complete the domestic double. They finished with 89 points and scored a Bundesliga-record 122 goals, then came extremely close to adding a Champions League final appearance, losing to PSG by a single goal over two semifinal legs.

That puts them firmly back among the elite.

The summer wasn't as dramatic as some of the teams below them, but adding Ismael Saibari from PSV should improve the midfield, while Nathaniel Brown gives them another option at the back. Leon Goretzka and Raphaël Guerreiro departing removes some veteran depth but doesn't fundamentally change the outlook.

Bayern remain the clearest favorite in Germany, which gives them a relatively straightforward path to another successful domestic season. The bigger question is whether they can turn another deep Champions League run into a trophy.

There isn't much separating the teams from second through fifth. Bayern get the slight edge because we already saw this version of the team come within a few moments of reaching the final.

<figure class="soccer-article-figure soccer-article-figure--portrait">
  <img src="{{ '/assets/images/kane-bayern.jpg' | relative_url }}" alt="Harry Kane celebrating in a Bayern Munich shirt" loading="lazy">
  <figcaption>Harry Kane remains the reference point for a Bayern side coming off a 122-goal Bundesliga season.</figcaption>
</figure>

{% include power-ranking-team-heading.html rank=4 %}

The most frightening thing about Barcelona is that so many of their best players should still be improving.

Lamine Yamal, Pedri and Pau Cubarsí form the core of a team that has already won consecutive La Liga titles. Now Barcelona have added Anthony Gordon and Karim Adeyemi to an attack that hardly lacked talent.

Their ceiling going forward is enormous.

They have lost Ronald Araújo on loan to Liverpool and Marc-André ter Stegen to a loan to Ajax, but neither played significant minutes last season.

They are pursuing a deal to sign Rodri away from Manchester City, which would potentially boost them higher in these rankings, adding perhaps the best holding midfielder in the game to their already loaded midfield of Pedri, Frenkie de Jong, Marc Bernal and Gavi. It would both raise their ceiling and give them additional depth to insure them against injuries. Rodri could also help improve a defense that remains a question mark at times.

They are also pursuing Julián Álvarez of Atlético Madrid as a replacement and upgrade at striker from the departed Robert Lewandowski.

Barcelona should score plenty of goals. We already know they are good enough to win Spain. Whether they can consistently defend the best teams in Europe is what separates them from PSG and Arsenal at the top of this list.

{% include power-ranking-team-heading.html rank=5 %}

It feels strange calling Manchester City the most uncertain team in any elite group, but this is not quite the City roster we have become accustomed to.

They still finished second in the Premier League last season, so there wasn't exactly a collapse domestically. Their Champions League exit was another story, with Real Madrid overwhelming them in the round of 16.

Now comes a significant transition.

Not only is Enzo Maresca replacing coaching legend Pep Guardiola, but Bernardo Silva, John Stones, Manuel Akanji and Nathan Aké all departed over the summer. That is an enormous amount of experience. Elliot Anderson is an excellent addition, but City are asking a new coach to integrate a new collection of players to replace several pillars of the team that dominated England for years.

The ceiling remains obvious. City still have enough talent to win the Premier League and Champions League.

There is simply more uncertainty around them than there has been in a long time.

{% include power-ranking-tier-heading.html tier=2 %}

All six of these teams can win a major domestic league and make a serious Champions League run. Each also has at least one question that keeps them outside the top five.

{% include power-ranking-team-heading.html rank=6 %}

No team is harder to rank.

Purely on paper, Real Madrid may have the best roster in Europe.

Madrid added Yan Diomande, Bernardo Silva, Ibrahima Konaté, Marc Cucurella and Denzel Dumfries. José Mourinho is back as manager. It is the kind of summer that looks like somebody turned off financial restrictions in a video game.

But Madrid had plenty of superstars last year and failed to find cohesion or the success they expect.

They are coming off two consecutive trophyless seasons in which assembling the most famous collection of players did not necessarily produce the best team. Adding another group of big names doesn't automatically solve that problem.

Maybe Mourinho finds the right balance immediately and Madrid are back at No. 1 by October. I wouldn't be remotely surprised.

For the preseason ranking, though, I need to see it work first.

{% include power-ranking-team-heading.html rank=7 %}

After years of false starts, Manchester United finally appear to be moving in the right direction.

A third-place Premier League finish established them as a legitimate challenger rather than another expensive rebuilding project. The summer should help accelerate that progress.

Andrey Santos and Youri Tielemans provide a major refresh in midfield, while Rasmus Højlund, Casemiro and André Onana are among the notable departures.

United now need to prove last season wasn't simply one good year. The gap between finishing third and actually beating Arsenal and Manchester City over a full season remains significant.

Still, this is probably the most optimistic United have had reason to be in quite a while.

{% include power-ranking-team-heading.html rank=8 %}

Inter remain the safest bet in Italy.

They are the reigning Serie A champions and have the combination of experience, tactical structure and depth needed to win it again. Adding John Stones and Manuel Akanji only increases that experience, particularly in a defense that should be comfortable handling big European games.

The reason Inter aren't higher is what happened in Europe last season.

Losing to Bodø/Glimt in the Champions League playoff was a massive disappointment for a club with legitimate aspirations of making another deep run.

My inclination is to treat that as an aberration rather than evidence that Inter have suddenly become a mediocre European team. But they need to prove it.

{% include power-ranking-team-heading.html rank=9 %}

This is easily one of the biggest projection bets in the ranking.

Chelsea finished 10th in the Premier League last season. Teams finishing 10th do not normally enter the following year ranked among Europe's top ten.

But almost everything about Chelsea looks different entering this season. They aggressively upgraded the roster with Morgan Rogers, Geovany Quenda, Maxence Lacroix and Marco Palestra among the additions, while also handing the team to new manager Xabi Alonso.

Alonso is probably the most interesting part of the equation. He led Bayer Leverkusen to an unbeaten Bundesliga title before his less successful stint at Real Madrid, and Chelsea are betting that he can impose some structure on a roster that has often looked more like a collection of expensive young players than a coherent team. If nothing else, his track record at Leverkusen provides a legitimate reason to believe he can get more out of the talent already there.

There is also considerable risk. Alonso is taking over another dramatically reshaped roster, and Chelsea are asking a lot of new players to quickly understand their roles and each other.

That is ultimately why they land at No. 9. The talent, new signings and Alonso give Chelsea one of the highest ceilings outside the top group. But after finishing 10th, they still have to demonstrate that all of those pieces actually form a good soccer team.

{% include power-ranking-team-heading.html rank=10 %}

Atlético's 2025-26 season probably deserves more attention than it received.

They reached the Champions League semifinals and the Copa del Rey final, proving they could compete deep into major knockout competitions.

The summer brought Morten Hjulmand, Alejandro Grimaldo and Kang-in Lee, all of whom should strengthen an already competitive roster.

The cloud hanging over everything is Julián Álvarez, who has publicly pushed for a move. Losing him would considerably change the attacking outlook.

Atlético also haven't won La Liga in five years. At some point, consistent competitiveness has to turn back into trophies if they want to move into the top tier.

{% include power-ranking-team-heading.html rank=11 %}

Liverpool have enough talent to remain dangerous, but no Tier 2 team enters the season with more change.

Mohamed Salah, Ibrahima Konaté and Andy Robertson are gone. Those aren't just three starters. They were three pillars of the previous Liverpool era.

There is also a major change on the sideline, with Andoni Iraola replacing Arne Slot as head coach. Iraola earned the opportunity after an impressive three-year run at Bournemouth, culminating in a sixth-place Premier League finish last season. His aggressive, high-energy approach makes him an intriguing fit for Liverpool, but implementing a new system while simultaneously replacing several foundational players adds another layer of uncertainty.

Liverpool responded to the personnel losses with Ronald Araújo on loan and younger additions including Jérémy Jacquet and Victor Muñoz. There is still plenty to like about the roster, and Liverpool did reach the Champions League quarterfinals last season.

But they also finished fifth in the Premier League before losing all that experience and changing coaches.

Iraola could inject new energy into the team and make this ranking look conservative. For now, Liverpool have more to prove than the teams directly above them.

{% include power-ranking-tier-heading.html tier=3 %}

These teams can challenge for a domestic championship or make a surprising Champions League run, but reaching the European semifinals would be an achievement rather than the expectation.

{% include power-ranking-team-heading.html rank=12 %}

Napoli finished second in Serie A and should once again be one of Inter's primary challengers.

Massimiliano Allegri takes over as manager, while Rasmus Højlund's move was made permanent. Romelu Lukaku departed for Fenerbahçe.

There is enough here to win Italy if things fall into place, but Napoli don't quite have the same European ceiling as the teams in the first two tiers.

{% include power-ranking-team-heading.html rank=13 %}

Dortmund finished second in Germany last year, but their European campaign ended much earlier than their talent suggested it should.

The summer brought another round of transition. Konstantinos Karetsas and Joane Gadou are intriguing young additions, while Karim Adeyemi, Julian Brandt and Niklas Süle all departed.

Dortmund remain Bayern's most credible Bundesliga challenger. The question is whether all that turnover leaves them spending the first half of the season figuring out what they are.

{% include power-ranking-team-heading.html rank=14 %}

Few teams in this tier can match Villa's recent results.

They finished fourth in the Premier League, won the Europa League and then gave PSG a competitive game in a 2-1 UEFA Super Cup loss.

The problem is that the team responsible for those accomplishments no longer exists in quite the same form.

Morgan Rogers, Youri Tielemans, Lucas Digne and Donyell Malen all left. Johan Manzambi, João Gomes and Alejandro Garnacho headline the replacements.

That is enough talent to keep Villa competitive. But after losing that much proven production, they have to earn their way back toward the top ten.

{% include power-ranking-team-heading.html rank=15 %}

Juventus continue to look like a team moving toward contention without quite being there yet.

Making Randal Kolo Muani's move permanent gives them a proven forward, while Kerim Alajbegović adds another interesting attacking option.

But last season's Champions League playoff exit was a pretty clear indication of the existing gap.

Juventus can challenge in Serie A. I need to see more before considering them a serious Champions League threat.

{% include power-ranking-team-heading.html rank=16 %}

This one may be a surprise to those not paying close attention.

Bournemouth finished sixth in the Premier League last season and earned European soccer. At some point, actual week-to-week performance has to matter more than the badge on the shirt.

Adding António Silva should help compensate for Marcos Senesi's move to Tottenham.

Now comes a different challenge. Bournemouth have to maintain that Premier League standard while adding European games to the schedule.

If they do it, their rise is no longer a cute story. They're simply one of the better teams in Europe.

{% include power-ranking-team-heading.html rank=17 %}

Leverkusen have come back toward earth after their remarkable peak.

They finished sixth in the Bundesliga last season and Arsenal eliminated them in the Champions League round of 16.

There has been considerable change at the back as well, with Alejandro Grimaldo and Piero Hincapié departing and Facundo Medina and Miguel Gutiérrez arriving.

There is still enough talent for Leverkusen to rebound. I just see a team retooling rather than one prepared to immediately jump back among Europe's elite.

{% include power-ranking-team-heading.html rank=18 %}

Brighton are the other Premier League team whose ranking benefits from the level of competition they face every week.

They finished eighth last season and qualified for the Conference League. Luka Vušković and Pascal Struijk reinforce the roster, although Jan Paul van Hecke and Danny Welbeck are among the experienced players who departed.

PSV and Sporting have stronger recent histories of actually winning things. Brighton get the nod because surviving near the top of the Premier League week after week is a pretty convincing demonstration of quality.

Europe now gives them another opportunity to prove it outside England.

{% include power-ranking-tier-heading.html tier=4 %}

The final two teams enter the year as major domestic contenders with enough quality to cause problems in Europe. Their path to the very top is simply more difficult.

{% include power-ranking-team-heading.html rank=19 %}

PSV are the defending Eredivisie champions and remain one of the two dominant teams in the Netherlands.

The biggest concern is obvious: Ismael Saibari is now at Bayern Munich.

Losing one of your best midfielders to the team ranked third on this list is a pretty good illustration of the structural challenge PSV face. They can replace players well enough to remain a domestic power, but keeping enough elite talent together to seriously challenge for the Champions League is another matter.

{% include power-ranking-team-heading.html rank=20 %}

Sporting had a strange 2025-26 season. They reached the Champions League quarterfinals and produced the best attack in Portugal, but ultimately finished the domestic season without a trophy.

FC Porto beat them to the league title despite Sporting's prolific attack, led by league-leading scorer Luís Suárez. The bigger disappointment came in the Taça de Portugal final, where Sporting lost 2-1 to second-division Torreense.

Their position falls even further because of what happened this summer. Geovany Quenda went to Chelsea, Morten Hjulmand to Atlético Madrid and Ousmane Diomande to Nottingham Forest. That's a painful amount of high-end talent to replace at once.

Sporting should still be one of the main contenders in Portugal, and last season's Champions League run showed they can compete with stronger European opposition. But after losing the domestic title, the cup final and several of their best players, assuming they can immediately reproduce last season's European success would be a stretch.
