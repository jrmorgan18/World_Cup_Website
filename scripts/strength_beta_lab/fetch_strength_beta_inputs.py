"""Fetch public, keyless inputs for the local Team Strength Index beta."""
import argparse
import hashlib
import io
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import pandas as pd
import pyarrow.parquet as pq

from legacy_inputs import PBP_COLUMNS

BASE = "https://github.com/nflverse/nflverse-data/releases/download/"
COLUMNS = list(dict.fromkeys(PBP_COLUMNS + [
    "play_id", "game_date", "down", "ydstogo", "passer_player_id", "passer_player_name",
    "rusher_player_id", "rusher_player_name", "qb_scramble", "kicker_player_id", "punter_player_id",
]))


def fetch(cache, name, relative, refresh=False, columns=None):
    path = cache / name
    metadata = cache / (name + ".source.json")
    if path.exists() and metadata.exists() and not refresh:
        return json.loads(metadata.read_text(encoding="utf-8"))
    url = BASE + relative
    with urlopen(url, timeout=120) as response:
        modified = response.headers.get("Last-Modified")
        payload = response.read()
    if columns:
        available = pq.read_schema(io.BytesIO(payload)).names
        missing = set(columns) - set(available)
        if missing:
            raise ValueError(f"{name}: missing columns {sorted(missing)}")
        frame = pd.read_parquet(io.BytesIO(payload), columns=columns)
        frame.to_parquet(path, index=False)
    else:
        path.write_bytes(payload)
    record = {"file": name, "url": url, "fetched_at": datetime.now(timezone.utc).isoformat(),
              "http_last_modified": modified, "source_sha256": hashlib.sha256(payload).hexdigest(),
              "cache_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    metadata.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Retrieved {name}", flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path(tempfile.gettempdir()) / "dual-eights-strength-beta")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--start-season", type=int, default=2016)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    tasks = [(f"pbp-{year}.parquet", f"pbp/play_by_play_{year}.parquet", COLUMNS)
             for year in range(args.start_season, args.season + 1)]
    tasks += [("games.csv", "schedules/games.csv", None),
              ("depth_charts.parquet", f"depth_charts/depth_charts_{args.season}.parquet", None),
              ("injuries.parquet", f"injuries/injuries_{args.season}.parquet", None),
              ("snap_counts.parquet", f"snap_counts/snap_counts_{args.season}.parquet", None)]
    def task(item):
        return fetch(args.cache_dir, item[0], item[1], args.refresh, item[2])
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(task, tasks))
    (args.cache_dir / "manifest.json").write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(records)} source snapshots to {args.cache_dir}", flush=True)


if __name__ == "__main__":
    main()
