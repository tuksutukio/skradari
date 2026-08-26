#!/usr/bin/env python3
"""One-shot live snapshot of what the fr24 receiver currently sees.

Unlike fr24.py's continuous poll loop, this does a single fetch and prints
what's in range right now — independent of whether fr24.py happens to be
running anywhere.
"""

import time

from fr24 import (
    ALARM_SQUAWKS,
    DUMP1090_URL,
    fetch_aircraft,
    format_aircraft,
    is_ground_vehicle,
    lookup_route,
    lookup_type,
    planespotters_url,
)


def main():
    current = fetch_aircraft()
    if current is None:
        print(f"couldn't reach the antenna at {DUMP1090_URL}")
        raise SystemExit(1)

    visible = []
    for ac in current.values():
        try:
            alt = int(ac["altitude"])
        except (TypeError, ValueError):
            alt = None

        if is_ground_vehicle(ac) and (alt is None or alt <= 100):
            continue

        if not ac["type"]:
            ac["type"] = lookup_type(ac["hex"])
        if not ac["route"]:
            ac["route"] = lookup_route(ac["callsign"])

        visible.append(ac)

    print(time.strftime("%d-%m-%Y %H:%M:%S"))

    alarms = [ac for ac in visible if ac["squawk"] in ALARM_SQUAWKS]
    for ac in alarms:
        print(f"*** {ALARM_SQUAWKS[ac['squawk']]} *** {format_aircraft(ac)}")

    others = [ac for ac in visible if ac["squawk"] not in ALARM_SQUAWKS]
    if not others and not alarms:
        print("nothing in range right now")
        return

    for ac in sorted(others, key=lambda ac: ac["hex"]):
        print(f"  {format_aircraft(ac)}  {planespotters_url(ac)}")


if __name__ == "__main__":
    main()
