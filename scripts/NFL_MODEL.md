# NFL beta publishing and operation

The public hub has one reviewed TSI formula. Coefficients are frozen in
`nfl_model_config.json`; public pages show only “Beta.” Production Efficiency
uses `compute_league_metrics` followed by the existing production
`efficiency_dashboard.apply_model` and frozen calibration. The NFL pipeline
does not change that formula or the Ravens dataset. Frozen TSI helpers use
relative package imports so future Efficiency module updates cannot alter TSI.

Run `python scripts/update_nfl_dashboard.py --season 2026 --ratings-week 4`
for the launch cutoff. Omit `--ratings-week` in subsequent scheduled runs to
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

Manual interim updates: pass `--ratings-week 5 --allow-partial-week` to include
only final games from Week 5. All earlier weeks must be complete. Coverage
is checked against PBP, pending matchups are exposed on the UI, and the
scheduled default still requires a fully completed week.

Completed QB reconciliation: use the first recorded dropback by a known QB
from current-season PBP, with full names from archived depth charts. Correct
current-season schedule identities before observed-starter features and
actual-starter adjustments. Trick-play passers, later relief QBs and future
games do not replace the recorded starter. Without PBP, retain the schedule
fallback. Expose mismatches in `completed_qb_corrections` for audit.
