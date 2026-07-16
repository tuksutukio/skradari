#!/usr/bin/env python3

import json
import sys
import time
import urllib.request

DUMP1090_URL      = "http://192.168.1.131/dump1090/data/aircraft.json"
ADSB_FI_URL       = "https://opendata.adsb.fi/api/v2/hex/{hex}"
ADSBDB_ROUTE_URL  = "https://api.adsbdb.com/v0/callsign/{callsign}"
PLANESPOTTERS_URL = "https://www.planespotters.net/search?q={hex} "
POLL_INTERVAL = 60

VSPEED_THRESHOLD  = 300   # ft per poll to count as climbing/descending
VSPEED_POLLS      = 3     # consecutive polls required before showing arrow

ALARM_SQUAWKS = {
    "7500": "HIJACK",
    "7600": "RADIO LOSS",
    "7700": "MAYDAY",
}


def fetch_json(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception:
        return None


def fetch_aircraft():
    data = fetch_json(DUMP1090_URL)
    if not data:
        return None

    aircraft = {}
    for ac in data.get("aircraft", []):
        hex_id = (ac.get("hex") or "").upper().strip()
        if not hex_id:
            continue
        aircraft[hex_id] = {
            "hex":      hex_id,
            "callsign": (ac.get("flight") or "").strip(),
            "altitude": ac.get("alt_baro") or ac.get("altitude"),
            "speed":    ac.get("gs") or ac.get("speed"),
            "squawk":   ac.get("squawk") or "",
            "type":     ac.get("t") or "",
            "route":    "",
        }
    return aircraft


def lookup_type(hex_id):
    data = fetch_json(ADSB_FI_URL.format(hex=hex_id))
    if not data:
        return ""
    if isinstance(data, list):
        return (data[0].get("t") or "") if data else ""
    ac = data.get("ac", [])
    if ac:
        return ac[0].get("t") or ""
    return data.get("t") or ""


def lookup_route(callsign):
    if not callsign:
        return ""
    data = fetch_json(ADSBDB_ROUTE_URL.format(callsign=callsign))
    if not data:
        return ""
    route = data.get("response", {}).get("flightroute", {})
    origin = route.get("origin", {}).get("iata_code", "")
    dest   = route.get("destination", {}).get("iata_code", "")
    if origin and dest:
        return f"{origin}→{dest}"
    return ""


def classify_intention(first_alt, last_alt, first_speed, last_speed):
    try:
        fa, la = int(first_alt), int(last_alt)
        delta = la - fa
        if delta > 2000:
            return "departure"
        if delta < -2000:
            return "arrival"
        if fa > 5000 and la > 5000:
            return "overflight"
    except (TypeError, ValueError):
        pass
    return "uncertain"


def bell():
    sys.stdout.write("\a")
    sys.stdout.flush()


def format_aircraft(ac, arrow=""):
    parts = [ac["hex"]]
    if ac["callsign"]:
        parts.append(ac["callsign"])
    if ac["altitude"] is not None:
        parts.append(f"{ac['altitude']}ft")
    if ac.get("route"):
        parts.append(ac["route"])
    if ac["type"]:
        parts.append(ac["type"])
    if arrow:
        parts.append(arrow)
    return " ".join(parts)


def planespotters_url(ac):
    return PLANESPOTTERS_URL.format(hex=ac["hex"])


def update_vspeed(hex_id, curr_alt, alt_history, arrow_state):
    """Track altitude history and return arrow if trend is confirmed."""
    history = alt_history.get(hex_id, [])

    try:
        curr = int(curr_alt)
    except (TypeError, ValueError):
        alt_history[hex_id] = []
        arrow_state.pop(hex_id, None)
        return ""

    history.append(curr)
    if len(history) > VSPEED_POLLS:
        history = history[-VSPEED_POLLS:]
    alt_history[hex_id] = history

    if len(history) < VSPEED_POLLS:
        return ""

    deltas = [history[i+1] - history[i] for i in range(len(history)-1)]

    if all(d > VSPEED_THRESHOLD for d in deltas):
        arrow = "↑"
    elif all(d < -VSPEED_THRESHOLD for d in deltas):
        arrow = "↓"
    else:
        arrow = ""

    prev_arrow = arrow_state.get(hex_id, "")
    arrow_state[hex_id] = arrow

    # only report when arrow changes
    if arrow != prev_arrow:
        return arrow
    return ""


def main():
    print(f"Polling {DUMP1090_URL} every {POLL_INTERVAL}s")

    known         = {}   # hex -> aircraft dict
    entry_state   = {}   # hex -> {alt, speed} at first appearance
    alt_history   = {}   # hex -> list of recent altitudes
    arrow_state   = {}   # hex -> current arrow ("↑", "↓", or "")
    ignored       = set()  # hex codes identified as ground vehicles
    no_alt_count  = {}   # hex -> consecutive polls without altitude

    while True:
        current = fetch_aircraft()

        if current is None:
            print(f"\n[{time.strftime('%H:%M:%S')}] fetch failed")
            time.sleep(POLL_INTERVAL)
            continue

        # drop ignored ground vehicles that have left the feed
        ignored -= ignored - set(current)

        entered = set(current) - set(known) - ignored
        exited  = set(known)   - set(current)

        output_lines = []

        for hex_id in sorted(entered):
            ac = current[hex_id]

            if not ac["type"]:
                ac["type"] = lookup_type(hex_id)
            if not ac["route"]:
                ac["route"] = lookup_route(ac["callsign"])

            # ground vehicle: no callsign, no type, at ground level
            try:
                alt = int(ac["altitude"])
            except (TypeError, ValueError):
                alt = None

            if not ac["callsign"] and not ac["type"] and (alt is None or alt <= 100):
                ignored.add(hex_id)
                continue

            squawk = ac["squawk"]
            if squawk in ALARM_SQUAWKS:
                bell()
                output_lines.append(f"*** {ALARM_SQUAWKS[squawk]} *** {format_aircraft(ac)}")

            output_lines.append(f"  + {format_aircraft(ac)}  {planespotters_url(ac)}")
            known[hex_id] = dict(ac)
            entry_state[hex_id] = {
                "alt":   ac["altitude"],
                "speed": ac["speed"],
            }
            alt_history[hex_id] = []
            arrow_state[hex_id] = ""

        for hex_id in sorted(exited):
            ac = known[hex_id]
            es = entry_state.get(hex_id, {})
            intention = classify_intention(
                es.get("alt"), ac["altitude"],
                es.get("speed"), ac["speed"],
            )
            suffix = f"  [{intention}]" if intention != "uncertain" else ""
            output_lines.append(f"  - {format_aircraft(ac)}{suffix}")

            del known[hex_id]
            entry_state.pop(hex_id, None)
            alt_history.pop(hex_id, None)
            arrow_state.pop(hex_id, None)

        if output_lines:
            print(f"\n{time.strftime('%d-%m-%Y %H:%M:%S')}")
            for line in output_lines:
                print(line)

        # vertical speed for aircraft that stayed; auto-ignore persistent no-altitude contacts
        arrows_output = []
        for hex_id, ac in current.items():
            if hex_id in entered:
                continue
            if hex_id not in known:
                continue

            if ac["altitude"] is None:
                no_alt_count[hex_id] = no_alt_count.get(hex_id, 0) + 1
                if no_alt_count[hex_id] >= 3:
                    ignored.add(hex_id)
                    del known[hex_id]
                    entry_state.pop(hex_id, None)
                    alt_history.pop(hex_id, None)
                    arrow_state.pop(hex_id, None)
                    no_alt_count.pop(hex_id, None)
                    continue
            else:
                no_alt_count.pop(hex_id, None)

            arrow = update_vspeed(hex_id, ac["altitude"], alt_history, arrow_state)
            known[hex_id] = dict(ac)
            if arrow:
                arrows_output.append(f"  {arrow} {format_aircraft(ac, arrow)}")

        if arrows_output:
            print(f"\n{time.strftime('%d-%m-%Y %H:%M:%S')}")
            for line in arrows_output:
                print(line)

        if not output_lines and not arrows_output:
            print(".", end="", flush=True)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
