# skradari

A Python rewrite of a personal ADS-B feeder monitor. Polls a local `dump1090` instance,
tracks aircraft entering/leaving range, classifies departures/arrivals/overflights by
altitude trend, flags emergency squawks (7500/7600/7700), and prints a live console log
with vertical-speed arrows and PlaneSpotters links.

If you find this useful and/or have any comments or improvement ideas, never hesitate to
let me know.

## Requirements

Python 3, no external dependencies (see `requirements.txt`). Requires a reachable
`dump1090` JSON endpoint — edit `DUMP1090_URL` in `fr24.py` to point at yours.

## Usage

```
python3 fr24.py
```

## Mute list

`mute.txt`, next to `fr24.py` — one ICAO hex code per line, case-insensitive, `#` for
comments. Matching contacts are filtered out entirely in `fetch_aircraft()`, so both
`fr24.py`'s poll loop and `skywatch.py` skip them. Reloaded fresh on every fetch, so edits
take effect immediately without restarting anything. Missing file is fine (no mutes).

## legacy/

The original macOS bash/zsh version of this project (`fr24poll.sh`, `planespot.sh`,
`fr24mute.txt`), kept for reference. Superseded by `fr24.py`.
