#!/usr/bin/env python3
"""
add_city.py -- add cities to your travel map by name. Coordinates are looked up
automatically via OpenStreetMap's Nominatim geocoder, so you never hand-enter
lat/lon (or ask an AI).

    python3 add_city.py                             # interactive: type a city, blank to stop
    python3 add_city.py Porvoo Kuopio Koli           # add the cities you name
    python3 add_city.py --file cities_to_add.txt      # one city per line
    python3 add_city.py --file cities_to_add.txt --continent Europe --type been

New cities are appended to data/travel.json in your existing shape:
    { "<continent>": [ {"name","coords":[lat,lon],"type","message"}, ... ], ... }
Highlighted cities carry "highlight": true and, optionally, "rank".

The continent is detected from the matched country (override for a whole run with
--continent). Marker style follows --type: been (a filled dot) or future (an
open ring, for somewhere not visited yet; default been). Pass --highlight to
give the city an always-on card on the map; add a "rank" to it in travel.json
afterwards to say how early it claims space when cards compete. Cities already
present (matched by name, any continent)
are skipped. Each match prints the full place name so you can catch a wrong hit.

Standard library only. Needs internet when run; waits ~1s between lookups to
respect Nominatim's usage policy.
"""

import argparse, json, sys, time, urllib.parse, urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA = SCRIPT_DIR.parent / "data" / "travel.json"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "korvanick-travel-map/1.0 (personal website build script)"

CONTINENTS = ["North America", "Europe", "Asia", "South America",
              "Africa", "Australia and Oceania", "Antarctica"]

# ISO-3166 alpha-2 country code -> continent key (matches the JSON's continents).
# Purely organizational; if a code is missing it falls back to --continent.
_CC = {
 "North America": "US CA MX GL BM GT BZ SV HN NI CR PA CU DO HT JM BS BB TT AG DM GD KN LC VC PR AW CW SX KY TC VG AI MS BQ",
 "South America": "BR AR CL PE CO VE EC BO PY UY GY SR GF FK",
 "Europe": "GB IE FR DE ES PT IT NL BE LU CH AT DK SE NO FI IS EE LV LT PL CZ SK HU RO BG GR HR SI RS BA ME MK AL XK UA BY MD RU MT CY AD MC SM VA LI FO GI",
 "Asia": "CN JP KR KP IN PK BD LK NP BT MM TH VN LA KH MY SG ID PH BN TL MN KZ UZ TM KG TJ AF IR IQ SA AE QA BH KW OM YE JO IL PS LB SY TR GE AM AZ HK MO TW MV",
 "Africa": "EG MA DZ TN LY SD SS ET ER DJ SO KE UG TZ RW BI CD CG GA CM NG GH CI SN ML BF NE TD MR GM GW GN SL LR TG BJ CF ZA NA BW ZW ZM MW MZ AO MG SC MU KM CV ST SZ LS DZ",
 "Australia and Oceania": "AU NZ FJ PG SB VU WS TO KI FM MH NR PW TV CK NC PF GU",
 "Antarctica": "AQ",
}
CODE_TO_CONTINENT = {code: cont for cont, codes in _CC.items() for code in codes.split()}


def geocode(city):
    query = urllib.parse.urlencode({"q": city, "format": "json", "limit": 1, "addressdetails": 1})
    req = urllib.request.Request(f"{NOMINATIM}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        results = json.load(resp)
    if not results:
        return None
    hit = results[0]
    cc = (hit.get("address", {}).get("country_code") or "").upper()
    return {"lat": round(float(hit["lat"]), 6), "lon": round(float(hit["lon"]), 6),
            "cc": cc, "display_name": hit["display_name"]}


def load_data(path):
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            sys.exit(f"{path} exists but isn't valid JSON — fix or move it first.")
    else:
        data = {}
    for c in CONTINENTS:                 # keep the continent keys present and ordered
        data.setdefault(c, [])
    return data


def gather_input(args):
    if args.file:
        return [c.strip() for c in Path(args.file).read_text(encoding="utf-8").splitlines() if c.strip()]
    if args.cities:
        return args.cities
    print("Enter cities one at a time (blank line to finish):")
    out = []
    while True:
        c = input("City: ").strip()
        if not c:
            break
        out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser(description="Add cities to the travel map by name.")
    ap.add_argument("cities", nargs="*", help="city names to add")
    ap.add_argument("--file", help="text file with one city per line")
    ap.add_argument("--data", help="path to travel.json (default: ../data/travel.json)")
    ap.add_argument("--continent", choices=CONTINENTS, help="force a continent for every city this run")
    ap.add_argument("--type", default="been", choices=["been", "future"],
                    help="been = filled dot, future = open ring (default been)")
    ap.add_argument("--highlight", action="store_true",
                    help="give these cities an always-on card on the map")
    args = ap.parse_args()

    data_path = Path(args.data).expanduser().resolve() if args.data else DEFAULT_DATA
    data_path.parent.mkdir(parents=True, exist_ok=True)

    cities = gather_input(args)
    if not cities:
        sys.exit("No cities given.")

    data = load_data(data_path)
    have = {e["name"].lower() for c in data.values() for e in c}

    added, skipped, failed = 0, [], []
    for city in cities:
        if city.lower() in have:
            skipped.append(city)
            print(f"  = {city}: already on the map, skipping")
            continue
        try:
            hit = geocode(city)
        except Exception as e:
            failed.append(city)
            print(f"  ! {city}: lookup error ({e})")
            time.sleep(1)
            continue
        if not hit:
            failed.append(city)
            print(f"  ! {city}: no match found — check the spelling")
            time.sleep(1)
            continue

        continent = args.continent or CODE_TO_CONTINENT.get(hit["cc"])
        if not continent:
            continent = "Europe"
            print(f"  ? {city}: couldn't map country '{hit['cc']}' to a continent — filed under Europe, move if needed")

        entry = {"name": city, "coords": [hit["lat"], hit["lon"]], "type": args.type}
        if args.highlight:
            entry["highlight"] = True
        entry["message"] = ""
        data[continent].append(entry)
        have.add(city.lower())
        added += 1
        print(f"  + {city}  ->  [{hit['lat']}, {hit['lon']}]  {continent}   ({hit['display_name']})")
        time.sleep(1)   # be polite to the free geocoder

    data_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(len(v) for v in data.values())
    print(f"\nAdded {added}, skipped {len(skipped)}, failed {len(failed)}.  {total} cities total.")
    print(f"Saved to {data_path}")
    if failed:
        print("Fix the spelling and re-run these: " + ", ".join(failed))


if __name__ == "__main__":
    main()
