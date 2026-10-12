# Dual Eights Efficiency Index v2.1

Version 2 implements opponent/venue adjustment, magnitude-preserving aggregation,
and game-state weighting with separate dropback and designed-run estimates.
Version 2.1 adds special teams with a 45% offense / 45% defense / 10% ST blend.
It describes observed team efficiency, not a win probability, betting model,
or roster-based forecast. A separate power ranking remains future work.

## Inputs and automation

The existing updater downloads the public nflverse schedule CSV and season PBP
Parquet releases, now additionally reading `qb_dropback`, `wp`, `qtr` and
`game_seconds_remaining`, plus `ep`, kick distance, half time, attempt flags,
kick results and block attribution. No additional provider, key or paid data is required.
EPA, success and the existing eligibility exclusions are unchanged. Raw dashboard
EPA, success, explosive rates and red-zone statistics remain unweighted.

Source dictionaries:
- https://nflreadr.nflverse.com/articles/dictionary_pbp.html
- https://nflreadr.nflverse.com/articles/dictionary_schedules.html
- https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html

The updater refuses to replace the last good JSON if a scheduled completed game
lacks eligible plays for either offense, or a retained play lacks a required
model field or valid venue/team mapping. This catches missing games, not every
possible truncated-game or upstream scoring error. Source corrections can revise
the current period on a subsequent update; archived weekly snapshots are retained.

## Model

1. Classify `qb_dropback == 1` as a dropback, including sacks and scrambles.
   Other eligible run/pass plays are designed runs.
2. Weight all plays 1, except fourth-quarter plays with 0–900 regulation seconds
   remaining. Let `p = min(wp, 1 - wp)` from the pre-snap, non-Vegas win probability:
   `weight = 0.25 + 0.75 * clip((p - 0.05) / 0.10, 0, 1)`.
   Thus competitive plays retain full weight; extreme states retain one quarter.
   Earlier quarters and overtime retain full weight. Comeback plays regain weight
   when the pre-snap state becomes competitive.
3. For each play type, fit two weighted linear ridge models, one for EPA and one
   for binary success:
   `outcome = intercept + offense[team] - defense[opponent] + venue_coefficient * venue`.
   Venue is +1 for the home offense, -1 away, and 0 at neutral sites. Team and
   venue coefficients receive a ridge penalty of 100 in an unnormalized weighted
   sum-of-squares objective; the intercept is unpenalized. Strong defense has a
   positive coefficient, indicating suppression of the opponent's outcome.
   The success model estimates relative effects, not bounded play probabilities.
4. Fit the previous completed regular season with the same procedure. For each
   of the eight unit/type/metric coefficients, use the across-team population
   standard deviation as its scale. Use that prior season's weighted league
   dropback/designed-run share as the common play mix. No prior team coefficients
   enter the current-season fit. The calibration year must precede the season.
5. Divide each current coefficient by its corresponding prior-season scale,
   then combine dropbacks and designed runs with the common mix. Average the
   four standardized offense/defense EPA/success components with 22.5% each.
6. Add standardized special-teams value with a 10% weight, as specified below.
7. Convert composite `z` to `50 + 50 * tanh(z / 2)`. This smooth display transform
   preserves ordering and differences before rounding; 50 is average unit
   strength, not the 50th percentile or a 50% win probability. Rank unrounded
   scores, display one decimal, and allow identical displayed scores to have
   different ranks when the underlying values differ.

The 100-play penalty, 25% garbage-time floor, probability thresholds, equal
component weights, 10% ST weight and display transform are explicit initial design choices,
not empirically optimal parameters. In sparse schedules the ridge penalty
necessarily pulls effects toward zero. No confidence intervals, injury inputs,
recent-form decay, or prior team rankings have been added.

## Special teams

ST includes live field goals, extra points, punts and kickoffs with valid EPA,
expected points, field position and half time. Require the matching attempt
flag; nflverse can label a nullified kick as a kick without flagging it deleted.
Deleted rows and two-point attempts are excluded. Fake kicks classified as
run/pass plays stay in scrimmage efficiency and are not counted twice. Kicks
retain full weight regardless of game state; the Q4 taper above applies to
scrimmage only. No standalone penalty-only/no-attempt value is added.

The target is the resulting point value `ep + epa`, compared with prior-season
expectation for the same kind of kick. This removes the inherited pre-kick
expected-points value before crediting execution. Scoring kicks use attempt
distance; punts and kickoffs use starting field position, never realized kick
distance or return yards. Half-time context is grouped into <=60 seconds,
61–180 seconds, and >180 seconds. Prior-season outcomes are smoothed with
Gaussian distance weights (five yards for scoring kicks/kickoffs, ten for punts)
at matching five-/ten-yard bucket centers. Clock groups with fewer than ten
plays fall back to that kick type's full prior-season sample. Each type receives
an offset so its calibration-play residuals average zero. All lookup values and
offsets are recorded in the generated JSON.

On punts, posteam is the punting team; on kickoffs it is the receiving team.
Credit residual value to posteam and its opposite to defteam for these two
types. A normal scoring-kick miss costs the kicking team without crediting the
opponent. Explicit blocks or defensive returns receive opposite credit for the
blocking/return unit. This includes blocks, returns, muffs and recoveries when
represented in the eligible play's EPA; defensive conversion returns remain
excluded by the existing two-point-attempt rule.

Sum the four categories and divide by team games, not kick count. Then use
`total_points / (games + 2)` to limit small samples and standardize against
the prior season's across-team mean and population standard deviation using
the same procedure. Per-category points, games, raw points/game, adjusted
points/game and standardized ST are available in the model's fitted output.
The prior mean/scale are league anchors; prior team ratings are not imported.

ST is adjusted for kick context, not opposing ST unit strength, weather or
individual kicker quality. Kickoff rule changes may affect cross-season
baselines. The 10% blend is an explicit descriptive design choice, not a
forecasting weight learned from these historical diagnostics.

## Versions and historical cutoffs

The dashboard JSON includes `efficiency_model` with parameters and the frozen
2025 calibration, plus `model_version` on snapshots. League rows contain the
unrounded overall score and offense, defense and special-teams ranks. Raw
dashboard rates are not replaced by adjusted coefficients. Both the dashboard
and Ravens sidebar are generated from the same live ranking table.

Archived Weeks 1–3 retain their original v1 values and are explicitly tagged;
cross-version score changes are not displayed. The published Week 4 v2.1 board
supplies that archived dashboard snapshot's overall score and rank. Subsequent
current-period fits use only completed games available at the cutoff and the
same frozen calibration throughout. The 2025 benchmark is scored on its own
full-season calibration as a retrospective reference, not an out-of-sample test.

The current league cutoff follows completed league games, including during a
Ravens bye or before Baltimore plays that week. A team's score can change when
its opponents play, even if the team itself has no new game. Archived articles
keep their originally published values. Version 2.1 was introduced with Week 4
and is now part of the production daily updater.

## Validation

Run:

```powershell
python scripts/test_efficiency_dashboard.py
python scripts/test_ravens_filmstudy.py
ruby scripts/check_ravens_dashboard.rb
```

The pre-publication historical diagnostic fitted weeks 3, 6, 9 and 12 in 2024 and 2025, using only
the preceding season for calibration. It compares rankings with net EPA/play
and average scoring margin over the next four calendar weeks. Parameters were
not selected from these results. Mean Spearman correlations across eight folds:

| Subsequent outcome | Original v1 | Adjusted v2.0 | v2.1 with ST |
| --- | ---: | ---: | ---: |
| Net EPA/play | 0.402 | 0.397 | 0.381 |
| Scoring margin/game | 0.415 | 0.402 | 0.384 |

These results do not establish a predictive improvement from the adjusted model
or from adding ST. The original v2.0 report is preserved separately. The windows overlap,
teams recur, and the test includes only two seasons. The change adds explicit
context adjustment and retains actual performance magnitudes; future predictive
claims require separate training/tuning and untouched holdout seasons.

Those research diagnostics are separate from the production updater. CI runs
offline behavioral tests, then fetches the current feeds and validates the
generated dashboard and sidebar together before committing either artifact.
