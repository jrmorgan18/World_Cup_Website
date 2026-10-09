"""Retrieve supplemental public inputs, preserving the original beta snapshots."""
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fetch_strength_beta_inputs import fetch

EXTRAS = ['game_id', 'play_id', 'epa', 'fumble', 'fumbled_1_team',
          'fumbled_2_team', 'fumble_lost', 'qb_epa']


def main():
    base = Path(tempfile.gettempdir()) / 'dual-eights-strength-beta'
    target = base / 'refinement'
    target.mkdir(exist_ok=True)
    tasks = [(f'pbp-extra-{year}.parquet', f'pbp/play_by_play_{year}.parquet', EXTRAS)
             for year in range(2016, 2027)]
    tasks.append(('draft_picks.parquet', 'draft_picks/draft_picks.parquet',
                  ['season', 'round', 'pick', 'gsis_id', 'position']))
    def retrieve(task):
        return fetch(target, task[0], task[1], columns=task[2])
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(retrieve, tasks))
    (target / 'manifest.json').write_text(json.dumps(records, indent=2)+'\n', encoding='utf-8')
    print(f'Saved {len(records)} additional public source snapshots', flush=True)


if __name__ == '__main__':
    main()
