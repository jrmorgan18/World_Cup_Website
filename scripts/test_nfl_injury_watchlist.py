import unittest
import pandas as pd
from update_nfl_injury_watchlist import build,risk,group_for

class InjuryWatchlistTests(unittest.TestCase):
    def fixture(self):
        players=pd.DataFrame([{'pfr_id':p,'gsis_id':p} for p in ['one','two']])
        snaps=pd.DataFrame([{'season':2026,'week':w,'team':'BAL','pfr_player_id':p,'position':'CB','offense_pct':0.,'defense_pct':share} for p in ['one','two'] for w,share in [(1,1.),(2,1.),(3,0.)]])
        injury=pd.DataFrame([{'season':2026,'week':w,'team':'BAL','gsis_id':p,'full_name':p,'position':'CB','report_status':'Out' if w==3 else None,'practice_status':'Did Not Participate In Practice' if w==3 else 'Full Participation in Practice'} for p in ['one','two'] for w in [3,4]])
        schedule=pd.DataFrame([{'season':2026,'week':4,'game_type':'REG','home_team':'BAL','away_team':'CLE'}])
        depth=pd.DataFrame(columns=['dt','team','gsis_id','pos_rank'])
        return injury,snaps,players,schedule,depth
    def run_build(self,inputs,week=4):
        return build(*inputs,2026,week,'2026-10-16T12:00:00Z',{'groups':[]},[],{'url':'https://example.org','fetched_at':'2026-10-16T11:00:00Z'})
    def test_missing_reports_are_unknown_not_healthy(self):
        result=self.run_build(self.fixture(),week=5)
        self.assertEqual(result['cards'],[])
        # Teams without a scheduled game are marked Bye, never Healthy.
        self.assertFalse(any('healthy' in t['coverage'].lower() for t in result['teams']))
        self.assertEqual(len(result['teams']),32)
    def test_unavailable_optional_injury_feed_does_not_break_the_model_refresh(self):
        inputs=list(self.fixture());inputs[0]=pd.DataFrame(columns=['team','week','gsis_id'])
        result=self.run_build(inputs)
        self.assertEqual(result['cards'],[])
        self.assertEqual(next(t for t in result['teams'] if t['team']=='BAL')['coverage'],'No current-week report')
    def test_multiple_possible_returns_remain_explicit_candidates(self):
        result=self.run_build(self.fixture())
        card=result['cards'][0]
        self.assertEqual(card['state'],'Potential improvement');self.assertFalse(card['reviewed'])
        self.assertTrue(all(p['return_candidate'] for p in card['players']))
        self.assertTrue(all(p['healthy_share']==1. for p in card['players']))
    def test_future_participation_cannot_change_prior_roles(self):
        inputs=list(self.fixture());before=self.run_build(inputs)
        future=inputs[1].iloc[[0]].copy();future['week']=5;future['defense_pct']=.05
        inputs[1]=pd.concat([inputs[1],future],ignore_index=True)
        self.assertEqual(before,self.run_build(inputs))
    def test_rest_and_qbs_do_not_become_non_qb_cluster_flags(self):
        self.assertIsNone(risk({'practice_primary_injury':'Rest','practice_status':'Did Not Participate In Practice'}))
        self.assertIsNone(group_for('QB'));self.assertEqual(group_for('OLB'),'FRONT')
    def test_unmapped_identity_does_not_fabricate_a_healthy_role(self):
        inputs=list(self.fixture());inputs[2]=inputs[2].iloc[:0]
        result=self.run_build(inputs)
        self.assertEqual(result['cards'],[])
        self.assertEqual(next(t for t in result['teams'] if t['team']=='BAL')['unresolved_participation_ids'],2)
    def test_generic_linebacker_snap_labels_use_precise_public_edge_role(self):
        inputs=list(self.fixture());inputs[1]['position']='LB';inputs[2]['pff_position']='ED'
        self.assertEqual(self.run_build(inputs)['cards'][0]['group'],'FRONT')

if __name__=='__main__':unittest.main()
