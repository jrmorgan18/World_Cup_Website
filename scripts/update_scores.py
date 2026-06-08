#!/usr/bin/env python3
"""Update _data/schedule.json with live group-stage scores.

Pulls finished group-stage results from football-data.org and writes
home_score / away_score / status onto the matching fixtures. The site's
standings tables (computed client-side) then reflect the new results on
the next GitHub Pages build.

Behaviour:
  * Needs the FOOTBALL_DATA_API_KEY env var (a free football-data.org key).
    Without it, the script exits 0 without changes — so the workflow is a
    harmless no-op until the key is added as a repo secret.
  * Only runs inside the tournament window (June 10 – July 20, 2026).
  * Matches fixtures by unordered team pair, so it is robust to home/away
    orientation differences.
  * Scores can also be edited by hand in _data/schedule.json at any time.
"""
import json
import os
import sys
import unicodedata
import urllib.request
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEDULE = os.path.join(ROOT, "_data", "schedule.json")
API_URL = "https://api.football-data.org/v4/competitions/WC/matches?stage=GROUP_STAGE"

# Canonical-key aliases (applied after accent/punctuation stripping) so the
# API's team names line up with the names used on the site.
ALIASES = {
    "korearepublic": "southkorea",
    "iriran": "iran",
    "cotedivoire": "ivorycoast",
    "caboverde": "capeverde",
    "turkey": "turkiye",
    "congodr": "drcongo",
    "congo": "drcongo",
    "usa": "unitedstates",
    "unitedstatesofamerica": "unitedstates",
    "bosniaherzegovina": "bosniaandherzegovina",
}


def canon(name):
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = "".join(c for c in s.lower() if c.isalnum())
    return ALIASES.get(s, s)


def in_window():
    today = date.today()
    return date(2026, 6, 10) <= today <= date(2026, 7, 20)


def fetch(key):
    req = urllib.request.Request(API_URL, headers={"X-Auth-Token": key})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()
    if not key:
        print("No FOOTBALL_DATA_API_KEY set — skipping (no changes).")
        return 0
    if not in_window():
        print("Outside tournament window — skipping.")
        return 0

    with open(SCHEDULE, encoding="utf-8") as f:
        data = json.load(f)
    # index our fixtures by unordered canonical team pair
    index = {}
    for m in data["matches"]:
        index[frozenset((canon(m["home"]), canon(m["away"])))] = m

    try:
        api = fetch(key)
    except Exception as e:  # network/auth/etc. — never fail the build
        print("API fetch failed (%s) — skipping." % e)
        return 0

    changed = 0
    for am in api.get("matches", []):
        status = am.get("status")
        ft = (am.get("score") or {}).get("fullTime") or {}
        hs, as_ = ft.get("home"), ft.get("away")
        if status not in ("IN_PLAY", "PAUSED", "FINISHED") or hs is None or as_ is None:
            continue
        h = (am.get("homeTeam") or {}).get("name", "")
        a = (am.get("awayTeam") or {}).get("name", "")
        m = index.get(frozenset((canon(h), canon(a))))
        if not m:
            print("  unmatched API fixture: %s vs %s" % (h, a))
            continue
        # orient scores to our home/away
        if canon(m["home"]) == canon(h):
            nh, na = hs, as_
        else:
            nh, na = as_, hs
        if m.get("home_score") != nh or m.get("away_score") != na or m.get("status") != status:
            m["home_score"], m["away_score"], m["status"] = nh, na, status
            changed += 1
            print("  %s %d-%d %s [%s]" % (m["home"], nh, na, m["away"], status))

    if changed:
        with open(SCHEDULE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("Updated %d fixture(s)." % changed)
    else:
        print("No score changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
