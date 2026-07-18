# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

skradari is a personal ADS-B feeder monitor. `fr24.py` polls a local `dump1090` JSON
endpoint, tracks aircraft entering/leaving range, classifies departures/arrivals/overflights
by altitude trend, flags emergency squawks (7500/7600/7700), and prints a live console log
with vertical-speed arrows and PlaneSpotters links. Single file, no external dependencies,
no test suite, no build step.

## Running

```
python3 fr24.py
```

Requires a reachable `dump1090` JSON endpoint — `DUMP1090_URL` at the top of `fr24.py` is
hardcoded to the author's local receiver and must be edited to point at a different one.

There's no test suite or linter configured; verify changes by running the script against a
live (or mocked) `dump1090` endpoint and watching the console output over a few poll cycles.

## Architecture

Everything lives in `fr24.py` as one continuous poll loop (`main()`), driven by a handful of
module-level constants at the top of the file (`DUMP1090_URL`, poll/threshold tuning,
`ALARM_SQUAWKS`).

Each iteration of the loop:
1. Fetches the current aircraft snapshot (`fetch_aircraft`) from `dump1090`.
2. Diffs it against the previous snapshot (`known`) to get `entered` and `exited` hex codes.
3. For newly entered aircraft: checks emergency squawks first (before any network I/O, so the
   bell/alert isn't delayed by lookups), then enriches with type (`lookup_type`, via
   opendata.adsb.fi) and route (`lookup_route`, via api.adsbdb.com), then applies a
   ground-vehicle heuristic (no callsign, no type, at/near ground level) to filter transponder
   noise from cars/vehicles rather than real aircraft.
4. For aircraft that exited range: classifies the flight as departure/arrival/overflight/
   uncertain by comparing altitude at entry vs. exit (`classify_intention`).
5. For aircraft that stayed: tracks a rolling altitude history per hex code
   (`update_vspeed`) and emits a climb/descend arrow once a trend is confirmed over
   `VSPEED_POLLS` consecutive polls, only reporting when the arrow's state changes.

State is all in-memory, keyed by ICAO hex code, and lives entirely in local variables inside
`main()` (`known`, `entry_state`, `alt_history`, `arrow_state`, `ignored`, `no_alt_count`) —
there's no persistence across restarts. `ignored` accumulates hex codes identified as ground
vehicles or as contacts stuck without altitude data; membership is re-evaluated each poll so a
contact that starts showing a real callsign/type is re-admitted rather than staying blacklisted
for the rest of its time in the feed.

External services hit over the network, all best-effort (failures degrade gracefully to blank
fields, never crash the loop — see `fetch_json`):
- `dump1090` (local, primary aircraft feed)
- opendata.adsb.fi (aircraft type lookup)
- api.adsbdb.com (route lookup by callsign)
- planespotters.net (URL construction only, not fetched)

## legacy/

`legacy/` holds the original macOS bash/zsh implementation (`fr24poll.sh`, `planespot.sh`,
`fr24mute.txt`), superseded by `fr24.py` and kept for reference only. Don't extend it.
