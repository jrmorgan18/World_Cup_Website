import unittest
from copy import deepcopy
from nfl_market_history import observations_from_dashboard, merge_observations, eligible_observations, attach_market_history


class MarketHistoryTests(unittest.TestCase):
    def game(self, **changes):
        return {'game_id':'2026_07_A_B','status':'Upcoming','forecast_kind':'saved',
            'forecast_generated_at':'2026-10-20T12:00:00+00:00','forecast_home_margin':9.,
            'kickoff_utc':'2026-10-25T17:00:00+00:00','market_home_margin':7.,
            'market_retrieved_at':'2026-10-20T11:59:30+00:00',**changes}

    def test_same_build_quote_qualifies_but_postkickoff_commit_does_not(self):
        data={'generated_at':'2026-10-20T12:00:00+00:00','games':[self.game()]}
        rows=observations_from_dashboard(data)
        self.assertEqual(len(rows),1)
        self.assertEqual(eligible_observations(self.game(status='Final'),rows),rows)
        self.assertEqual(observations_from_dashboard(data,'2026-10-26T12:00:00+00:00'),[])

    def test_finals_missing_quotes_and_invalid_timing_cannot_backfill_pregame_history(self):
        for change in [{'status':'Final'},{'market_home_margin':None},{'market_home_margin':float('nan')},
            {'market_retrieved_at':'2026-10-21T12:00:00+00:00'}, {'forecast_kind':'retrospective'},
            {'forecast_generated_at':'2026-10-21T12:00:00+00:00'},{'kickoff_utc':None}]:
            self.assertEqual(observations_from_dashboard({'games':[self.game(**change)]},'2026-10-20T12:01:00+00:00'),[])

    def test_forecast_revisions_cannot_borrow_earlier_prices_or_adjusted_qb_predictions(self):
        rows=observations_from_dashboard({'games':[self.game()]},'2026-10-20T12:01:00+00:00')
        self.assertEqual(eligible_observations(self.game(forecast_generated_at='2026-10-21T12:00:00+00:00'),rows),[])
        self.assertEqual(eligible_observations(self.game(forecast_home_margin=10.),rows),[])
        self.assertEqual(len(eligible_observations(self.game(display_home_margin=5.,lineup_changed=True),rows)),1)
        self.assertEqual(eligible_observations(self.game(forecast_kind='retrospective'),rows),[])

    def test_repeated_snapshot_is_deduplicated_without_mutating_original(self):
        rows=observations_from_dashboard({'games':[self.game()]},'2026-10-20T12:01:00+00:00')
        before=deepcopy(rows)
        later=observations_from_dashboard({'games':[self.game()]},'2026-10-20T13:00:00+00:00')
        self.assertEqual(merge_observations(rows,later),rows)
        self.assertEqual(rows,before)
        self.assertEqual(attach_market_history({'games':[self.game()]},rows)['games'][0]['market_history'],rows)

    def test_deduplication_compares_real_utc_time_across_offsets(self):
        rows=observations_from_dashboard({'games':[self.game()]},'2026-10-20T12:01:00+00:00')
        later=deepcopy(rows);later[0]['recorded_at']='2026-10-20T08:02:00-04:00'
        self.assertEqual(merge_observations(later,rows),rows)


if __name__=='__main__':
    unittest.main()
