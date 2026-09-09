---
layout: post
title: "European Power Rankings: Barcelona Takes No. 1 as the Champions League Begins"
excerpt: "Barcelona takes the top spot after a five-goal win at Valencia, while PSG falls to fourth and the Champions League finally gives the rankings their first real test."
date: 2026-09-08 23:30:00 -0400
categories: [analysis]
section_theme: soccer
permalink: /soccer/european-power-rankings-2026-09-08/
author: "Randy Morgan"
read_time: 17
thumbnail: /assets/images/barcelona-power-rankings-2026-09-08.jpg
hero_image: /assets/images/barcelona-power-rankings-2026-09-08.jpg
hero_alt: "Lamine Yamal attacks for Barcelona against Valencia"
hero_wide: true
newsletter_cta: true
power_rankings_feature: true
power_rankings_edition: "2026-27-week-2"
source_docx: "articles/European Power Rankings 9_8.docx"
home_recent: true
home_recent_label: "European Power Rankings"
home_recent_theme: soccer
feature_label: "European Power Rankings"
feature_badge: "Week 2"
feature_kicker: "Europe"
feature_topic: "Top 20"
---

The Champions League begins this week, which means the European power rankings are finally about to be put to the test.

Comparing Barcelona rolling through La Liga with Arsenal beating Premier League opponents or Inter winning in Serie A can only tell us so much. Now the best teams start playing each other.

The opening slate gives us Real Madrid against Inter immediately, followed Wednesday by Napoli-Arsenal and Liverpool-Atlético Madrid. Barcelona begins against Feyenoord, while Bayern, Roma, Manchester United and PSV join the competition Thursday.

These rankings are locked based on results through Monday, before the Champions League games began.

There is also a new No. 1.

Barcelona has scored 17 goals through four league matches and just went to Valencia and won 5-0. Arsenal passed its first major domestic test against Chelsea. Inter came back from two goals down to beat Napoli.

Meanwhile, PSG is still searching for its first league win, Real Madrid finally lost and Atlético got hammered at San Mamés.

The early-season sample is no longer completely meaningless.

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

{% include power-ranking-team-heading.html rank=1 %}

Last Week: 3 | Up 2

Barcelona has done enough to take the top spot.

Hansi Flick's team went to Mestalla and dismantled Valencia 5-0, its second 5-0 road win in four league games. Lamine Yamal scored twice, while Fermín López, Raphinha and Pedri added the others. Barcelona is now 4-0-0 with 17 goals scored and only two conceded.

The preseason question was whether Barcelona could maintain the same level of attack after losing Robert Lewandowski and going into the season without an obvious traditional striker.

So far, the answer has been to make the attack even less dependent on a striker.

Raphinha can move centrally. Fermín attacks the spaces around him. Lamine can create or finish from the right. Pedri determines when the possession should accelerate. Barcelona is getting runners into the box from enough different positions that opponents have not been able to solve the absence of one central reference point.

There will be much more difficult defensive tests.

Feyenoord is first up in the Champions League, followed in October by Galatasaray and PSG.

For now, Barcelona has been the most convincing team in Europe.

{% include power-ranking-team-heading.html rank=2 %}

Last Week: 2

Arsenal finally conceded a league goal.

It still won.

Chelsea scored after only two minutes at the Emirates, but Arsenal gradually took control, equalized through Kai Havertz and won 2-1 when Martin Ødegaard finished after a clever Havertz dummy early in the second half.

This was a much more useful test than beating Coventry or an Aston Villa team that currently seems incapable of scoring.

Chelsea has enough attacking talent to punish mistakes and was dangerous again late. Arsenal still managed the game well enough to recover from the early goal without becoming frantic.

That is probably the defining quality of this team right now.

Arsenal does not require everything to go according to plan. The defensive structure is good enough to survive uncomfortable stretches, and there are enough different sources of attacking quality to find a goal without Bukayo Saka having to create every dangerous moment.

The next test is considerably different.

Arsenal goes to Napoli on Wednesday, a matchup against a wounded team that still has enough talent to expose any complacency.

{% include power-ranking-team-heading.html rank=3 %}

Last Week: 4 | Up 1

Bayern moves up despite producing one of the strangest results of the weekend.

After scoring five against Stuttgart in the Bundesliga opener, Bayern went to newly promoted Schalke and drew 0-0. Their 59-match scoring streak came to an end.

Vincent Kompany did rotate, leaving Harry Kane and Michael Olise on the bench before introducing both during the second half.

There is obviously no reason to panic about one goalless draw, particularly after Bayern already beat Dortmund in the Supercup and overwhelmed Stuttgart in the opener. But it was a useful reminder that all the attacking talent does not automatically solve a compact opponent if the passing becomes too predictable.

Bayern moves up mostly because PSG has earned its drop.

The larger body of evidence remains strong enough to keep Bayern in the top three.

{% include power-ranking-team-heading.html rank=4 %}

Last Week: 1 | Down 3

At some point, the results have to count.

PSG is still the defending European champion and still has perhaps the strongest argument for being the most talented team on the continent.

It also has two points through three Ligue 1 games.

The latest stumble was worse than the first two. PSG led Monaco 1-0 at halftime through Marquinhos, then conceded twice after the break and lost 2-1 at home. The result leaves Paris winless through its opening three league matches for the first time since 2012-13. Its two points are its fewest through three matches since 2007-08.

Luis Enrique offered a reasonable defense afterward. Monaco scored on both of its shots on target, while PSG pressed well and controlled significant portions of the game.

Power rankings should not pretend finishing variance does not exist. A strong performance can produce a bad result.

The problem is that this is now three bad results.

PSG remains fourth because its ceiling has not disappeared in two weeks. But Barcelona, Arsenal and Bayern have provided much stronger current evidence.

The Champions League should offer PSG an easy opportunity to reset against Slovan Bratislava.

{% include power-ranking-tier-heading.html tier=2 %}

{% include power-ranking-team-heading.html rank=5 %}

Last Week: 6 | Up 1

Inter produced perhaps the best win of the European weekend.

It also required an absurd comeback.

Napoli scored twice in the opening eight minutes of the second half and looked headed toward a major road victory. Instead, Lautaro Martínez pulled one back three minutes later, Marcus Thuram equalized in the 82nd and Lautaro scored again in stoppage time to complete the 3-2 win.

Inter finished with 29 shots and hit the woodwork twice, so this was not simply a lucky late escape.

The impressive part was the response.

Going down 2-0 against a team like Napoli can force a team into desperate crosses and rushed attacks. Inter kept creating enough pressure to gradually distort Napoli's defensive shape, then Cristian Chivu used his substitutions aggressively rather than settling for the draw once they reached 2-2.

Inter is now 3-0-0 in Serie A.

A trip to Real Madrid for the Champions League opener should tell us considerably more.

{% include power-ranking-team-heading.html rank=6 %}

Last Week: 7 | Up 1

Manchester City is 3-0-0 under Enzo Maresca.

That sentence makes the transition from Pep Guardiola sound considerably smoother than the actual performances have been.

City followed its 4-1 win at Crystal Palace with a 1-0 home victory over Coventry. Erling Haaland scored the only goal, but Gianluigi Donnarumma was required to make several important saves to preserve the lead.

City has enough talent to win while Maresca experiments.

That was part of the reason for keeping them high after the awkward opening victory over Bournemouth. Rayan Cherki can change a match. Haaland can score from very little. Donnarumma can erase a defensive mistake.

The collective structure still looks less automatic than it did under Guardiola.

That is understandable.

The question is how quickly it becomes automatic enough to survive against Champions League opponents that can punish those uncertain possession phases.

{% include power-ranking-team-heading.html rank=7 %}

Last Week: 5 | Down 2

This is probably a harsher drop than Real Madrid's actual performance deserves.

Betis beat Madrid 1-0 on Friday, but the match was not an example of José Mourinho's new team suddenly falling apart.

Madrid created the better chances, struck the woodwork three times and even received a stoppage-time penalty that Kylian Mbappé failed to convert. Troy Parrott's 81st-minute goal was enough for Betis to escape with all three points.

Sometimes you play reasonably well and lose.

That context prevents Madrid from falling farther.

The concern is that the result exposed one of the questions that has followed the rebuild. Madrid is terrifying when Mbappé, Vinícius and Bellingham can attack open space. Against an opponent willing to defend deeper and survive pressure, the attack can still become dependent on one of the stars producing the final action.

The first three games suggested Mourinho had already solved more of that issue than expected.

Betis provided the first real counterexample.

{% include power-ranking-tier-heading.html tier=3 %}

{% include power-ranking-team-heading.html rank=8 %}

Last Week: 8

Chelsea loses its first game and stays in the same place.

The 2-1 defeat at Arsenal was actually more encouraging than dropping Chelsea several spots would suggest.

Morgan Rogers gave Chelsea the early lead. They threatened Arsenal on the counter, hit the post through Pedro Neto and forced David Raya into an excellent late save from Estêvão.

The difference was that Arsenal controlled more of the middle portion of the match and punished Chelsea when the visitors left space around the box.

Xabi Alonso's team remains dangerous.

The concern from the first two weeks also remains.

Chelsea can score against almost anyone. It has not yet shown the same ability to control matches defensively once the opponent begins attacking the spaces behind its aggressive structure.

Losing narrowly at Arsenal does not change the overall evaluation.

{% include power-ranking-team-heading.html rank=9 %}

Last Week: 9

Manchester United had three points in its hands at Everton.

Then it gave them away.

Bryan Mbeumo put United ahead early in the second half. Everton equalized late, Benjamin Šeško restored the lead in the 88th minute and Ainsley Maitland-Niles scored from distance in the 96th to make it 2-2.

The attack looks considerably healthier than it did in the opening loss at Hull.

The defense does not.

United has now allowed at least two goals in each of its first three Premier League games. That is especially frustrating because the latest pair came after Michael Carrick's team had twice reached a winning position.

The top-end attacking talent keeps United in the top ten.

They need to start closing games.

{% include power-ranking-team-heading.html rank=10 %}

Last Week: 10

This ranking is hanging on by a thread.

Atlético went to San Mamés and lost 3-0 to Athletic Club, conceding twice in the opening three minutes of the second half before Oihan Sancet added the third late.

That was easily Atlético's worst performance of the young season.

The more concerning issue is how little resistance there was once Athletic seized control. Diego Simeone has more tactical flexibility and more technical quality in midfield than he did last year, but the new pieces have not yet produced a team capable of consistently controlling difficult road matches.

They stay tenth mostly because the teams directly below them have their own questions.

Liverpool is still settling under Andoni Iraola. Roma has only three games of evidence. Napoli has now lost twice.

Atlético gets one more week of benefit of the doubt.

Liverpool at Anfield on Wednesday is a fairly brutal place to try to justify it.

{% include power-ranking-team-heading.html rank=11 %}

Last Week: 11

Liverpool finally has its first league win under Iraola.

Alexander Isak scored twice inside the opening ten minutes at Ipswich, both created by Cody Gakpo, and Liverpool controlled the remainder of the match for a 2-0 victory.

It was not the most difficult opponent.

It was still important.

The first two Liverpool games showed a team capable of creating danger but also extremely vulnerable when its aggressive positioning broke down. Against Ipswich, Liverpool did a much better job playing the match from ahead instead of turning it into another transition contest.

Isak scoring twice is also encouraging for obvious reasons.

The attack never lacked theoretical talent. Getting the expensive pieces functioning together was the issue.

{% include power-ranking-team-heading.html rank=12 %}

Last Week: 15 | Up 3

Roma is making it increasingly difficult to treat the first two weeks as a fun little early-season run.

They are 3-0-0.

They have scored ten goals and conceded one.

The latest win was completely different from the two 4-0 blowouts that preceded it.

Atalanta led until the 90th minute at the Olimpico. Mario Hermoso equalized, Roma kept pushing rather than accepting the point and Matías Soulé scored in the 93rd minute to win 2-1.

That tells us something useful.

The first two matches showed what Gian Piero Gasperini's attacking structure can look like when Roma gets space and the forwards start interchanging.

Atalanta showed whether Roma could solve a game when that initial advantage disappeared.

So far, the answer is yes.

The next question is whether this travels to Europe.

{% include power-ranking-team-heading.html rank=13 %}

Last Week: 12 | Down 1

Napoli was eight minutes into the second half at Inter and leading 2-0.

It lost.

That alone would be frustrating.

Combined with the previous loss to Como, it creates a more significant concern.

Napoli's attack looked much better at San Siro, with Matteo Politano and Rasmus Højlund giving them a deserved advantage. The problem came once Inter increased the pressure and Napoli could no longer control where the match was being played.

The absence of Scott McTominay did not help and he will also miss the Champions League opener against Arsenal following a planned heart procedure.

Napoli still has enough quality to remain around this level.

Two consecutive losses keep them from going any higher.

{% include power-ranking-team-heading.html rank=14 %}

Last Week: 13 | Down 1

Dortmund drops despite winning.

That is mostly Roma's fault.

Dortmund fell 2-0 behind at Hoffenheim before Serhou Guirassy sparked a comeback with a goal and assist. Fábio Silva equalized five minutes later and Dortmund eventually won 3-2 through an own goal in the 86th minute.

There are two ways to interpret the performance.

Coming back from two goals down on the road shows attacking depth and resilience.

Going two goals down to Hoffenheim is not especially encouraging.

Both can be true.

Dortmund remains dangerous enough to beat good teams, but it has not yet shown the week-to-week control of the teams above it.

{% include power-ranking-team-heading.html rank=15 %}

Last Week: 14 | Down 1

Brighton opened the season by destroying Aston Villa 4-0.

Since then it has taken one point from two games.

The 1-1 draw against Leeds was less alarming than the 4-3 loss at Chelsea, but Leeds probably had the stronger case for winning. Brighton needed a Luka Vušković goal to salvage the point.

The early impression has not really changed.

Brighton is going to be aggressive, technically sharp and difficult to defend.

The question is whether it can consistently control what happens after possession changes.

The ceiling remains high enough to keep them in the middle of the rankings.

{% include power-ranking-team-heading.html rank=16 %}

Last Week: 16

Juventus remains unbeaten, although perfection is gone.

AC Milan took the lead in Turin through 19-year-old Alphadjo Cissé before Federico Gatti rescued a 1-1 draw with a late header.

Luciano Spalletti was relatively pleased with the performance and less pleased with the finishing.

That seems fair.

Juventus created enough opportunities to win, pressed aggressively and generally played the match on its preferred terms. It simply lacked the final action until Gatti eventually arrived.

Seven points through three matches is a solid start.

Roma and Inter currently look more convincing.

{% include power-ranking-team-heading.html rank=17 %}

Last Week: 17

Brentford remains unbeaten.

It also keeps leaving opportunities behind.

After drawing Leeds last week, Brentford took the lead against Sunderland through Vitaly Janelt and appeared headed toward another win before conceding a late penalty for the 1-1 draw.

The underlying impression is still positive.

Brentford is organized, the midfield understands when to press forward and the team rarely gives opponents easy attacking sequences.

They just have not been as ruthless as they were in the 3-0 opening win against Tottenham.

No reason to drop them yet.

{% include power-ranking-team-heading.html rank=18 %}

Last Week: 18

Bournemouth might be the best winless team in Europe.

That is not exactly an award they want.

For the third straight league game, Bournemouth took the lead.

For the third straight league game, Bournemouth failed to win.

They went 2-0 ahead at Newcastle before Harvey Barnes pulled one back and substitute Jacob Ramsey equalized in the 88th minute.

The pattern is getting difficult to ignore.

Bournemouth has now conceded twice late against Manchester City, allowed Everton to equalize in stoppage time and blown a two-goal advantage at Newcastle.

Marco Rose's initial plans have repeatedly worked.

Managing the second half has not.

{% include power-ranking-tier-heading.html tier=4 %}

{% include power-ranking-team-heading.html rank=19 %}

Last Week: 19

PSV produced a result worthy of moving higher.

The problem is finding someone to move below them.

PSV went to Ajax and won 3-1, its first victory in Amsterdam since 2022. Ricardo Pepi scored after five minutes, Lutsharel Geertruida restored the lead before halftime and Esmir Bajraktarević finished the game late.

Peter Bosz was particularly pleased with the second half, when PSV stopped allowing the match to become a transition contest and controlled it more effectively.

That is exactly the type of performance I want to see before moving an Eredivisie team higher.

Domestic dominance is one thing.

Winning a difficult road game against your primary rival is stronger evidence.

A good Champions League start against Shakhtar could push PSV upward next week.

{% include power-ranking-team-heading.html rank=20 %}

Last Week: 20

Aston Villa still has not scored a Premier League goal.

It stays ranked anyway.

Villa followed losses to Brighton and Arsenal with a 0-0 draw against newly promoted Hull, producing only one meaningful shot on target. Hull has started impressively and still has not conceded, so this is not quite as humiliating as it sounds.

Still, three league games without a goal is a serious problem.

The roster lost attacking quality during the summer and Unai Emery has not yet found a replacement structure that creates enough around the penalty area.

Villa survives because there is still enough talent and coaching history to believe the current version is temporary.

That patience is running out.

## Just Missed

### Como

If there were a No. 21, it would probably be Como.

Cesc Fàbregas's team followed its win over Napoli by going to Genoa and winning 4-1. Nico Paz, Martin Baturina and Assane Diao were all involved as Como turned a 1-0 deficit into a rout.

They are no longer a novelty.

Another result like this and they are coming in.

### Bayer Leverkusen

Leverkusen responded exactly how a talented team should respond after an embarrassing loss.

One week after losing to newly promoted Elversberg, Bayer beat Union Berlin 4-0 and scored after only one minute. Miguel Gutiérrez created the first two goals, while Patrik Schick and Ibrahim Maza finished the rout after halftime.

That goes a long way toward repairing the opener.

They need another week before returning.

### Sporting CP

Sporting has quietly won four straight after beating Nacional 2-0.

The score actually undersold the performance, with Sporting controlling the match from the beginning against an opponent mostly interested in defending and countering.

The Champions League will provide a much more useful measuring stick.

### Newcastle United

Newcastle remains unbeaten through three Premier League games but needed a late comeback to rescue the latest point against Bournemouth.

There is plenty to like about the early work under Matthias Jaissle.

There is not yet enough to crack the 20.

### AC Milan

Milan is also unbeaten and has seven points through three matches after coming within minutes of winning at Juventus.

Cissé's emergence gives Rúben Amorim another dangerous attacking option, while Milan has looked considerably more stable than it did for stretches last season.

They are close.

## The Rankings

Just Missed: Como, Bayer Leverkusen, Sporting CP, Newcastle United, AC Milan

The domestic results have given us a reasonable opening picture.

The Champions League is where we start finding out how much of it is real.

Barcelona has earned the top spot by flattening nearly everything in front of it. Arsenal looks more complete than the other Premier League contenders. Inter and Roma have made strong early cases in Italy. PSG's European résumé still demands respect, but three winless league games can no longer be ignored.

Now they get to play each other.

Next week's rankings should be considerably more interesting.
