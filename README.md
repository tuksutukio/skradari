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

## legacy/

The original macOS bash/zsh version of this project (`fr24poll.sh`, `planespot.sh`,
`fr24mute.txt`), kept for reference. Superseded by `fr24.py`.
