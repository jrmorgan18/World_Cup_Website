"""Behavioral checks for causal cutoffs, unit continuity, recovery luck and QB priors."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from strength_beta_lab.refine_strength_beta import (TEAMS, Experiment, correct_venues, continuity,
                                 fit_phase, stabilize, refined_qb_skills, skill_for, add_qbs)
from strength_beta_lab.refine_strength_beta import history_penalty


class RefinementTests(unittest.TestCase):
    def test_history_reduction_transfers_prior_influence_to_current_evidence(self):
        n = np.array([40., 80., 120., 200.])
        for prior in [175., 75.]:
            adjusted = history_penalty(n, prior, .9)
            np.testing.assert_allclose(adjusted/(n+adjusted), .9*prior/(n+prior))
            self.assertTrue(np.all(n/(n+adjusted) > n/(n+prior)))
            self.assertEqual(history_penalty(np.array([0.]), prior, .9)[0], prior)

    def test_neutral_stadium_overrides_designated_home(self):
        schedule = pd.DataFrame({'stadium': ['Tottenham Hotspur Stadium', 'AT&T Stadium', 'Wembley Stadium'],
                                 'location': ['Home', 'Home', 'Neutral']})
        result = correct_venues(schedule)
        self.assertEqual(list(result.location), ['Neutral', 'Home', 'Neutral'])
        self.assertEqual(schedule.iloc[0].location, 'Home')

    def test_offense_carries_more_history_and_changes_reduce_only_relevant_units(self):
        previous = pd.DataFrame([{'week': 18, 'gameday': '2025-12-31', 'home_team': 'BAL', 'away_team': 'BUF',
                                  'home_coach': 'Old', 'away_coach': 'Same', 'home_qb_id': 'oldqb', 'away_qb_id': 'sameqb'}])
        current = pd.DataFrame([{'week': 1, 'gameday': '2026-09-01', 'home_team': 'BAL', 'away_team': 'BUF',
                                 'home_coach': 'New', 'away_coach': 'Same', 'home_qb_id': 'newqb', 'away_qb_id': 'sameqb'},
                                {'week': 2, 'gameday': '2026-09-08', 'home_team': 'BAL', 'away_team': 'BUF',
                                 'home_coach': 'Future', 'away_coach': 'Same', 'home_qb_id': 'backup', 'away_qb_id': 'replacement'}])
        off, defense, flags = continuity(current, previous, 1, Experiment('a', 'a'))
        i, j = TEAMS.index('BAL'), TEAMS.index('BUF')
        self.assertAlmostEqual(off[i], .8 * .65 * .6)
        self.assertAlmostEqual(defense[i], .4 * .65)
        self.assertEqual(flags['BAL']['head_coach'], 'New')
        self.assertAlmostEqual(off[j], .8)
        self.assertAlmostEqual(defense[j], .4)
        off2, _, flags2 = continuity(current, previous, 2, Experiment('a', 'a'))
        self.assertFalse(flags2['BUF']['new_opening_qb'])
        self.assertAlmostEqual(off2[j], .8)

    def test_future_plays_cannot_change_current_fit(self):
        rows = pd.DataFrame({'phase': ['dropback'] * 3, 'week': [1, 1, 2], 'weight': [1.] * 3,
                             'epa': [.2, -.1, 1000.], 'success': [1., 0., 1.],
                             'posteam': ['BAL', 'BUF', 'BAL'], 'defteam': ['BUF', 'BAL', 'BUF'], 'venue': [1., -1., 1.]})
        args = ('dropback', 1, Experiment('a', 'a'), np.zeros((32, 2, 2)), [np.full(32, .8), np.full(32, .4)])
        a = fit_phase(rows, *args)[0]
        rows.loc[2, 'epa'] = -1000.
        rows.loc[2, 'success'] = 0.
        np.testing.assert_array_equal(a, fit_phase(rows, *args)[0])

    def test_temporary_backup_does_not_reset_default_starter_history(self):
        previous = pd.DataFrame([{'week': 18, 'gameday': '2025-12-31', 'home_team': 'BAL', 'away_team': 'BUF',
                                  'home_coach': 'Same', 'away_coach': 'Same', 'home_qb_id': 'starter', 'away_qb_id': 'sameqb'}])
        current = previous.copy(); current['week'] = 1; current['home_qb_id'] = 'temporary'
        off, _, flags = continuity(current, previous, 1, Experiment('a', 'a'), {'BAL': 'starter'})
        self.assertFalse(flags['BAL']['new_opening_qb'])
        self.assertAlmostEqual(off[TEAMS.index('BAL')], .8)

    def test_unit_specific_preseason_carry_is_centered(self):
        prior = np.zeros((32, 2, 2)); prior[0, 0, 0] = .2; prior[0, 1, 0] = .2
        rows = pd.DataFrame(columns=['phase', 'week'])
        units, _, _ = fit_phase(rows, 'dropback', 0, Experiment('a', 'a'), prior, [np.full(32, .8), np.full(32, .4)])
        self.assertAlmostEqual(units[0, 0, 0], 2 * units[0, 1, 0])
        np.testing.assert_allclose(units.mean(axis=0), 0., atol=1e-15)

    def test_recovery_luck_does_not_erase_expected_fumble_cost(self):
        rows = pd.DataFrame({'epa': [-5., -1., .2], 'success': [0., 0., 1.], 'fumble_lost': [1., 0., 0.],
                             'offensive_fumble': [True, True, False], 'phase': ['dropback'] * 3})
        result = stabilize(rows, {'loss_rates': {'dropback': .5}, 'turnover_cost': 4.})
        np.testing.assert_allclose(result.stable_epa, [-3., -3., .2])
        self.assertAlmostEqual(result.fumble_adjustment.sum(), 0.)
        self.assertTrue((result.stable_epa[:2] < 0).all())

    def test_qb_priors_use_past_roles_and_do_not_read_future_performance(self):
        records = []
        for qb, epa in [('star', .3), ('backup', -.3)]:
            for week in [1, 2]:
                records.append({'qb_id': qb, 'posteam': 'BAL', 'week': week, 'season': 2025,
                                'relative_epa': epa, 'cpoe': 1., 'weight': 60., 'rush_value': .01})
        history = {2025: pd.DataFrame(records)}
        current = pd.DataFrame([{'qb_id': 'new', 'posteam': 'BAL', 'week': 1, 'season': 2026,
                                 'relative_epa': -.2, 'cpoe': -2., 'weight': 30., 'rush_value': 0.},
                                {'qb_id': 'new', 'posteam': 'BAL', 'week': 2, 'season': 2026,
                                 'relative_epa': 1000., 'cpoe': 1000., 'weight': 30., 'rush_value': 1000.}])
        games = {2024: pd.DataFrame({'home_qb_id': ['star'] * 9, 'away_qb_id': ['other'] * 9}),
                 2025: pd.DataFrame({'home_qb_id': ['star'] * 9, 'away_qb_id': ['other'] * 9})}
        draft = {'unseen': {'season': 2026, 'pick': 5}, 'new': {'season': 2026, 'pick': 100}}
        first = {'star': 2020, 'backup': 2020, 'new': 2026}
        a, priors = refined_qb_skills(history, current, 2026, 1, games, draft, first)
        current.loc[1, 'relative_epa'] = -1000.
        b, _ = refined_qb_skills(history, current, 2026, 1, games, draft, first)
        pd.testing.assert_frame_equal(a, b)
        self.assertGreater(priors['established_starter']['epa'], priors['experienced_backup']['epa'])
        self.assertEqual(a.loc['star', 'prior_plays'], 75.)
        self.assertEqual(a.loc['backup', 'prior_plays'], 200.)
        self.assertEqual(skill_for(a, 'unseen', priors)['prior_group'], 'rookie_early')

    def test_qb_replaces_embedded_contribution_including_rushing(self):
        table = pd.DataFrame(index=TEAMS)
        embedded = np.tile([.1, 2., .02], (32, 1))
        skills = pd.DataFrame({'epa': [.1, -.2], 'cpoe': [2., -3.], 'rush': [.02, -.01],
                               'effective_dropbacks': [300., 50.]}, index=['star', 'backup'])
        starters = {t: {'id': 'star'} for t in TEAMS}
        priors = {'epa': 0., 'cpoe': 0., 'rush': 0.}
        result = add_qbs(table, embedded, skills, priors, starters)
        np.testing.assert_allclose(result.to_numpy(), 0.)
        starters['BAL'] = {'id': 'backup'}
        result = add_qbs(table, embedded, skills, priors, starters)
        np.testing.assert_allclose(result.loc['BAL'], [-.3, -5., -.03])


if __name__ == '__main__':
    unittest.main()
