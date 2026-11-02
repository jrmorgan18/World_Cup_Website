from copy import deepcopy
import unittest
from nfl_rating_reviews import apply_rating_reviews


class RatingReviewTests(unittest.TestCase):
    def teams(self):
        return [{'abbr':abbr,'strength':points,'rank':i+1,'previous_week_beta_rank':i+1,
            'weekly_rank_change':0,'defense_points':0.,'offense_points':points,'st_points':0.,'qb_points':0.,
            'efficiency':60.,'components':{'pass_offense':points,'pass_defense':0.}}
            for i,(abbr,points) in enumerate([('BUF',6.),('LA',5.7),('BAL',-1.)])]

    def review(self,**changes):
        return {'id':'buf-week8','season':2026,'reference_week':8,'game_id':'2026_08_BAL_BUF',
            'team':'BUF','component':'defense','points':-.5,'half_life_weeks':8,
            'observed_at':'2026-11-02T18:00:00+00:00','summary':'Reviewed QB mismatch.',
            'sources':[{'title':'Team report','url':'https://example.com/report'}],**changes}

    def apply(self,teams,review=None,week=8,exposure=None,completed=None,season=2026):
        return apply_rating_reviews(teams,{'reviews':[review or self.review()]},season,week,
            {'2026_08_BAL_BUF'} if completed is None else completed,
            {('BUF',8):100.} if exposure is None else exposure,'2026-11-02T19:00:00+00:00')

    def test_only_bills_points_and_defense_change_with_rank_swap_and_no_recentering(self):
        teams=self.teams(); before=deepcopy(teams)
        self.apply(teams)
        self.assertEqual([t['abbr'] for t in teams],['LA','BUF','BAL'])
        buf=next(t for t in teams if t['abbr']=='BUF')
        self.assertEqual((buf['strength'],buf['defense_points'],buf['efficiency']),(5.5,-.5,60.))
        self.assertEqual(buf['weekly_rank_change'],-1)
        for abbr in ['LA','BAL']:
            new=next(t for t in teams if t['abbr']==abbr);old=next(t for t in before if t['abbr']==abbr)
            self.assertEqual(new['strength'],old['strength']);self.assertEqual(new['components'],old['components'])
        self.assertAlmostEqual(sum(t['strength'] for t in teams),sum(t['strength'] for t in before)-.5)
        self.assertEqual(buf['strength'],sum(buf[k] for k in ['offense_points','defense_points','st_points','qb_points']))

    def test_review_dilutes_with_new_plays_but_not_future_plays_or_a_bye(self):
        teams=self.teams();self.apply(teams,week=9,exposure={('BUF',8):100.,('BUF',10):10000.})
        self.assertAlmostEqual(next(t for t in teams if t['abbr']=='BUF')['rating_review_points'],-.5)
        teams=self.teams();self.apply(teams,week=9,exposure={('BUF',8):100.,('BUF',9):100.})
        correction=next(t for t in teams if t['abbr']=='BUF')['rating_review_points']
        self.assertGreater(correction,-.5);self.assertLess(correction,0.)

    def test_refresh_is_idempotent_and_prior_weeks_or_next_seasons_are_not_rewritten(self):
        teams=self.teams();self.apply(teams);once=deepcopy(teams);self.apply(teams)
        self.assertEqual(teams,once)
        for options in [{'week':7},{'season':2027}]:
            teams=self.teams();self.apply(teams,**options)
            self.assertFalse(any('rating_review_points' in t for t in teams))

    def test_missing_game_exposure_sources_and_future_observations_fail_closed(self):
        for changes in [{'sources':[]},{'observed_at':'2026-11-03T18:00:00+00:00'},
            {'team':'XYZ'},{'points':float('nan')},{'component':'offense'}]:
            with self.assertRaises(ValueError):self.apply(self.teams(),self.review(**changes))
        with self.assertRaises(ValueError):self.apply(self.teams(),completed=set())
        with self.assertRaises(ValueError):self.apply(self.teams(),exposure={})


if __name__=='__main__':
    unittest.main()
