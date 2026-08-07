#!/usr/bin/env python3
"""
One-off: correct four entries the geocoder placed badly, and move Skeleton
Coast out of Australia and back into Africa.

    python3 fix_coords.py            # from the automation/ folder

Safe to run twice -- it only writes when something actually changes.
"""
import json
import unicodedata
from pathlib import Path

TRAVEL = Path(__file__).resolve().parent.parent / "data" / "travel.json"

# name -> (correct coords, continent it belongs in, why)
FIXES = {
    "Skeleton Coast":       ([-19.9772, 13.0206], "Africa",
                             "matched Skeleton Creek Trail in Melbourne; now Terrace Bay, Namibia"),
    "Huangshan":            ([30.1300, 118.1600], "Asia",
                             "matched Huangshan City (Tunxi); now the mountain itself, 50 km north"),
    "Mae Hong Son, Thailand": ([19.3011, 97.9684], "Asia",
                             "matched the province centroid; now the town"),
    "Chongqing, China":     ([29.5630, 106.5516], "Asia",
                             "matched the municipality centroid, 140 km out; now the city"),
}

sort_key = lambda s: unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()

data = json.loads(TRAVEL.read_text(encoding="utf-8"))
changed = False

for name, (coords, continent, why) in FIXES.items():
    found = None
    for cont, arr in data.items():
        for entry in list(arr):
            if entry["name"] == name:
                found = (cont, entry)
                if cont != continent:          # filed under the wrong continent
                    arr.remove(entry)
                    data[continent].append(entry)
                    found = (continent, entry)
    if not found:
        print(f"  ?  {name}: not in travel.json, skipped")
        continue
    cont, entry = found
    if entry["coords"] != coords:
        print(f"  ~  {name}: {entry['coords']} -> {coords}  [{cont}]")
        print(f"        {why}")
        entry["coords"] = coords
        changed = True
    else:
        print(f"  =  {name}: already correct")

if changed:
    for arr in data.values():
        arr.sort(key=lambda c: sort_key(c["name"]))
    TRAVEL.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nSaved {TRAVEL}")
else:
    print("\nNothing to change.")
