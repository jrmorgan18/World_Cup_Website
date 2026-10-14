"""Regression checks for complete-week ratings and honest forecast archiving."""
import unittest
from copy import deepcopy
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import update_nfl_dashboard as dashboard
from update_nfl_dashboard import (add_forecasts, completed_cutoff, archived_before_game,
    actual_starter_adjustment, reconcile_completed_qbs, model_for_rating,
    model_for_forecast, publication_is_frozen, preserve_previous_published_ranks)


class NFLDashboardTests(unittest.TestCase):
    def production_config(self):
        return json.loads((Path(__file__).parent/'nfl_model_config.json').read_text())

    def test_refit_activates_after_week_six_and_preserves_legacy_forecasts(self):
        config = self.production_config()
        legacy = config['previous_model']
        self.assertIs(model_for_rating(config,2026,5),legacy)
        self.assertIs(model_for_rating(config,2026,6),config)
        self.assertIs(model_for_rating(config,2027,0),config)
        self.assertIs(model_for_forecast(config,{'rating_week':5},2026,5),legacy)
        self.assertIs(model_for_forecast(config,{'model_id':legacy['model_id']},2026,8),legacy)
        self.assertIs(model_for_forecast(config,{'model_id':config['model_id']},2026,6),config)
        with self.assertRaises(ValueError):
            model_for_forecast(config,{'model_id':'unknown'},2026,6)
        self.assertTrue(publication_is_frozen(config,2026,5,True))
        self.assertTrue(publication_is_frozen(config,2026,6,False))
        self.assertFalse(publication_is_frozen(config,2026,6,True))
        self.assertFalse(publication_is_frozen(config,2026,7,False))

    def test_frozen_refresh_never_writes_published_data_or_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); cache = root/'cache'; cache.mkdir()
            (root/'scripts').mkdir()
            (root/'scripts/nfl_model_config.json').write_text(json.dumps(self.production_config()))
            paths = ['_data/nfl_dashboard.json','_data/nfl_forecast_archive.json',
                'assets/data/nfl-dashboard.json','assets/data/nfl-rankings.csv','assets/data/nfl-results.csv']
            for name in paths:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(b'published Week 5 bytes\n')
            games=pd.DataFrame([{'season':2026,'game_type':'REG','week':w,
                'home_score':10.,'away_score':3.} for w in range(1,6)])
            games.to_csv(cache/'games.csv',index=False)
            with patch.object(dashboard,'ROOT',root), patch.object(dashboard,'RefinedBuilder') as builder, patch.object(dashboard,'atomic_json') as writer:
                dashboard.build(cache,2026,None)
                games.loc[len(games)]={'season':2026,'game_type':'REG','week':6,'home_score':None,'away_score':None}
                games.loc[len(games)]={'season':2026,'game_type':'REG','week':6,'home_score':13.,'away_score':7.}
                games.to_csv(cache/'games.csv',index=False)
                dashboard.build(cache,2026,6,allow_partial=True)
                builder.assert_not_called();writer.assert_not_called()
            for name in paths:
                self.assertEqual((root/name).read_bytes(),b'published Week 5 bytes\n')

    def test_refit_scale_is_applied_once_and_home_advantage_is_not_compressed(self):
        config=self.production_config()
        self.assertEqual(config['experiment']['margin_penalty'],360.)
        self.assertEqual(config['point_multiplier'],.85)
        self.assertEqual(config['coefficient_fit_through'],2023)
        self.assertEqual(set(config['coefficients']),set(config['previous_model']['coefficients']))
        self.assertFalse(any(k.startswith('drive') for k in config['coefficients']))
        for name,raw in config['fit']['raw_coefficients'].items():
            expected=raw if name=='home_advantage' else raw*.85
            self.assertAlmostEqual(config['coefficients'][name],expected,places=12)
        game=type('Game',(),{'home_team':'DAL','away_team':'TB','home_qb_id':'dak','away_qb_id':'backup'})()
        snapshot={'skills':pd.DataFrame.from_dict({'dak':{'epa':.2},'baker':{'epa':.3},'backup':{'epa':-.1}},orient='index'),'priors':{}}
        assumed={'DAL':{'id':'dak'},'TB':{'id':'baker'}}
        legacy=model_for_forecast(config,None,2026,5)
        old_adjustment,_=actual_starter_adjustment(game,assumed,snapshot,['qb_epa_delta'],[legacy['coefficients']['qb_epa_delta']])
        new_adjustment,_=actual_starter_adjustment(game,assumed,snapshot,['qb_epa_delta'],[config['coefficients']['qb_epa_delta']])
        self.assertAlmostEqual(old_adjustment,.4*18.959105807753335)
        self.assertNotEqual(old_adjustment,new_adjustment)

    def test_weekly_movement_uses_actual_published_ranks_across_method_change(self):
        previous={'season':2026,'rating_week':5,'teams':[{'abbr':'SEA','rank':10}]}
        teams=[{'abbr':'SEA','rank':7,'previous_week_beta_rank':8,'weekly_rank_change':1}]
        preserve_previous_published_ranks(teams,previous,2026,6)
        self.assertEqual(teams[0]['previous_week_beta_rank'],10)
        self.assertEqual(teams[0]['weekly_rank_change'],3)
        unchanged=deepcopy(teams)
        preserve_previous_published_ranks(teams,previous,2026,7)
        self.assertEqual(teams,unchanged)

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

    def test_manual_partial_week_uses_only_final_games(self):
        games=pd.DataFrame({'season':[2026]*4,'game_type':['REG']*4,'week':[1,1,2,2],
            'home_score':[10.,20.,12.,None],'away_score':[3.,15.,6.,None]})
        cutoff,selected=completed_cutoff(games,2026,2,allow_partial=True)
        self.assertEqual(cutoff,2);self.assertEqual(len(selected),3)
        games.loc[0,'home_score']=None
        with self.assertRaises(ValueError):completed_cutoff(games,2026,2,allow_partial=True)

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

    def test_completed_qb_is_verified_against_pbp_without_picking_later_relief_qb(self):
        games=pd.DataFrame([{'game_id':'g','home_team':'SEA','away_team':'SF','home_score':29,'away_score':32,
            'home_qb_id':'lock','home_qb_name':'Drew Lock','away_qb_id':'purdy','away_qb_name':'Brock Purdy'}])
        plays=pd.DataFrame([{'game_id':'g','posteam':'SEA','qb_dropback':1,'passer_player_id':q,'play_id':n}
            for q,n in [('receiver',1),('darnold',2),('lock',3),('lock',4)]])
        corrected,changes=reconcile_completed_qbs(games,plays,{'lock':'Drew Lock','darnold':'Sam Darnold','purdy':'Brock Purdy'})
        self.assertEqual(corrected.iloc[0].home_qb_id,'darnold')
        self.assertEqual(corrected.iloc[0].home_qb_name,'Sam Darnold')
        self.assertEqual(len(changes),1);self.assertEqual(games.iloc[0].home_qb_id,'lock')
        self.assertEqual(actual_starter_adjustment(next(corrected.itertuples()),{'SEA':{'id':'darnold'},'SF':{'id':'purdy'}},{'skills':pd.DataFrame(),'priors':{}},['qb_epa_delta'],[10.]),(0.,False))
        games.loc[0,'home_score']=None
        unchanged,changes=reconcile_completed_qbs(games,plays,{'lock':'Drew Lock','darnold':'Sam Darnold'})
        self.assertEqual(unchanged.iloc[0].home_qb_id,'lock');self.assertFalse(changes)

    def test_actual_starter_replacement_uses_cutoff_skills_and_home_away_signs(self):
        from types import SimpleNamespace
        game=SimpleNamespace(home_team='DAL',away_team='TB',home_qb_id='dak',away_qb_id='backup')
        snapshot={'skills':pd.DataFrame.from_dict({'dak':{'epa':.2,'cpoe':0.,'rush':0.},
            'baker':{'epa':.3,'cpoe':0.,'rush':0.},'backup':{'epa':-.1,'cpoe':0.,'rush':0.}},orient='index'),'priors':{}}
        assumed={'DAL':{'id':'dak'},'TB':{'id':'baker'}}
        adjustment,changed=actual_starter_adjustment(game,assumed,snapshot,['qb_epa_delta'],[10.])
        self.assertTrue(changed);self.assertAlmostEqual(adjustment,4.)
        game.home_qb_id='backup';game.away_qb_id='baker'
        adjustment,changed=actual_starter_adjustment(game,assumed,snapshot,['qb_epa_delta'],[10.])
        self.assertTrue(changed);self.assertAlmostEqual(adjustment,-3.)
        game.home_qb_id='dak'
        self.assertEqual(actual_starter_adjustment(game,assumed,snapshot,['qb_epa_delta'],[10.]),(0.,False))

    def test_eastern_kickoff_is_compared_in_utc(self):
        game=next(self.schedule().itertuples())
        self.assertTrue(archived_before_game({'generated_at':'2026-10-09T00:14:59+00:00','rating_week':4},game))
        self.assertFalse(archived_before_game({'generated_at':'2026-10-09T00:15:00+00:00','rating_week':4},game))


if __name__=='__main__':unittest.main()
