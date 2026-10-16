# Dual Eights Power Index: NFL publishing and operation

## Injury watchlist and manual scenarios

`/nfl/injuries/` shows non-QB position-group candidates and all-team feed coverage.
Flags never apply points. Team-row links and the QB & injury scenarios launcher
open signed manual group adjustments. Those are personal browser-session scenarios,
not editorial publication settings: they affect only games whose kickoff is still
in the future, and affect rankings only when explicitly selected. Completed games,
archives and Efficiency remain unchanged. Changes expire with the base data revision.
Lineup columns include QB and injury ranking effects and remain league-centered.

`scripts/nfl_injury_baselines.json` defines conservative **editorial**, unvalidated
starting group effects. Meaningful/severe: OL 1/2; receivers 1/2; secondary .75/1.5;
front .75/1.25; off-ball linebackers .5/.75; backs .25/.75 points. These are total
group effects relative to healthy, not per player. No public research found in this
review establishes these exact weekly cluster values. Position-weighted burden
research supports differentiated screening; it does not calibrate these presets.
The low magnitudes and quarter-point steps are deliberate starting judgments.
Use the calculator: net = upcoming impairment minus impairment already embedded.
For full recovery from an embedded -1, upcoming effect 0 gives net +1. Do not
apply the refit's .85 multiplier again or duplicate supporting-cast/QB effects.

Refresh the watchlist without recomputing or rewriting rankings:

```
python scripts/update_nfl_injury_watchlist.py --cache-dir .nfl-cache --season 2026 --week 6 --refresh
python -m unittest discover -s scripts -p test_nfl_injury_watchlist.py -v
node --test scripts/test_nfl_injuries.cjs
```

The CLI refreshes the latest injury statuses and public player IDs; prior-game
snaps and timestamped depth charts come from the model cache. GSIS/PFR IDs are
joined explicitly; unmatched players are counted, never assigned invented roles.
Healthy-role proxy: median of the three largest prior-game snap shares, with two
substantial prior games or a current depth-chart starter designation.

Strict screening requires **two meaningful players in the same position group**,
each meeting at least one condition:

- Explicit **Out** game designation (Doubtful/Questionable do not suffice).
- Sourced, currently confirmed **IR**, without a later activation.
- Two consecutive **injury-related DNP** daily reports in the current game week.

A later LP/FP clears the practice trigger. OUT or IR still qualifies independently;
returning to practice alone does not activate someone from IR. Non-injury rest or
personal absences do not count toward a DNP streak. Missing reports are unknown.
Speculative returns, single DNPs and routine limited practice no longer populate
the watchlist. Positive return scenarios remain available manually in the UI.

The latest-status parquet has no daily report dates/history. Never infer a second
DNP from fetch times, duplicate polls, prior weeks or a missing report. Research
agents can add official dated team reports and verified IR/activation records to
`scripts/nfl_injury_evidence.json`; its instructions define both schemas. Include
LP/FP rows so recovery clears the trigger. Reports are deduplicated by team/day,
using the latest observed revision; omitted players break a streak. Two dated DNPs
must be on adjacent days: unverified calendar gaps are not filled. Evidence must
match the target season/week, be observed by the build time, and have an HTTPS
source. Practice dates are checked against the scheduled game week. IR evidence
is reverified for each target week, not carried forward as an unverified assumption.
An empty evidence ledger means **OUT-only feed screening**, not complete injury
coverage; the page displays daily-history coverage explicitly.

`scripts/nfl_injury_reviews.json` can add sourced, timestamped commentary to a
qualifying team/group. Reviews require season, week, team, group, summary,
confidence, sources (title/url) and observed_at (timezone-aware ISO timestamp).
They cannot change eligibility, substitute player lists or reinstate cleared cases.
Verify replacement quality, normal workloads and effects already reflected in
DEPI before choosing points. Neither flags nor reviews apply adjustments.

After the Week 5 publication hold ends, the normal complete-week updater also
refreshes watchlist candidates for its projection week. While the hold is active,
use the standalone CLI; the existing updater still writes nothing. No periodic
agent or new automation was created. Research design and validation requirements
are in the local October 15 injury-cluster proposal.

The public hub has one reviewed DEPI formula. Coefficients are frozen in
`nfl_model_config.json`; public pages show only “Beta.” Production Efficiency
uses `compute_league_metrics` followed by the existing production
`efficiency_dashboard.apply_model` and frozen calibration. The NFL pipeline
does not change that formula or the Ravens dataset. Frozen DEPI helpers use
relative package imports so future Efficiency module updates cannot alter DEPI.

Omit `--ratings-week` in subsequent scheduled runs to
advance only after every game in the next week is final. Scores/market data
may include newer games than the rating cutoff. The cache is excluded from
Jekyll output and Git. Download current PBP once for both trimmed datasets;
historical cached inputs are hash checked. No public data is replaced when
coverage or model checks fail.

The current-year replays compute features before each target week. Frozen
coefficients were trained through 2023. They are retrospective because model
selection happened later. Only records generated before kickoff may enter
the saved-forecast archive; revised forecasts append to it rather than erase
earlier values. Final games use the latest existing pregame record. Initial
saved records originated in private research, and the public results page
states this. They are not asserted to have been publicly published then.

The initial archive preserves the October 6 research forecast for Thursday’s
Tampa Bay–Dallas game, which finished before this hub was built. The forecast
assumed Mayfield; the record retains that assumption. Actual starters and
scores are separately sourced from the schedule. Completed games show a
separate `display_home_margin` adjusted to actual starters using the QB skill
snapshot at `forecast_rating_week`. `forecast_home_margin` and the saved
archive retain the original forecast. Adjustment labels and original margins
remain visible, so a retrospective lineup correction is never presented as a
saved pregame prediction. The displayed game error uses the adjusted margin;
internal summary metrics retain the original forecast basis. User QB scenarios
never rewrite results or archives.

`nfl_continuity_audit.json` records a whole-league experiment removing
coach/QB carry reductions while retaining frozen coefficients. Default
2024/25 MAE: 10.0237 / 10.1434. Without transition reductions: 10.0186 /
10.1375. These previously inspected seasons do not establish a predictive
advantage. Miami and Tennessee retain ranks 31/32; no formula change was
made from this audit.

## Refit activation after completed Week 6

The backend default is the reviewed **refit-only** formula: original features,
ridge penalty 360 (previously 120), and a 0.85 multiplier on fitted team-strength
coefficients. The multiplier is already embedded in the stored coefficients;
never multiply the dashboard outputs again. Fitted home advantage is unchanged
by that multiplier (1.536670 points). No drive, penalty or new QB/context features
enter. Historical priors and the production Efficiency Index are unchanged.

`nfl_model_config.json` freezes the new coefficients, original coefficients in
`previous_model`, and an activation cutoff of **2026 rating Week 6**. While the
latest complete cutoff is Week 5 or earlier, the updater exits before model
generation or any public-data/archive write. An explicit partial Week 6 update
also exits. Thus the published Week 5 rankings, Week 6 spreads, results and
accompanying article remain unchanged until all Week 6 games are final. Input
downloads may still refresh during this hold; they do not publish anything.

The next complete-week refresh automatically uses the refit for rankings through
Week 6 and projections for Week 7. Weekly rank movement compares with the actual
published Week 5 table. New forecast records identify their formula with
`model_id`. Existing archived forecasts remain untouched; older records without
an ID use the formula effective at their rating cutoff. Historical replay and
actual-starter adjustments also use that historical formula, so the new QB
coefficients do not rewrite old spreads. New helper logic depends on unchanged
feature generation across these two formulas; a future feature change needs
versioned feature snapshots as well.

The frozen refit was trained through 2023; scale selection used rolling
2022–2023 forecasts. Retrospective MAE is 10.0999 across 2024–2025 and 9.8425
through completed 2026 Week 5. Those inspected seasons did not select its
coefficients or scale, and do not establish a prospective accuracy gain.

Daily refreshes and a Thursday correction-window refresh are defined in
`update-nfl-dashboard.yml`. Market lines are dated snapshots from nflverse,
not live book quotes. Missing current-week injury context never confirms QB
availability. Depth charts are timestamped and players remain manually
selectable.

Validation:

```
python scripts/check_nfl_dashboard.py
python -m unittest discover -s scripts -p test_nfl_dashboard.py -v
python -m unittest discover -s scripts/strength_beta_lab -p test_refinement.py -v
bundle exec jekyll build --destination _site-validation
python scripts/check_site.py _site-validation
```

After activation, manual interim updates can pass an explicit `--ratings-week`
with `--allow-partial-week` to include only final games. All earlier weeks must be complete. Coverage
is checked against PBP, pending matchups are exposed on the UI, and the
scheduled default still requires a fully completed week.

Completed QB reconciliation: use the first recorded dropback by a known QB
from current-season PBP, with full names from archived depth charts. Correct
current-season schedule identities before observed-starter features and
actual-starter adjustments. Trick-play passers, later relief QBs and future
games do not replace the recorded starter. Without PBP, retain the schedule
fallback. Expose mismatches in `completed_qb_corrections` for audit.
