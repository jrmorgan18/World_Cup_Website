# Dual Eights NFL Rankings Research Brief — Complete Week 5

Prepared October 13, 2026. Research notes for an article, not a finished article.

## Coverage and comparison rules

- All **15 of 15 Week 5 games** are final and included. The current-season sample is **79 games** through Monday, October 12. Kansas City and Carolina had Week 5 byes; Week 6 plays are excluded from ratings.
- Efficiency is the published **v2.1** formula. DEPI uses the existing frozen production coefficients. Neither formula was changed for this refresh.
- All movement below compares **the complete Week 5 cutoff with the Week 4 cutoff**, recomputed from the same current source revision. It is not movement from Monday's partial Week 5 board. This avoids treating the final Monday game as an entire week's movement.
- Historical DEPI comparisons are a same-model replay with archived prior-week QB/depth-chart context, not a claim that these rankings were publicly issued before Week 5. Current DEPI assumes the listed default quarterback; a depth-chart listing does not confirm game-day availability.
- Ranks use unrounded scores. Display rounding can hide small differences; a team can improve its score and still fall in rank if other teams improve more.

## Quick story angles

1. **The 49ers lead both boards.** San Francisco is first in Efficiency at 68.7 and first in DEPI at +9.86 points, after a 32–29 win in Seattle.
2. **Buffalo's Monday-night win changes the top of the forecast.** The Bills climb from fourth to second in DEPI and from 15th to 10th in Efficiency.
3. **Tampa Bay is the week's biggest Efficiency rank riser despite being 1–4.** The Buccaneers move 17th → ninth; their record is not a substitute for how they have played.
4. **New England makes the strongest combined leap.** The Patriots move 18th → 11th in Efficiency and 13th → eighth in DEPI after beating the Raiders 45–17.
5. **Minnesota is the useful disagreement case.** A 5–0 team ranks sixth in Efficiency but 18th in DEPI. Its defensive/special-teams dominance is real in the descriptive model; its offensive profile and historical context still constrain the forward-looking model.
6. **The Ravens' strength ranking needs a quarterback footnote.** Fourth in default DEPI means Lamar is assumed. Huntley changes the projection materially; see the dedicated note below.

## Brief DEPI introduction — usable draft copy

> The Dual Eights Efficiency Index asks how well a team has played this season. The Dual Eights Power Index, or DEPI, asks a different question: how strong should that team be going forward? DEPI combines opponent-adjusted passing and rushing efficiency, success rates, special teams, historical performance and the expected starting quarterback into a rating expressed in scoring-margin points above or below an average team on a neutral field.
>
> A +5 team is estimated to be five points better than average on neutral ground. Compare two teams' ratings and add the model's home-field allowance to estimate a matchup margin. The point scale makes DEPI useful alongside Efficiency, but it is still a beta estimate—not a win probability, a certainty or a betting guarantee.

### Background to support that introduction

- **Performance versus projected strength:** Efficiency uses this season's observed plays. DEPI adds prior-season team information, recency weighting and expected-QB adjustments; it is not another name for the same 0–100 index.
- **Inputs:** opponent/venue-adjusted passing and designed-rushing EPA and success rates; context-adjusted special teams; and pooled quarterback estimates. CPOE is considered in the feature framework but its frozen production margin coefficient is zero, so it is not a separate active contributor to the current DEPI score.
- **Historical weighting:** offense carries more prior information than defense (80% versus 40% before current evidence competes with the priors). Current-season plays decay with an eight-week half-life. Coach/primary-QB transitions reduce carryover. These are modeling assumptions, not subjective team-specific bonuses.
- **Stabilization:** the model reduces the influence of fortunate fumble recoveries and pools small quarterback samples toward historical role/draft cohorts rather than treating every early-season highlight as established talent.
- **Additive scale:** offense + defense + special teams + lineup adjustment = DEPI. The lineup term replaces the quarterback contribution already embedded in offense; it is not a standalone QB grade or a second full count of QB value.
- **Home field:** the fitted allowance is **1.57 points**. International/neutral-site games receive no home-field allowance.
- **Validation caveat:** frozen margin coefficients were fitted using seasons through 2023. Previously inspected 2024/2025 retrospective mean absolute errors were 10.02/10.14 points per game. Those are limitations to disclose, not evidence of guaranteed predictive superiority or a live betting record.
- **What is missing:** explicit weather/rest adjustments and non-QB injury/player-matchup effects. Default quarterbacks may be unavailable. Early-season priors and small QB samples remain important sources of uncertainty.

## Efficiency Index: full league standings

Positive movement means places gained. Index change is Week 5 minus Week 4 on the same v2.1 scale.

| W5 rank | Team | Record | Index | W4 rank | Rank move | Index change |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | San Francisco 49ers | 5-0 | 68.7 | 2 | ↑ 1 | +1.37 |
| 2 | Jacksonville Jaguars | 4-1 | 68.1 | 1 | ↓ 1 | −0.00 |
| 3 | Seattle Seahawks | 3-2 | 63.4 | 3 | — | −1.80 |
| 4 | Kansas City Chiefs | 4-0 | 62.6 | 4 | — | −1.49 |
| 5 | The Ravens | 4-1 | 62.5 | 6 | ↑ 1 | +2.07 |
| 6 | Minnesota Vikings | 5-0 | 61.6 | 7 | ↑ 1 | +3.02 |
| 7 | Cincinnati Bengals | 3-2 | 59.1 | 11 | ↑ 4 | +3.07 |
| 8 | Carolina Panthers | 2-2 | 56.8 | 8 | — | −1.10 |
| 9 | Tampa Bay Buccaneers | 1-4 | 56.7 | 17 | ↑ 8 | +5.94 |
| 10 | Buffalo Bills | 4-1 | 56.6 | 15 | ↑ 5 | +4.71 |
| 11 | New England Patriots | 3-2 | 55.9 | 18 | ↑ 7 | +6.86 |
| 12 | Chicago Bears | 3-2 | 55.5 | 5 | ↓ 7 | −7.56 |
| 13 | Atlanta Falcons | 2-3 | 55.2 | 9 | ↓ 4 | −1.93 |
| 14 | Detroit Lions | 3-2 | 54.1 | 19 | ↑ 5 | +5.35 |
| 15 | Denver Broncos | 3-2 | 53.2 | 12 | ↓ 3 | +0.12 |
| 16 | Houston Texans | 1-4 | 52.1 | 21 | ↑ 5 | +5.60 |
| 17 | Los Angeles Rams | 2-3 | 51.8 | 10 | ↓ 7 | −4.35 |
| 18 | Indianapolis Colts | 2-3 | 49.8 | 14 | ↓ 4 | −2.42 |
| 19 | New York Jets | 2-3 | 49.1 | 23 | ↑ 4 | +6.68 |
| 20 | New York Giants | 3-1-1 | 46.7 | 13 | ↓ 7 | −5.67 |
| 21 | Arizona Cardinals | 1-4 | 44.8 | 16 | ↓ 5 | −6.35 |
| 22 | Pittsburgh Steelers | 3-2 | 44.5 | 26 | ↑ 4 | +4.47 |
| 23 | Green Bay Packers | 3-2 | 43.9 | 29 | ↑ 6 | +5.41 |
| 24 | Cleveland Browns | 3-2 | 42.1 | 22 | ↓ 2 | −4.01 |
| 25 | Philadelphia Eagles | 2-3 | 41.6 | 24 | ↓ 1 | +0.39 |
| 26 | Washington Commanders | 1-3-1 | 39.7 | 28 | ↑ 2 | +0.19 |
| 27 | Las Vegas Raiders | 3-2 | 38.6 | 20 | ↓ 7 | −8.60 |
| 28 | Dallas Cowboys | 2-3 | 37.5 | 25 | ↓ 3 | −3.28 |
| 29 | New Orleans Saints | 1-4 | 36.2 | 27 | ↓ 2 | −3.43 |
| 30 | Los Angeles Chargers | 0-5 | 35.8 | 30 | — | +0.10 |
| 31 | Tennessee Titans | 0-5 | 27.1 | 31 | — | −2.84 |
| 32 | Miami Dolphins | 0-5 | 26.1 | 32 | — | −2.05 |

### The top 10: unit profiles

These are **adjusted unit ranks from the Efficiency model**, not raw EPA/play ranks or DEPI contribution ranks.

| Team | Index rank | Adjusted offense | Adjusted defense | Special teams |
| --- | --- | --- | --- | --- |
| San Francisco 49ers | 1 | 1 | 12 | 20 |
| Jacksonville Jaguars | 2 | 4 | 4 | 19 |
| Seattle Seahawks | 3 | 26 | 2 | 2 |
| Kansas City Chiefs | 4 | 5 | 13 | 10 |
| The Ravens | 5 | 6 | 10 | 14 |
| Minnesota Vikings | 6 | 32 | 1 | 1 |
| Cincinnati Bengals | 7 | 8 | 14 | 13 |
| Carolina Panthers | 8 | 12 | 15 | 11 |
| Tampa Bay Buccaneers | 9 | 21 | 7 | 6 |
| Buffalo Bills | 10 | 2 | 29 | 4 |

### 1. San Francisco 49ers — 68.7 (5-0)

The 32–29 win at Seattle moves the 49ers ahead of Jacksonville. The adjusted offense ranks first; the defense is 12th and special teams 20th. Their lead comes principally from offensive efficiency, not across-the-board dominance.

### 2. Jacksonville Jaguars — 68.1 (4-1)

A 19–17 win over Philadelphia keeps the Jaguars very close to first: only 0.54 index points behind San Francisco. Fourth in both adjusted offense and defense gives them the most balanced top-two profile. Their 68.1 display score barely changes even as they fall one place.

### 3. Seattle Seahawks — 63.4 (3-2)

The Seahawks remain third despite losing to San Francisco. Their second-ranked adjusted defense and second-ranked special teams outweigh the 26th-ranked adjusted offense. A loss does not automatically force a large slide in an efficiency ranking.

### 4. Kansas City Chiefs — 62.6 (4-0)

Kansas City stays fourth during its bye. Its index falls from 64.1 to 62.6 because opponents' new results change the joint opponent-adjusted fit. That is a contextual rating change, not a nonexistent Chiefs game.

### 5. The Ravens — 62.5 (4-1)

The Ravens climb from sixth to fifth after the 30–23 overtime win in Atlanta. Adjusted offense ranks sixth, defense 10th and special teams 14th. The descriptive index includes Huntley's actual Week 5 performance; it does not substitute hypothetical Lamar snaps.

### 6. Minnesota Vikings — 61.6 (5-0)

The unbeaten Vikings move from seventh to sixth after beating New Orleans 23–13. This is the most distinctive top-10 profile: first in adjusted defense and special teams, but 32nd in adjusted offense. Do not describe their offense as efficient just because they are 5–0.

### 7. Cincinnati Bengals — 59.1 (3-2)

Cincinnati rises four spots after a 31–24 win at Miami. Eighth-ranked adjusted offense leads a more middle-of-the-pack defense (14th) and special-teams unit (13th). The Bengals are sixth in DEPI as well, so the two measures agree relatively closely.

### 8. Carolina Panthers — 56.8 (2-2)

Carolina remains eighth through its bye. Its score falls from 58.0 to 56.8 as the opponent-adjusted league fit changes, but its relative rank holds. The Panthers have played four games, so their record and sample differ from most of the league.

### 9. Tampa Bay Buccaneers — 56.7 (1-4)

Tampa Bay jumps eight places after a 24–16 win at Dallas. At 1–4, the Buccaneers rank ninth in Efficiency and 12th in DEPI: the clearest example this week of why performance ratings and the standings are different things. Adjusted defense is seventh and special teams sixth.

### 10. Buffalo Bills — 56.6 (4-1)

Monday night's 37–34 win at the Rams completes the week and pushes Buffalo from 15th to 10th. The Bills have the second-ranked adjusted offense and fourth-ranked special teams, but the defense is 29th. They are second in DEPI, a more optimistic forecast than their current-season Efficiency rank.

## Efficiency: biggest risers

| Team | W4 → W5 rank | Places gained | Index W4 → W5 | Week 5 result |
| --- | --- | --- | --- | --- |
| Tampa Bay Buccaneers | 17 → 9 | +8 | 50.8 → 56.7 | W 24–16 at DAL |
| New England Patriots | 18 → 11 | +7 | 49.0 → 55.9 | W 45–17 vs. LV |
| Green Bay Packers | 29 → 23 | +6 | 38.5 → 43.9 | W 31–7 vs. CHI |
| Buffalo Bills | 15 → 10 | +5 | 51.9 → 56.6 | W 37–34 at LA |
| Detroit Lions | 19 → 14 | +5 | 48.7 → 54.1 | W 45–21 at ARI |
| Houston Texans | 21 → 16 | +5 | 46.5 → 52.1 | W 26–3 at TEN |

Include Buffalo, Detroit and Houston if listing the five-place tier: all three gained five places. By **index points**, New England (+6.86) and the Jets (+6.68) are the two biggest risers; the Jets gain four rank places, so a rank-only list understates their score improvement.

## Efficiency: biggest fallers

| Team | W4 → W5 rank | Places lost | Index W4 → W5 | Week 5 result |
| --- | --- | --- | --- | --- |
| Chicago Bears | 5 → 12 | 7 | 63.0 → 55.5 | L 7–31 at GB |
| Los Angeles Rams | 10 → 17 | 7 | 56.1 → 51.8 | L 34–37 vs. BUF |
| New York Giants | 13 → 20 | 7 | 52.4 → 46.7 | T 27–27 at WAS |
| Las Vegas Raiders | 20 → 27 | 7 | 47.2 → 38.6 | L 17–45 at NE |
| Arizona Cardinals | 16 → 21 | 5 | 51.1 → 44.8 | L 21–45 vs. DET |
| Atlanta Falcons | 9 → 13 | 4 | 57.1 → 55.2 | L 23–30 vs. BAL |
| Indianapolis Colts | 14 → 18 | 4 | 52.2 → 49.8 | L 22–34 at PIT |

Chicago, the Rams, the Raiders and the Giants all lose seven places. The Raiders have the largest index-point decline. The Giants' 27–27 tie is worth highlighting: a non-loss can still worsen their efficiency profile and rank. The Rams' 37–34 loss and Chicago's 31–7 loss produce the same rank drop, but that does not mean identical game performance.

## DEPI: full league standings

DEPI points are relative to an average team on a neutral field. The QB column is a modeling assumption, not an availability report.

| W5 rank | Team | Record | DEPI pts | W4 rank | Rank move | Point change | Assumed QB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | San Francisco 49ers | 5-0 | +9.86 | 1 | — | +0.51 | Brock Purdy |
| 2 | Buffalo Bills | 4-1 | +7.22 | 4 | ↑ 2 | +1.68 | Josh Allen |
| 3 | Jacksonville Jaguars | 4-1 | +6.15 | 2 | ↓ 1 | −0.47 | Trevor Lawrence |
| 4 | The Ravens | 4-1 | +5.72 | 6 | ↑ 2 | +0.66 | Lamar Jackson |
| 5 | Los Angeles Rams | 2-3 | +4.97 | 3 | ↓ 2 | −1.20 | Matthew Stafford |
| 6 | Cincinnati Bengals | 3-2 | +4.31 | 8 | ↑ 2 | +0.74 | Joe Burrow |
| 7 | Chicago Bears | 3-2 | +3.32 | 5 | ↓ 2 | −2.02 | Caleb Williams |
| 8 | New England Patriots | 3-2 | +3.01 | 13 | ↑ 5 | +2.26 | Drake Maye |
| 9 | Kansas City Chiefs | 4-0 | +2.71 | 9 | — | −0.51 | Patrick Mahomes |
| 10 | Seattle Seahawks | 3-2 | +2.69 | 7 | ↓ 3 | −1.46 | Sam Darnold |
| 11 | Detroit Lions | 3-2 | +2.40 | 12 | ↑ 1 | +1.62 | Jared Goff |
| 12 | Tampa Bay Buccaneers | 1-4 | +1.31 | 17 | ↑ 5 | +1.91 | Baker Mayfield |
| 13 | Atlanta Falcons | 2-3 | +0.75 | 10 | ↓ 3 | −1.52 | Michael Penix Jr. |
| 14 | Green Bay Packers | 3-2 | +0.64 | 18 | ↑ 4 | +1.98 | Jordan Love |
| 15 | Denver Broncos | 3-2 | +0.06 | 14 | ↓ 1 | −0.36 | Bo Nix |
| 16 | Carolina Panthers | 2-2 | +0.02 | 15 | ↓ 1 | −0.21 | Bryce Young |
| 17 | Indianapolis Colts | 2-3 | −0.10 | 11 | ↓ 6 | −1.13 | Daniel Jones |
| 18 | Minnesota Vikings | 5-0 | −0.31 | 20 | ↑ 2 | +1.45 | Kyler Murray |
| 19 | Pittsburgh Steelers | 3-2 | −1.11 | 23 | ↑ 4 | +1.21 | Aaron Rodgers |
| 20 | Dallas Cowboys | 2-3 | −1.32 | 16 | ↓ 4 | −1.09 | Dak Prescott |
| 21 | Houston Texans | 1-4 | −1.44 | 25 | ↑ 4 | +1.66 | C.J. Stroud |
| 22 | Washington Commanders | 1-3-1 | −1.83 | 21 | ↓ 1 | +0.30 | Jayden Daniels |
| 23 | New York Jets | 2-3 | −2.09 | 27 | ↑ 4 | +1.35 | Geno Smith |
| 24 | Philadelphia Eagles | 2-3 | −2.85 | 24 | — | −0.21 | Jalen Hurts |
| 25 | Arizona Cardinals | 1-4 | −3.35 | 19 | ↓ 6 | −1.64 | Jacoby Brissett |
| 26 | Las Vegas Raiders | 3-2 | −4.33 | 22 | ↓ 4 | −2.01 | Kirk Cousins |
| 27 | New York Giants | 3-1-1 | −4.62 | 28 | ↑ 1 | −0.38 | Jameis Winston |
| 28 | Los Angeles Chargers | 0-5 | −4.69 | 29 | ↑ 1 | −0.21 | Justin Herbert |
| 29 | Cleveland Browns | 3-2 | −5.02 | 26 | ↓ 3 | −1.89 | Deshaun Watson |
| 30 | New Orleans Saints | 1-4 | −5.52 | 30 | — | −0.14 | Tyler Shough |
| 31 | Miami Dolphins | 0-5 | −7.41 | 31 | — | −0.32 | Malik Willis |
| 32 | Tennessee Titans | 0-5 | −9.15 | 32 | — | −0.51 | Cam Ward |

### DEPI top 10: where the rating comes from

Positive defense points indicate better defense. Figures are rounded independently, so displayed contributions can differ from the displayed total by 0.01–0.02.

| Team | DEPI | Offense | Defense | ST | QB lineup adj. |
| --- | --- | --- | --- | --- | --- |
| San Francisco 49ers | +9.86 | +8.06 | +1.18 | +0.05 | +0.57 |
| Buffalo Bills | +7.22 | +8.05 | −2.26 | +0.91 | +0.53 |
| Jacksonville Jaguars | +6.15 | +2.83 | +3.36 | −0.02 | −0.02 |
| The Ravens | +5.72 | +3.51 | +0.46 | +0.17 | +1.57 |
| Los Angeles Rams | +4.97 | +5.04 | +1.92 | −1.88 | −0.10 |
| Cincinnati Bengals | +4.31 | +3.48 | −0.24 | +0.34 | +0.72 |
| Chicago Bears | +3.32 | +3.36 | −1.07 | +0.39 | +0.65 |
| New England Patriots | +3.01 | +3.17 | +0.37 | −0.60 | +0.07 |
| Kansas City Chiefs | +2.71 | +1.60 | +0.37 | +0.25 | +0.48 |
| Seattle Seahawks | +2.69 | −2.43 | +3.83 | +1.37 | −0.07 |

## DEPI: biggest risers

| Team | W4 → W5 rank | Places gained | DEPI W4 → W5 | Point change |
| --- | --- | --- | --- | --- |
| New England Patriots | 13 → 8 | +5 | +0.75 → +3.01 | +2.26 |
| Tampa Bay Buccaneers | 17 → 12 | +5 | −0.60 → +1.31 | +1.91 |
| Green Bay Packers | 18 → 14 | +4 | −1.33 → +0.64 | +1.98 |
| Pittsburgh Steelers | 23 → 19 | +4 | −2.32 → −1.11 | +1.21 |
| Houston Texans | 25 → 21 | +4 | −3.10 → −1.44 | +1.66 |
| New York Jets | 27 → 23 | +4 | −3.43 → −2.09 | +1.35 |

### Main drivers — model contribution changes, not box-score attribution

- **New England:** +2.26 DEPI points overall, led by +1.64 offense, +0.21 defense and +0.35 special teams. The 45–17 win at home against the Raiders makes this the largest DEPI point gain as well as a five-place climb.
- **Tampa Bay:** +1.91 overall; offense adds +1.35 and defense +0.51. Its move from slightly below average to +1.31 is meaningful even though the record remains 1–4.
- **Green Bay:** +1.98 overall, with +1.13 offense and +1.08 defense after beating Chicago 31–7; special teams decline by 0.35. The Packers rise four places to 14th.
- **Houston:** +1.66 overall, split between offense (+0.71) and defense (+0.73), after the 26–3 win at Tennessee. Houston's 1–4 record and 21st-place DEPI still limit any sweeping turnaround claim.
- **Pittsburgh:** +1.21 overall, principally offense (+0.94) and special teams (+0.41), after beating Indianapolis 34–22; its defensive contribution slips by 0.20.
- **Jets:** +1.35 overall, largely defense (+0.85) and special teams (+0.54), after the 17–12 win over Cleveland. The offensive contribution is essentially unchanged.
- **Buffalo:** a two-place climb to second is less dramatic by rank than those six movers, but its +1.68-point gain is among the week's largest. Nearly all of that gain is in offense (+1.49).

Because these are jointly adjusted, league-centered fits, contribution changes also reflect new opponent context, recency/history weighting and QB estimates. They are not a causal allocation of one game's scoring margin.

## DEPI: biggest fallers

| Team | W4 → W5 rank | Places lost | DEPI W4 → W5 | Point change |
| --- | --- | --- | --- | --- |
| Indianapolis Colts | 11 → 17 | 6 | +1.04 → −0.10 | −1.13 |
| Arizona Cardinals | 19 → 25 | 6 | −1.71 → −3.35 | −1.64 |
| Dallas Cowboys | 16 → 20 | 4 | −0.24 → −1.32 | −1.09 |
| Las Vegas Raiders | 22 → 26 | 4 | −2.32 → −4.33 | −2.01 |
| Seattle Seahawks | 7 → 10 | 3 | +4.16 → +2.69 | −1.46 |
| Atlanta Falcons | 10 → 13 | 3 | +2.27 → +0.75 | −1.52 |
| Cleveland Browns | 26 → 29 | 3 | −3.13 → −5.02 | −1.89 |

- **Indianapolis:** falls six places, 11th → 17th, despite only a 1.13-point decline. Its defensive contribution falls 0.95; the crowded middle amplifies the rank change.
- **Arizona:** also loses six places, 19th → 25th. The 45–21 loss to Detroit coincides with −1.64 DEPI points, including −0.94 defense and −0.40 special teams.
- **Dallas:** 16th → 20th, −1.09 points; offense (−0.48) and defense (−0.57) both deteriorate after the loss to Tampa Bay.
- **Rams:** remain fifth in DEPI even while slipping two places. Their −1.20-point change is largely defense (−1.19), reinforcing the difference between a strong offensive forecast and their 17th-place current Efficiency profile.
- **Seattle:** seventh → 10th, −1.46 points. The offensive contribution declines 2.26, partly offset by defense (+0.52) and special teams (+0.48).
- **Raiders:** 22nd → 26th, a four-place fall. Their −2.01 points are driven chiefly by defense (−1.63), then special teams (−0.37). Use the actual table baseline when writing.
- **Cleveland:** 26th → 29th, −1.89 points, primarily offense (−1.75). The 17–12 loss to the Jets sets up the next Ravens matchup.
- **Chicago deserves a separate point-change mention:** fifth → seventh is only two places, but −2.02 points is the largest DEPI decline. Defense (−1.04), offense (−0.78) and special teams (−0.43) all fall.

## Where Efficiency and DEPI disagree

| Team | Efficiency rank | DEPI rank | Useful interpretation |
| --- | --- | --- | --- |
| Minnesota Vikings | 6 | 18 | Defense/ST lead observed performance; DEPI offense is −5.28 points despite 5–0. |
| Los Angeles Rams | 17 | 5 | Historical/forward-looking strength stays high; current season performance has slipped. |
| Buffalo Bills | 10 | 2 | Strong offensive projection; current adjusted defense is only 29th. |
| Seattle Seahawks | 3 | 10 | Observed defense/ST are excellent; DEPI is less bullish on total strength. |
| Green Bay Packers | 23 | 14 | Recent improvement and historical/QB context exceed the season-to-date Efficiency rank. |
| Carolina Panthers | 8 | 16 | Solid four-game Efficiency profile; DEPI is approximately average. |

Do not force one ranking to validate the other. The gap is often the article's most useful question: are this season's results showing a durable change, or does the forecast still have reasons to be skeptical?

## The Ravens: the quarterback footnote you should include

- **Efficiency:** fifth at **62.5**, up one place from Week 4's 60.5.
- **Default DEPI:** fourth at **+5.72**, up two places and +0.66 points. It assumes **Lamar Jackson**.
- **Huntley scenario:** before league re-centering, replacing Jackson with Huntley lowers the rating by **4.02 points**, to **+1.69**, ranking **11th** if other QB assumptions remain unchanged. Applying the scenario to the rankings UI re-centers all 32 teams around zero, so its displayed Ravens rating is **+1.82**; relative rankings and matchup margins are unaffected by that common shift.
- This does not erase the Atlanta win or replace Huntley's actual plays in Efficiency. It changes the expected future quarterback contribution in DEPI.
- For Week 6 at Cleveland, the current model margin is **Ravens by 9.17 with Lamar** or approximately **Ravens by 5.14 with Huntley**, keeping Cleveland's default Deshaun Watson assumption. These are conditional model margins, not picks or confirmed lineups.
- Missing Week 6 injury designations do not establish that Jackson, or any other default QB, will play.

## Optional Week 6 matchup angle

**Seattle at Denver, Thursday, October 15:** Seattle ranks third in Efficiency and 10th in DEPI; Denver ranks 15th in both. The default model is tight at Seattle by 1.07 after Denver's home-field allowance. It offers an early test of Seattle's defense/ST-led profile rather than a top-two DEPI showdown.

For a balanced matchup, **Chicago at Atlanta** has the highest combined default DEPI (+4.08) among pairings with a model margin within three points, and the forecast is close (Chicago by 1.00). **Washington at San Francisco** actually has the highest combined DEPI overall (+8.03), but San Francisco is favored by 13.25 model points. **Houston at Jacksonville** has the highest combined Efficiency score (120.22), but Jacksonville is a much clearer default-model favorite. If selecting a 'best matchup,' specify whether that means combined team quality, balance or analytical interest; no Week 6 fixture pairs two top-10 DEPI teams.

## Selected Power Index branding

Use **Dual Eights Power Index (DEPI)** on first mention and **DEPI** thereafter. This is a name-only rebrand of the existing model: the formula, point scale, rankings, quarterback scenarios and historical forecasts are unchanged. Keep **Dual Eights Efficiency Index** for the separate descriptive performance measure.

## Sources, reproducibility and writing guardrails

- [Live NFL rankings](https://dualeights.com/nfl/rankings/) and [model methodology](https://dualeights.com/nfl/methodology/). The current downloadable [rankings CSV](https://dualeights.com/assets/data/nfl-rankings.csv) supplies the underlying standings.
- [nflverse 2026 play-by-play](https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_2026.parquet), [schedule/results](https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv), and [2026 depth charts](https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_2026.parquet). These public feeds supply the results and model inputs, not third-party power rankings.
- [Published Efficiency v2.1 explanation](https://dualeights.com/ravens/dual-eights-efficiency-index-week-four-2026/). Its formula is unchanged: 45% offense, 45% defense and 10% special teams, standardized against the frozen 2025 calibration and displayed as `50 + 50 × tanh(composite / 2)`.
- [nflverse availability/correction policy](https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html): Wednesday/Thursday statistical corrections can revise the descriptive ratings. This is a dated October 13 snapshot, not a permanent unchangeable Week 5 score.
- Production refresh commands: `python scripts/update_nfl_dashboard.py --season 2026 --ratings-week 5` and `python scripts/update_ravens_dashboard.py --season 2026 --as-of 2026-10-13`. Shared-current-PBP cutoff comparisons use the same fixed coefficients and calibration, without refitting or importing Week 6 plays.
- Use **index points** for Efficiency and **scoring-margin points above/below average** for DEPI. Neither is a percentile or win probability.
- A positive rank move is old rank minus new rank; a positive rating-point change is new score minus old score.
- Avoid calling retrospective replays saved pregame predictions. Do not conflate adjusted unit ranks with raw EPA ranks, or QB assumptions with availability confirmation.

