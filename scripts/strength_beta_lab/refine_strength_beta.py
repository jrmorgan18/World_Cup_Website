"""Opponent-adjusted NFL strength primitives used by the NFL dashboard."""
import hashlib
import argparse
import json
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from team_strength_beta import (Builder, TEAMS, TEAM_NAMES, normalize, decay, fit_margin,
                               fit_st, qb_rows, qb_skills, observed_starters, legacy_scores, metrics)

BASE_FEATURES = ['pass_offense', 'pass_defense', 'run_offense', 'run_defense', 'st',
                 'qb_epa_delta', 'qb_cpoe_delta', 'qb_rush_delta']
SUCCESS_FEATURES = ['pass_success_offense', 'pass_success_defense',
                    'run_success_offense', 'run_success_defense']
INTERNATIONAL = ('tottenham', 'wembley', 'maracana', 'melbourne', 'bernabeu',
                 'allianz', 'deutsche bank park', 'estadio', 'stade de france',
                 'fcbayern', 'fc bayern')


@dataclass(frozen=True)
class Experiment:
    key: str
    label: str
    qb: bool = False
    stable: bool = False
    offense_prior: float = 175.
    defense_prior: float = 75.
    offense_carry: float = .80
    defense_carry: float = .40
    half_life: float = 8.
    history_share: float = 1.
    continuity_adjustment: bool = True

    @property
    def features(self):
        return BASE_FEATURES + (SUCCESS_FEATURES if self.stable else [])


EXPERIMENTS = [Experiment('history', 'Historical weighting'),
               Experiment('qb', 'History + QB refinement', qb=True),
               Experiment('stability', 'History + consistency', stable=True),
               Experiment('refined', 'Combined beta 0.2', qb=True, stable=True),
               Experiment('lower_history', 'Combined · 10% less history', qb=True, stable=True, history_share=.9)]


def history_penalty(exposure, prior, share):
    """Reduce the prior's conditional influence relatively, transferring weight to observed plays.

    p'/(n+p') = share*p/(n+p). With no observed plays, retain the preseason
    anchor: there is no current-season evidence to receive the extra weight.
    """
    n = np.asarray(exposure, dtype=float)
    if not 0 < share <= 1:
        raise ValueError('history_share must be in (0, 1]')
    return np.where(n > 0, share * prior * n / np.maximum(n + (1-share)*prior, 1e-12), prior)


def correct_venues(games):
    games = games.copy()
    abroad = games.stadium.fillna('').str.lower().apply(lambda s: any(v in s for v in INTERNATIONAL))
    games.loc[abroad, 'location'] = 'Neutral'
    return games


def continuity(games, previous, cutoff, experiment, default_qbs=None):
    """Only observed current games identify changes; temporary midseason QB switches do not reset history."""
    offense = np.full(32, experiment.offense_carry)
    defense = np.full(32, experiment.defense_carry)
    info = {}
    current = games[games.week <= cutoff].sort_values(['week', 'gameday'])
    for i, team in enumerate(TEAMS):
        def appearances(frame):
            records = []
            for r in frame.itertuples():
                if r.home_team == team:
                    records.append((r.home_coach, r.home_qb_id))
                elif r.away_team == team:
                    records.append((r.away_coach, r.away_qb_id))
            return records
        old, now = appearances(previous), appearances(current)
        old_coach = old[-1][0] if old else None
        old_qbs = pd.Series([r[1] for r in old], dtype=object).dropna()
        old_qb = old_qbs.value_counts().index[0] if len(old_qbs) else None
        coach = now[-1][0] if now else None
        first_qb = (default_qbs or {}).get(team, now[0][1] if now else None)
        new_coach = bool(old_coach and coach and pd.notna(old_coach) and pd.notna(coach) and old_coach != coach)
        # A known returning backup making the opener is not a roster reset.
        new_qb = bool(old_qb and first_qb and pd.notna(first_qb) and old_qb != first_qb
                      and first_qb not in set(old_qbs))
        if new_coach and experiment.continuity_adjustment:
            offense[i] *= .65
            defense[i] *= .65
        if new_qb and experiment.continuity_adjustment:
            offense[i] *= .60
        info[team] = {'new_head_coach': new_coach, 'new_opening_qb': new_qb,
                      'head_coach': str(coach) if coach else 'Unobserved',
                      'offense_carry': float(offense[i]), 'defense_carry': float(defense[i])}
    return offense, defense, info


def fit_phase(rows, phase, cutoff, exp, prior, carries):
    """Fit EPA and success jointly against the same opponents, with separate unit priors."""
    sample = rows[(rows.phase == phase) & (rows.week <= cutoff)].copy()
    target = prior * np.asarray(carries).T[:, :, None]
    target -= target.mean(axis=0)
    if sample.empty:
        return target, {'intercept': 0., 'venue': 0.}, np.zeros(32)
    sample['w'] = sample.weight * decay(sample.week, cutoff, exp.half_life)
    sample['wy'] = sample.w * (sample.stable_epa if exp.stable else sample.epa)
    sample['ws'] = sample.w * (sample.stable_success if exp.stable else sample.success)
    grouped = sample.groupby(['posteam', 'defteam', 'venue'], as_index=False)[['w', 'wy', 'ws']].sum()
    positions = {t: i for i, t in enumerate(TEAMS)}
    x = np.zeros((len(grouped), 66))
    ix = np.arange(len(grouped))
    x[:, 0] = 1.
    x[ix, 1 + grouped.posteam.map(positions).to_numpy()] = 1.
    x[ix, 33 + grouped.defteam.map(positions).to_numpy()] = -1.
    x[:, -1] = grouped.venue
    off_counts = sample.groupby('posteam').w.sum().reindex(TEAMS, fill_value=0).to_numpy()
    def_counts = sample.groupby('defteam').w.sum().reindex(TEAMS, fill_value=0).to_numpy()
    penalty = np.r_[0., history_penalty(off_counts, exp.offense_prior, exp.history_share),
                   history_penalty(def_counts, exp.defense_prior, exp.history_share), 100.]
    anchor = np.vstack([np.zeros((1, 2)), target[:, 0], target[:, 1], np.zeros((1, 2))])
    beta = np.linalg.solve(x.T @ (x * grouped.w.to_numpy()[:, None]) + np.diag(penalty),
                           x.T @ grouped[['wy', 'ws']].to_numpy() + penalty[:, None] * anchor)
    units = np.stack([beta[1:33], beta[33:65]], axis=1)
    units -= units.mean(axis=0)
    counts = sample.groupby('posteam').w.sum().reindex(TEAMS, fill_value=0).to_numpy()
    return units, {'intercept': float(beta[0, 0]), 'venue': float(beta[-1, 0])}, counts


def fumble_baseline(rows):
    """Prior-season recovery rates and conditional turnover costs; no current/future outcomes."""
    sample = rows[rows.offensive_fumble].copy()
    if len(sample) < 40:
        raise ValueError('Insufficient prior-season offensive fumbles')
    # Context controls for sacks, passing, field position, down and gained yardage.
    x = np.column_stack([np.ones(len(sample)), sample.fumble_lost,
                         (sample.phase == 'dropback').astype(float), sample.sack.fillna(0),
                         sample.yardline_100 / 100., sample.down.fillna(1) / 4.,
                         sample.yards_gained.clip(-20, 40) / 20.])
    regularizer = np.eye(x.shape[1]) * 10.
    regularizer[0, 0] = 0.
    coef = np.linalg.solve(x.T @ x + regularizer, x.T @ sample.epa)
    cost = float(np.clip(-coef[1], 1., 7.))
    rates = {}
    overall = float(sample.fumble_lost.mean())
    for phase in ['dropback', 'designed_run']:
        subset = sample[sample.phase == phase]
        rates[phase] = float((subset.fumble_lost.sum() + 30 * overall) / (len(subset) + 30))
    return {'loss_rates': rates, 'turnover_cost': cost, 'sample': int(len(sample))}


def stabilize(rows, baseline):
    rows = rows.copy()
    adjustment = (rows.fumble_lost - rows.phase.map(baseline['loss_rates'])) * baseline['turnover_cost']
    rows['fumble_adjustment'] = adjustment.where(rows.offensive_fumble, 0.)
    rows['stable_epa'] = rows.epa + rows.fumble_adjustment
    rows['stable_success'] = rows.success.where(~rows.offensive_fumble, (rows.stable_epa > 0).astype(float))
    return rows


def draft_group(qb_id, year, first_seen, draft, starts):
    record = draft.get(qb_id, {})
    # NFL performance before this season is required for an established role.
    if first_seen.get(qb_id, year) < year:
        return 'established_starter' if starts.get(qb_id, 0) >= 8 else 'experienced_backup'
    return 'rookie_early' if record.get('season', year) == year and record.get('pick', 999) <= 32 else 'rookie_other'


def refined_qb_skills(history, current, year, cutoff, games, draft, first_seen):
    frames = [r for y, r in history.items() if year - 2 <= y < year] + [current[current.week <= cutoff]]
    data = pd.concat(frames, ignore_index=True).copy()
    ages = data.groupby('season').week.transform('max') - data.week
    ages = ages.where(data.season != year, cutoff - data.week)
    data['w'] = data.weight * .55 ** (year - data.season) * .5 ** (ages / 16.)
    data['wy'] = data.w * data.relative_epa
    data['wc'] = data.w.where(data.cpoe.notna(), 0.)
    data['wcy'] = data.wc * data.cpoe.fillna(0.)
    data['wr'] = data.w * data.rush_value
    starts_by_year = {}
    for y, schedule in games.items():
        if y >= year:
            continue
        starts_by_year[y] = pd.concat([schedule.home_qb_id, schedule.away_qb_id]).value_counts().to_dict()
    prior = data[data.season < year].groupby(['season', 'qb_id'])[['w', 'wy', 'wc', 'wcy', 'wr']].sum()
    prior = prior[prior.w >= 20].reset_index()
    prior['group'] = [draft_group(q, int(y), first_seen, draft, starts_by_year.get(int(y) - 1, {}))
                      for y, q in zip(prior.season, prior.qb_id)]
    population = {'epa': float((prior.wy / prior.w).clip(-.5, .5).mean()),
                  'cpoe': float((prior.wcy / prior.wc.replace(0, np.nan)).clip(-15, 15).mean()),
                  'rush': float((prior.wr / prior.w).clip(-.2, .2).mean())}
    if not np.isfinite(list(population.values())).all():
        population = {'epa': -.05, 'cpoe': 0., 'rush': 0.}
    priors = {}
    for group in ['established_starter', 'experienced_backup', 'rookie_early', 'rookie_other']:
        subset = prior[prior.group == group]
        priors[group] = {'quarterback_seasons': int(len(subset))}
        for metric, numerator, denominator, cap in [('epa', 'wy', 'w', .5), ('cpoe', 'wcy', 'wc', 15.), ('rush', 'wr', 'w', .2)]:
            estimates = (subset[numerator] / subset[denominator].replace(0, np.nan)).dropna().clip(-cap, cap)
            priors[group][metric] = float((estimates.sum() + 5 * population[metric]) / (len(estimates) + 5))
    summed = data.groupby('qb_id')[['w', 'wy', 'wc', 'wcy', 'wr']].sum()
    skills = pd.DataFrame(index=summed.index)
    last_starts = starts_by_year.get(year - 1, {})
    for qb_id, row in summed.iterrows():
        group = draft_group(qb_id, year, first_seen, draft, last_starts)
        anchor = priors[group]
        shrink = 75. if group == 'established_starter' else 200.
        skills.loc[qb_id, 'epa'] = (row.wy + shrink * anchor['epa']) / (row.w + shrink)
        skills.loc[qb_id, 'cpoe'] = (row.wcy + shrink * anchor['cpoe']) / (row.wc + shrink)
        skills.loc[qb_id, 'rush'] = (row.wr + 100 * anchor['rush']) / (row.w + 100)
        skills.loc[qb_id, 'effective_dropbacks'] = row.w
        skills.loc[qb_id, 'prior_plays'] = shrink
        skills.loc[qb_id, 'prior_group'] = group
    priors['_unseen_groups'] = {q: 'rookie_early' for q, r in draft.items()
                                if r.get('season') == year and r.get('pick', 999) <= 32}
    return skills, priors


def skill_for(skills, qb_id, priors):
    if qb_id in skills.index:
        return skills.loc[qb_id].to_dict()
    group = priors.get('_unseen_groups', {}).get(qb_id, 'rookie_other')
    anchor = priors[group] if 'rookie_other' in priors else priors
    return {**anchor, 'rush': anchor.get('rush', 0.), 'effective_dropbacks': 0.,
            'prior_plays': 200., 'prior_group': group}


def reference(rows, previous, skills, priors, cutoff, exp, offense_carry):
    sample = rows[(rows.phase == 'dropback') & (rows.week <= cutoff)].copy()
    sample['qb_id'] = sample.passer_player_id.where(sample.passer_player_id.notna(), sample.rusher_player_id)
    sample['w'] = sample.weight * decay(sample.week, cutoff, exp.half_life)
    previous = previous.copy() if previous is not None else pd.DataFrame()
    if len(previous):
        previous['w'] = previous.weight * decay(previous.week, int(previous.week.max()), exp.half_life)
    values = np.zeros((32, 3))
    for j, metric in enumerate(['epa', 'cpoe', 'rush']):
        mapping = skills[metric].to_dict() if metric in skills else {}
        fallback = skill_for(skills, '', priors).get(metric, 0.)
        sample['wy'] = sample.w * sample.qb_id.map(mapping).fillna(fallback)
        counts = sample.groupby('posteam').w.sum().reindex(TEAMS, fill_value=0)
        total = sample.groupby('posteam').wy.sum().reindex(TEAMS, fill_value=0)
        prior = np.zeros(32)
        if len(previous):
            previous['wy'] = previous.w * previous.qb_id.map(mapping).fillna(fallback)
            prior = (previous.groupby('posteam').wy.sum().reindex(TEAMS, fill_value=0) /
                     previous.groupby('posteam').w.sum().reindex(TEAMS, fill_value=0).replace(0, np.nan)).fillna(0).to_numpy()
        penalty = history_penalty(counts.to_numpy(), exp.offense_prior, exp.history_share)
        values[:, j] = (total.to_numpy() + penalty * prior * offense_carry) / (counts.to_numpy() + penalty)
    return values


def add_qbs(table, embedded, skills, priors, starters):
    table = table.copy()
    for i, team in enumerate(TEAMS):
        skill = skill_for(skills, starters.get(team, {}).get('id', ''), priors)
        for j, metric in enumerate(['epa', 'cpoe', 'rush']):
            table.loc[team, f'qb_{metric}_delta'] = skill.get(metric, 0.) - embedded[i, j]
    return table


class RefinedBuilder(Builder):
    def __init__(self, cache, season, week):
        super().__init__(cache, season, week)
        extra = cache / 'refinement'
        self.extra_sources = json.loads((extra / 'manifest.json').read_text())
        for source in self.extra_sources:
            if hashlib.sha256((extra / source['file']).read_bytes()).hexdigest() != source['cache_sha256']:
                raise ValueError('Supplemental input hash mismatch: ' + source['file'])
        self.all_schedule = correct_venues(self.all_schedule)
        draft = pd.read_parquet(extra / 'draft_picks.parquet')
        self.draft = {r.gsis_id: {'season': int(r.season), 'pick': int(r.pick)} for r in draft.dropna(subset=['gsis_id']).itertuples() if r.position == 'QB'}
        self.first_seen, self.fumble_context = {}, {}
        baseline = None
        for year in self.rows:
            self.games[year] = correct_venues(self.games[year])
            rows = self.rows[year]
            supplemental = normalize(pd.read_parquet(extra / f'pbp-extra-{year}.parquet'), ['fumbled_1_team', 'fumbled_2_team'])
            joined = rows.merge(supplemental, on=['game_id', 'play_id'], how='left', validate='one_to_one', suffixes=('', '_check'))
            if joined.epa_check.isna().any() or not np.allclose(joined.epa, joined.epa_check, atol=1e-6):
                raise ValueError(f'Original and supplemental PBP snapshots differ for {year}')
            neutral_ids = set(self.games[year].loc[self.games[year].location == 'Neutral', 'game_id'])
            joined.loc[joined.game_id.isin(neutral_ids), 'venue'] = 0.
            joined['offensive_fumble'] = ((joined.fumble == 1) & (joined.fumbled_1_team == joined.posteam)
                                         & joined.fumbled_2_team.isna() & (joined.interception != 1))
            joined['qb_epa'] = joined.qb_epa.fillna(joined.epa)
            own_baseline = fumble_baseline(joined)
            # First bootstrap year calibrates itself; scored years always use a prior season.
            self.fumble_context[year] = baseline or own_baseline
            self.rows[year] = stabilize(joined, self.fumble_context[year])
            baseline = own_baseline
            for qb_id in joined.loc[joined.phase == 'dropback', 'passer_player_id'].dropna().unique():
                self.first_seen.setdefault(qb_id, year)

    def generate_refined(self, exp, evaluate_from=2019):
        records, details = [], {}
        prior_pass = np.zeros((32, 2, 2))
        prior_run = np.zeros_like(prior_pass)
        prior_st = np.zeros(32)
        history = {}
        for year in self.rows:
            maximum = self.week if year == self.season else int(self.games[year].week.max())
            cutoffs = range(maximum + 1) if year >= evaluate_from else [maximum]
            for cutoff in cutoffs:
                default_qbs = None
                if year == self.season and cutoff > 0:
                    stamp = pd.Timestamp(self.games[year].loc[self.games[year].week <= cutoff, 'gameday'].max(), tz='UTC') + pd.Timedelta(days=1, hours=12)
                    archived = self.depth_all[pd.to_datetime(self.depth_all.dt, utc=True) <= stamp]
                    depth = self.depth if cutoff == self.week else archived[archived.dt == archived.dt.max()]
                    default_qbs = {r.team: r.gsis_id for r in depth[(depth.pos_abb == 'QB') & (depth.pos_rank == 1) & depth.gsis_id.notna()].itertuples()}
                off_carry, def_carry, flags = continuity(self.games[year], self.games.get(year - 1, self.games[year].iloc[:0]), cutoff, exp, default_qbs)
                passing, context, exposure = fit_phase(self.rows[year], 'dropback', cutoff, exp, prior_pass, [off_carry, def_carry])
                running, run_context, _ = fit_phase(self.rows[year], 'designed_run', cutoff, exp, prior_run, [off_carry, def_carry])
                st = fit_st(self.st[year], self.games[year], cutoff, type('Settings', (), {'half_life_weeks': exp.half_life})(), prior_st)
                table = pd.DataFrame({'pass_offense': passing[:, 0, 0], 'pass_defense': passing[:, 1, 0],
                                      'run_offense': running[:, 0, 0], 'run_defense': running[:, 1, 0], 'st': st,
                                      'pass_success_offense': passing[:, 0, 1], 'pass_success_defense': passing[:, 1, 1],
                                      'run_success_offense': running[:, 0, 1], 'run_success_defense': running[:, 1, 1]}, index=TEAMS)
                visible = self.rows[year][self.rows[year].week <= cutoff].copy()
                qrows = qb_rows(visible, passing[:, :, 0], context, year)
                # QB-specific EPA removes receiver fumble losses when nflverse supplies that adjustment.
                if exp.qb:
                    qrows['relative_epa'] += (visible.loc[visible.phase == 'dropback', 'qb_epa'] -
                                             visible.loc[visible.phase == 'dropback', 'epa']).to_numpy()
                qb_ids = set(qrows.qb_id) | set(self.draft) | set(history.get(year - 1, pd.DataFrame(columns=['qb_id'])).qb_id)
                rush = visible[(visible.phase == 'designed_run') & visible.rusher_player_id.isin(qb_ids)].copy()
                rush['value'] = rush.epa - run_context['intercept'] + rush.defteam.map(dict(zip(TEAMS, running[:, 1, 0]))) - run_context['venue'] * rush.venue
                rush_sum = (rush.value * rush.weight).groupby([rush.rusher_player_id, rush.week]).sum()
                drop_sum = qrows.weight.groupby([qrows.qb_id, qrows.week]).sum()
                qrows['rush_value'] = [float(rush_sum.get((q, w), 0.) / drop_sum.get((q, w), 1.)) for q, w in zip(qrows.qb_id, qrows.week)]
                if exp.qb:
                    skills, priors = refined_qb_skills(history, qrows, year, cutoff, self.games, self.draft, self.first_seen)
                else:
                    skills, priors = qb_skills(history, qrows, year, cutoff)
                    skills['rush'] = 0.
                embedded = reference(self.rows[year], history.get(year - 1), skills, priors, cutoff, exp, off_carry)
                starters = observed_starters(self.games[year], cutoff, self.games.get(year - 1))
                table = add_qbs(table, embedded, skills, priors, starters)
                legacy, net_epa = legacy_scores(self.rows[year], cutoff)
                if year >= 2019:
                    for game in self.games[year][self.games[year].week == cutoff + 1].itertuples():
                        home_venue = float(game.location == 'Home')
                        features = list((table.loc[game.home_team, exp.features] - table.loc[game.away_team, exp.features]).to_numpy()) + [home_venue]
                        # Actual starter identity is used only for conditional-lineup training/evaluation.
                        # Player skill still stops at the previous week; no upcoming performance is used.
                        conditional_features = list(features)
                        for team, actual_qb, sign in [(game.home_team, game.home_qb_id, 1.), (game.away_team, game.away_qb_id, -1.)]:
                            actual_skill = skill_for(skills, actual_qb, priors)
                            assumed_skill = skill_for(skills, starters.get(team, {}).get('id', ''), priors)
                            for metric in ['epa', 'cpoe', 'rush']:
                                j = exp.features.index('qb_' + metric + '_delta')
                                conditional_features[j] += sign * (actual_skill.get(metric, 0.) - assumed_skill.get(metric, 0.))
                        records.append({'season': year, 'week': int(game.week), 'game_id': game.game_id,
                                        'actual': float(game.home_score - game.away_score), 'features': features,
                                        'conditional': conditional_features,
                                        'starter_change': bool(starters.get(game.home_team, {}).get('id') != game.home_qb_id or starters.get(game.away_team, {}).get('id') != game.away_qb_id),
                                        'legacy': [float(legacy[game.home_team] - legacy[game.away_team]), home_venue],
                                        'market': float(game.spread_line) if pd.notna(game.spread_line) else None})
                if year == self.season:
                    details[cutoff] = {'table': table, 'embedded': embedded, 'skills': skills, 'priors': priors,
                                       'starters': starters, 'flags': flags, 'legacy': legacy, 'exposure': exposure}
            prior_pass, prior_run, prior_st = passing, running, st
            history[year] = qrows
            print(f'{exp.key}: finished {year}', flush=True)
        return pd.DataFrame(records), details


def evaluate(rows, exp):
    fit_key = 'conditional' if exp.qb else 'features'
    train, tune = rows[rows.season <= 2021], rows[rows.season.isin([2022, 2023])]
    candidates = []
    for penalty in [40., 120.]:
        c = fit_margin(np.stack(train[fit_key]), train.actual.to_numpy(), penalty)
        candidates.append((metrics(tune.actual, np.stack(tune.features) @ c)['mae'], penalty))
    tuning_mae, penalty = min(candidates)
    fit = rows[rows.season <= 2023]
    coef = fit_margin(np.stack(fit[fit_key]), fit.actual.to_numpy(), penalty)
    results = {}
    for year in [2024, 2025]:
        test = rows[rows.season == year]
        changes = test[test.starter_change]
        late = test[test.week >= 4]
        results[str(year)] = {'beta': metrics(test.actual, np.stack(test.features) @ coef),
                              'conditional_lineup': metrics(test.actual, np.stack(test.conditional) @ coef),
                              'starter_changes_conditional': metrics(changes.actual, np.stack(changes.conditional) @ coef),
                              'starter_changes_previous_qb': metrics(changes.actual, np.stack(changes.features) @ coef),
                              'week_4_onward': metrics(late.actual, np.stack(late.features) @ coef)}
    return coef, {'training': '2019-2021', 'parameter_selection': '2022-2023', 'final_fit': '2019-2023',
                  'note': '2024-25 are retrospective comparisons. Conditional lineup assumes recorded starting identity; prior-week player performance only. No archived injury forecasts.',
                  'selected': {**asdict(exp), 'margin_penalty': penalty, 'tuning_mae': tuning_mae}, 'seasons': results}


def expected_qbs(builder, details, week):
    if week == builder.week:
        depth = builder.depth
    else:
        cutoff = pd.Timestamp(builder.games[builder.season].loc[builder.games[builder.season].week <= week, 'gameday'].max(), tz='UTC') + pd.Timedelta(days=1, hours=12)
        archived = builder.depth_all[pd.to_datetime(builder.depth_all.dt, utc=True) <= cutoff]
        depth = archived[archived.dt == archived.dt.max()]
    starters = dict(details['starters'])
    for r in depth[(depth.pos_abb == 'QB') & (depth.pos_rank == 1) & depth.gsis_id.notna()].itertuples():
        starters[r.team] = {'id': r.gsis_id, 'name': r.player_name}
    return starters


def model_payload(builder, exp, details, coef, validation, baseline):
    d = details[builder.week]
    expected = expected_qbs(builder, d, builder.week)
    table = add_qbs(d['table'], d['embedded'], d['skills'], d['priors'], expected)
    contributions = table[exp.features].to_numpy() * coef[:-1]
    contributions -= contributions.mean(axis=0)
    points = contributions.sum(axis=1)
    ranks = pd.Series(points, index=TEAMS).rank(ascending=False, method='min').astype(int)
    previous = details[builder.week - 1]
    previous_expected = expected_qbs(builder, previous, builder.week - 1)
    previous_table = add_qbs(previous['table'], previous['embedded'], previous['skills'], previous['priors'], previous_expected)
    previous_points = previous_table[exp.features].to_numpy() @ coef[:-1]
    previous_points -= previous_points.mean()
    previous_ranks = pd.Series(previous_points, index=TEAMS).rank(ascending=False, method='min').astype(int)
    old = {t['abbr']: t for t in baseline['teams']}
    teams = []
    for i, team in enumerate(TEAMS):
        component = dict(zip(exp.features, map(float, contributions[i])))
        base = skill_for(d['skills'], expected[team]['id'], d['priors'])
        options = []
        depth = builder.depth[(builder.depth.team == team) & (builder.depth.pos_abb == 'QB') & builder.depth.gsis_id.notna()].sort_values('pos_rank')
        for q in depth.itertuples():
            skill = skill_for(d['skills'], q.gsis_id, d['priors'])
            change = sum((skill.get(metric, 0.) - base.get(metric, 0.)) * coef[exp.features.index('qb_' + metric + '_delta')] for metric in ['epa', 'cpoe', 'rush'])
            options.append({'id': q.gsis_id, 'name': q.player_name, 'depth_rank': int(q.pos_rank),
                            'points_change': float(change), 'effective_dropbacks': float(skill['effective_dropbacks']),
                            'prior_group': skill.get('prior_group', 'pooled'), 'prior_plays': float(skill.get('prior_plays', 200))})
        flags = d['flags'][team]
        warnings = list(old[team]['warnings'])
        if flags['new_head_coach']:
            warnings.append('Historical unit carry reduced for a new head coach.')
        if flags['new_opening_qb']:
            warnings.append('Historical offense carry reduced for a new primary QB; known returning backups do not trigger this reset.')
        offense = sum(v for k, v in component.items() if k.endswith('offense'))
        defense = sum(v for k, v in component.items() if k.endswith('defense'))
        qb = sum(v for k, v in component.items() if k.startswith('qb_'))
        teams.append({**old[team], 'rank': int(ranks[team]), 'strength': float(points[i]),
                      'offense_points': offense, 'defense_points': defense, 'qb_points': qb, 'st_points': component['st'],
                      'components': component, 'previous_week_beta_rank': int(previous_ranks[team]),
                      'previous_week_beta_strength': float(previous_points[i]),
                      'weekly_rank_change': int(previous_ranks[team] - ranks[team]),
                      'baseline_rank': old[team]['rank'], 'baseline_strength': old[team]['strength'],
                      'rank_difference': old[team]['rank'] - int(ranks[team]),
                      'expected_qb': expected[team], 'qb_options': options, 'warnings': warnings,
                      'historical_context': flags, 'effective_pass_plays': float(d['exposure'][i])})
    teams.sort(key=lambda t: t['rank'])
    for team in teams:
        team.pop('sensitivity_rank_min', None)
        team.pop('sensitivity_rank_max', None)
    return {'key': exp.key, 'label': exp.label, 'teams': teams, 'home_advantage': float(coef[-1]),
            'coefficients': dict(zip(exp.features + ['home_advantage'], map(float, coef))), 'validation': validation}
