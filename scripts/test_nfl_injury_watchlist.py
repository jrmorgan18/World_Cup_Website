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
    def run_build(self,inputs,week=4,evidence=None,reviews=None):
        return build(*inputs,2026,week,'2026-10-16T18:00:00Z',{'groups':[]},reviews or [],{'url':'https://example.org','fetched_at':'2026-10-16T17:00:00Z'},evidence)
    def daily(self,statuses):
        return {'practice_reports':[{'season':2026,'week':4,'team':'BAL','report_date':day,
            'observed_at':day+'T16:00:00Z','source_url':'https://example.org/'+day,
            'players':[{'id':p,'name':p,'position':'CB','practice_status':status,'practice_primary_injury':'Ankle'} for p in ['one','two']]}
            for day,status in statuses]}
    def current_status(self,status=None,practice=None):
        inputs=list(self.fixture());current=inputs[0].week.eq(4)
        inputs[0].loc[current,'report_status']=status
        inputs[0].loc[current,'practice_status']=practice
        return inputs
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
    def test_returns_and_routine_statuses_do_not_populate_watchlist(self):
        self.assertEqual(self.run_build(self.fixture())['cards'],[])
        for status in ['Questionable','Doubtful',None]:
            for practice in ['DNP','LP','FP',None]:
                self.assertEqual(self.run_build(self.current_status(status,practice))['cards'],[])
    def test_confirmed_out_overrides_practice_and_preserves_healthy_role(self):
        card=self.run_build(self.current_status('Out','FP'))['cards'][0]
        self.assertEqual(card['state'],'Availability risk');self.assertFalse(card['reviewed'])
        self.assertTrue(all(p['status']=='Confirmed OUT' and p['healthy_share']==1. for p in card['players']))
    def test_two_dated_current_week_dnps_qualify(self):
        evidence=self.daily([('2026-10-14','DNP'),('2026-10-15','DNP')])
        card=self.run_build(self.current_status(None,'DNP'),evidence=evidence)['cards'][0]
        self.assertTrue(all(p['status']=='Two consecutive DNP reports' for p in card['players']))
        self.assertEqual(card['players'][0]['practice_dates'],['2026-10-14','2026-10-15'])
    def test_duplicate_fetch_or_missing_day_does_not_establish_streak(self):
        for dates in [[('2026-10-14','DNP'),('2026-10-14','DNP')],[('2026-10-13','DNP'),('2026-10-15','DNP')],[('2026-10-15','DNP')]]:
            self.assertEqual(self.run_build(self.current_status(None,'DNP'),evidence=self.daily(dates))['cards'],[])
    def test_later_limited_or_full_practice_clears_dnps(self):
        for status in ['LP','FP']:
            evidence=self.daily([('2026-10-14','DNP'),('2026-10-15','DNP'),('2026-10-16',status)])
            self.assertEqual(self.run_build(self.current_status(None,'DNP'),evidence=evidence)['cards'],[])
            evidence=self.daily([('2026-10-14','DNP'),('2026-10-15','DNP')])
            self.assertEqual(self.run_build(self.current_status(None,status),evidence=evidence)['cards'],[])
    def test_newly_fetched_old_report_cannot_override_latest_feed_return(self):
        evidence=self.daily([('2026-10-15','DNP'),('2026-10-16','DNP')])
        evidence['practice_reports'][-1]['observed_at']='2026-10-16T17:30:00Z'
        self.assertEqual(self.run_build(self.current_status(None,'LP'),evidence=evidence)['cards'],[])
    def test_return_interrupts_streak_and_new_single_dnp_does_not_restart_it(self):
        evidence=self.daily([('2026-10-14','DNP'),('2026-10-15','LP'),('2026-10-16','DNP')])
        self.assertEqual(self.run_build(self.current_status(None,'DNP'),evidence=evidence)['cards'],[])
    def test_missing_player_and_non_injury_dnps_do_not_count(self):
        evidence=self.daily([('2026-10-14','DNP'),('2026-10-15','DNP')])
        evidence['practice_reports'][-1]['players']=[]
        self.assertEqual(self.run_build(self.current_status(None,'DNP'),evidence=evidence)['cards'],[])
        evidence=self.daily([('2026-10-14','DNP'),('2026-10-15','DNP')])
        for report in evidence['practice_reports']:
            for player in report['players']:player['practice_primary_injury']='Rest'
        self.assertEqual(self.run_build(self.current_status(None,'DNP'),evidence=evidence)['cards'],[])
    def test_wrong_week_and_future_evidence_do_not_count(self):
        for change in ['week','observed_at']:
            evidence=self.daily([('2026-10-14','DNP'),('2026-10-15','DNP')])
            for report in evidence['practice_reports']:report[change]=3 if change=='week' else '2026-10-17T16:00:00Z'
            self.assertEqual(self.run_build(self.current_status(None,'DNP'),evidence=evidence)['cards'],[])
    def test_confirmed_ir_survives_practice_but_activation_clears_it(self):
        evidence={'roster_status':[{'season':2026,'week':4,'team':'BAL','id':p,'name':p,'position':'CB','status':'IR',
            'effective_at':'2026-10-14T12:00:00Z','observed_at':'2026-10-14T13:00:00Z','source_url':'https://example.org/ir'} for p in ['one','two']]}
        result=self.run_build(self.fixture(),evidence=evidence)
        self.assertTrue(all(p['status']=='Confirmed IR' for p in result['cards'][0]['players']))
        evidence['roster_status'] += [{**r,'status':'Active','effective_at':'2026-10-16T12:00:00Z','observed_at':'2026-10-16T13:00:00Z'} for r in evidence['roster_status']]
        self.assertEqual(self.run_build(self.fixture(),evidence=evidence)['cards'],[])
    def test_ir_players_missing_from_weekly_feed_are_still_screened(self):
        evidence={'roster_status':[{'season':2026,'week':4,'team':'BAL','id':p,'name':p,'position':'CB','status':'IR',
            'effective_at':'2026-10-14T12:00:00Z','observed_at':'2026-10-14T13:00:00Z','source_url':'https://example.org/ir'} for p in ['one','two']]}
        inputs=list(self.fixture());inputs[0]=inputs[0].iloc[:0]
        self.assertEqual(len(self.run_build(inputs,evidence=evidence)['cards']),1)
    def test_one_eligible_player_cannot_form_cluster_with_limited_teammate(self):
        inputs=self.current_status('Out','FP');inputs[0].loc[inputs[0].gsis_id.eq('two'),'report_status']='Questionable'
        self.assertEqual(self.run_build(inputs)['cards'],[])
    def test_reviews_cannot_bypass_filter_or_reintroduce_players(self):
        review={'season':2026,'week':4,'team':'BAL','group':'DB','players':[{'id':'fake'}],'state':'Improving',
            'summary':'Reviewed','observed_at':'2026-10-16T12:00:00Z','sources':[{'title':'Club','url':'https://example.org'}]}
        self.assertEqual(self.run_build(self.fixture(),reviews=[review])['cards'],[])
        card=self.run_build(self.current_status('Out','FP'),reviews=[review])['cards'][0]
        self.assertTrue(card['reviewed']);self.assertEqual([p['id'] for p in card['players']],['one','two'])
        self.assertEqual(card['state'],'Availability risk')
    def test_future_participation_cannot_change_prior_roles(self):
        inputs=self.current_status('Out','FP');before=self.run_build(inputs)
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
        inputs=self.current_status('Out','FP');inputs[1]['position']='LB';inputs[2]['pff_position']='ED'
        self.assertEqual(self.run_build(inputs)['cards'][0]['group'],'FRONT')

if __name__=='__main__':unittest.main()
