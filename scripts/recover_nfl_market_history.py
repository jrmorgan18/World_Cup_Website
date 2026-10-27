"""Recover only verifiable pregame quotes from published-branch Git history.

Run manually in a full-history checkout; scheduled updates append new observations.
"""
import argparse
import json
from pathlib import Path
import subprocess
from nfl_market_history import observations_from_dashboard, merge_observations


def recover(root, ref):
    path = '_data/nfl_dashboard.json'
    log = subprocess.check_output(['git','log','--format=%H %cI',ref,'--',path],cwd=root,text=True)
    observations = []
    for item in log.splitlines():
        revision, recorded = item.split(' ',1)
        raw = subprocess.check_output(['git','show',revision+':'+path],cwd=root)
        data = json.loads(raw)
        observations += observations_from_dashboard(data,recorded,revision)
    target = root/'_data/nfl_market_archive.json'
    existing = json.loads(target.read_text())['observations'] if target.exists() else []
    result = {'observations':merge_observations(existing,observations)}
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(f"Recovered {len(result['observations'])} pregame quote/forecast observations from {len(log.splitlines())} published snapshots.")


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref',default='origin/main')
    args=parser.parse_args()
    recover(Path(__file__).resolve().parents[1],args.ref)
