---
layout: post
title: "How the Project 2030 Big Board Works"
subtitle: "A present-value ranking first, with a separate and deliberately limited look ahead to 2030."
excerpt: "What the Big Board measures, how Current and 2030 Scores differ, and why the rankings will keep changing."
date: 2026-08-09 09:00:00 -0400
categories: [project-2030, usmnt]
permalink: /soccer/project-2030/how-the-big-board-works/
author: "Randy Morgan"
read_time: 4
section_theme: project
big_board_explainer: true
---

The Project 2030 Big Board is not a prediction of the final 2030 roster, and it is not a list of the most talented American players in the abstract. Its starting question is simpler: **if the World Cup were tomorrow, how strong is each player right now?**

That answer is the Current Score. The board then offers a separate 2030 Score that adds a modest projection layer. Keeping those two ideas apart matters. A young player with real upside should not be ranked above a better current player just because his future is appealing. At the same time, the board should not pretend that a 20-year-old prospect and a 32-year-old veteran carry the same forward-looking value.

## The Current Score: what matters today

The Current Score is built from three pieces:

- **65% club performance.** This is the largest part of the board. It evaluates production and, where available, advanced attacking or defensive indicators, then accounts for position, playing time, the quality of the competition, club strength, and the reliability of the sample. A strong season in a stronger league should carry more weight than the same raw totals in an easier environment.

- **15% club role.** Minutes and starts are evidence. This piece asks whether a player is actually trusted by his club, rather than treating a handful of good appearances as a full season. It also helps distinguish a meaningful role at a high-level club from a peripheral one.

- **20% USMNT evidence.** International performance belongs in the ranking. World Cup selection and usage carry the most weight, followed by performance in those matches and a discounted record of minutes in recent major senior competitions. A player who helped the United States in meaningful games should receive credit for it.

The goal is not to create a fake sense of precision. A 61.2 is not inherently a different caliber of player than a 60.8. The score is a transparent way to combine the evidence and make the order of the board easier to interrogate.

## Recent evidence with older context

Soccer seasons are noisy. Players get hurt, change clubs, lose a manager's trust, or run unusually hot or cold for a few months. To keep one difficult stretch from wiping out a player's established level, the model gives the most weight to the recent twelve-month club window and includes the preceding window at half weight. Some source observations cover a separately dated season rather than the entire rolling window; those remain identified with their actual period.

## What the 2030 Score adds

The 2030 Score starts with the Current Score, then applies three capped adjustments:

- **Age curve:** a position-aware adjustment for where a player will be in 2030. It rewards players who should be entering or remaining in their prime and discounts the positions and ages where decline is more likely.

- **Recent trajectory:** a small credit or debit for whether the most recent evidence is improving or slipping compared with the previous season.

- **Market-value signal:** a limited Transfermarkt-based signal that reflects how the broader market values a player's age and future runway. It is intentionally capped; market value can inform a projection, but it cannot overrule performance.

The projection adjustments are deliberately modest. A player does not become a star on the board solely because he is young, and an established player is not erased solely because he will be older in 2030.

## What the board does not do

The Big Board does not include a separate injury/readiness penalty. Verified injury absences can be removed from eligible club opportunities, so a documented absence is not automatically treated as a lost selection battle. That changes the availability denominator, not the player's recorded minutes or production. It also does not make a new transfer instantly change a score. The club and league label can update right away, but the score waits for actual evidence in the new environment; older performance remains tied to the club and competition where it happened.

The data is also not perfectly complete. Some players have deeper defensive or advanced data than others, especially outside the largest leagues. The model identifies those gaps in its internal audit and uses cautious fallbacks rather than inventing precision. Players without enough usable evidence remain on the pool but may appear without a score until the record is sufficient.

## A living board

### What changed in the October 9, 2026 update

The October release adds available club evidence through October 5 and senior international matches through October 6. Friendlies enter the international history at a quarter of the major-competition minute weight. Older or incomplete source observations remain in use where comparable new data is unavailable, so the release date does not mean every player's underlying statistics share that date.

For MLS players with fewer than 900 league minutes **or** at most five starts in the previous season, the new-season role sample begins at their first league start. Both played minutes and eligible opportunities use that same starting point. Cavan Sullivan has a separate May 1, 2026 cutoff for his club sample. These adjustments measure the role a player earned after breaking through rather than counting earlier weeks as opportunities he failed to take.

The update also checks position and availability, keeps reserve-team evidence separate from first-team league evidence, and avoids treating different position-specific baskets as a comparable form trend. Non-overlapping production samples are combined once per rating period before applying the existing volume cap and older-period decay. The 65% club-performance, 15% club-role and 20% international weights remain unchanged.

The point of publishing the methodology is accountability. Readers should be able to disagree with a ranking, understand the evidence behind it, and see what would need to change for a player to move. The board will update as club seasons develop, USMNT matches add new evidence, and better data becomes available.

That is the standard for Project 2030: make the judgment visible, keep the model flexible, and let the soccer change the rankings.
