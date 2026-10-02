# Dual Eights Efficiency Index v2

Version 2 implements opponent/venue adjustment, magnitude-preserving aggregation,
and game-state weighting with separate dropback and designed-run estimates.
It is an adjusted description of observed scrimmage efficiency, not a win
probability, betting model, or roster-based forecast. Special teams are excluded.

## Inputs and automation

The existing updater downloads the public nflverse schedule CSV and season PBP
Parquet releases, now additionally reading `qb_dropback`, `wp`, `qtr` and
`game_seconds_remaining`. No additional provider, key or paid data is required.
EPA, success and the existing eligibility exclusions are unchanged. Raw dashboard
EPA, success, explosive rates and red-zone statistics remain unweighted.

Source dictionaries:
- https://nflreadr.nflverse.com/articles/dictionary_pbp.html
- https://nflreadr.nflverse.com/articles/dictionary_schedules.html
- https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html

The updater refuses to replace the last good JSON if a scheduled completed game
lacks eligible plays for either offense, or a retained play lacks a required
model field or valid venue/team mapping. This catches missing games, not every
possible truncated-game or upstream scoring error. Historical data corrections
can revise prior weekly snapshots on a subsequent update.

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
   four standardized offense/defense EPA/success components with 25% each.
6. Convert composite `z` to `50 + 50 * tanh(z / 2)`. This smooth display transform
   preserves ordering and differences before rounding; 50 is average unit
   strength, not the 50th percentile or a 50% win probability. Rank unrounded
   scores, display one decimal, and allow identical displayed scores to have
   different ranks when the underlying values differ.

The 100-play penalty, 25% garbage-time floor, probability thresholds, equal
component weights and display transform are explicit initial design choices,
not empirically optimal parameters. In sparse schedules the ridge penalty
necessarily pulls effects toward zero. No confidence intervals, injury inputs,
recent-form decay, or prior team rankings have been added.

## Versions and historical cutoffs

The generated JSON includes `efficiency_model` with parameters and calibration,
per-team adjusted components and old `legacy_value`, and `model_version` on
snapshots. Earlier current-season weekly snapshots are rebuilt from games with
`week <= cutoff`; future plays are excluded before fitting opponents. The same
prior-season calibration is used throughout. The previous-season benchmark is
scored on its own full-season calibration as a retrospective reference.

The current league cutoff follows completed league games, including during a
Ravens bye or before Baltimore plays that week. A team's score can change when
its opponents play, even if the team itself has no new game. Archived articles
keep their original v1 values and link to the revised methodology.

## Validation

Run:

```powershell
python -m unittest discover -s scripts -p test_efficiency_model.py -v
python scripts/check_efficiency_artifact.py
ruby scripts/check_ravens_dashboard.rb
python scripts/validate_efficiency_history.py --output articles/efficiency-model-v2-validation.json
```

The historical diagnostic fits weeks 3, 6, 9 and 12 in 2024 and 2025, using only
the preceding season for calibration. It compares rankings with net EPA/play
and average scoring margin over the next four calendar weeks. Parameters were
not selected from these results. Mean Spearman correlations across eight folds:

| Subsequent outcome | Original v1 | Adjusted v2 |
| --- | ---: | ---: |
| Net EPA/play | 0.402 | 0.397 |
| Scoring margin/game | 0.415 | 0.402 |

These results do not establish a predictive improvement. The windows overlap,
teams recur, and the test includes only two seasons. The change adds explicit
context adjustment and retains actual performance magnitudes; future predictive
claims require separate training/tuning and untouched holdout seasons.

Historical downloads are cached in the system temporary directory; use a fresh
`--cache-dir` to refresh source corrections. CI runs the behavioral tests and
artifact checks without network data retrieval. The scheduled updater also
validates the generated artifact before committing it.
