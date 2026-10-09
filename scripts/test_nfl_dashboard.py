"""Regression checks for complete-week ratings and honest forecast archiving."""
import unittest
from copy import deepcopy
import pandas as pd
from update_nfl_dashboard import add_forecasts, completed_cutoff, archived_before_game


class NFLDashboardTests(unittest.TestCase):
    def schedule(self):
        return pd.DataFrame([{'game_id':'2026_05_TB_DAL','season':2026,'game_type':'REG','week':5,
            'gameday':'2026-10-08','gametime':'20:15','home_team':'DAL','away_team':'TB',
            'location':'Home','home_score':None,'away_score':None}])

    def teams(self):
        return {'DAL':{'strength':0.,'expected_qb':{'id':'dak','name':'Dak'}},
                'TB':{'strength':-1.,'expected_qb':{'id':'baker','name':'Baker'}}}

    def test_partial_week_does_not_advance_rating_cutoff(self):
        games=pd.DataFrame({'season':[2026]*4,'game_type':['REG']*4,'week':[1,1,2,2],
                            'home_score':[10.,20.,12.,None],'away_score':[3.,15.,6.,None]})
        cutoff,selected=completed_cutoff(games,2026)
        self.assertEqual(cutoff,1);self.assertEqual(len(selected),2)
        with self.assertRaises(ValueError):completed_cutoff(games,2026,2)

    def test_forecasts_are_preserved_and_post_kickoff_updates_are_blocked(self):
        games=self.schedule();teams=self.teams()
        before=add_forecasts([],games,teams,1.5,4,'2026-10-06T12:00:00+00:00')
        frozen=deepcopy(before);teams['DAL']['strength']=5.
        after=add_forecasts(before,games,teams,1.5,4,'2026-10-09T12:00:00+00:00')
        self.assertEqual(before,frozen);self.assertEqual(after,frozen)
        self.assertTrue(archived_before_game(before[0],next(games.itertuples())))

    def test_revised_pregame_forecast_appends_without_rewriting_original(self):
        games=self.schedule();teams=self.teams()
        before=add_forecasts([],games,teams,1.5,4,'2026-10-06T12:00:00+00:00')
        frozen=deepcopy(before);teams['DAL']['strength']=1.
        after=add_forecasts(before,games,teams,1.5,4,'2026-10-07T12:00:00+00:00')
        self.assertEqual(before,frozen);self.assertEqual(after[0],frozen[0]);self.assertEqual(len(after),2)
        repeated=add_forecasts(after,games,teams,1.5,4,'2026-10-07T13:00:00+00:00')
        self.assertEqual(repeated,after)

    def test_eastern_kickoff_is_compared_in_utc(self):
        game=next(self.schedule().itertuples())
        self.assertTrue(archived_before_game({'generated_at':'2026-10-09T00:14:59+00:00','rating_week':4},game))
        self.assertFalse(archived_before_game({'generated_at':'2026-10-09T00:15:00+00:00','rating_week':4},game))


if __name__=='__main__':unittest.main()
