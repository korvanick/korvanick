#!/usr/bin/env python3
"""
update_gallery.py -- rebuild the gallery thumbnails and data/gallery.json

Drop photos into images/gallery/, then run:

    python3 update_gallery.py
    python3 update_gallery.py --dry-run     # show what would happen, touch nothing
    python3 update_gallery.py --force       # rebuild every thumbnail

What it does, in order:
  1. converts any .heic/.heif to .jpg (browsers can't display HEIC)
  2. makes a thumbnail in images/gallery/thumbs/ for anything new or edited
  3. deletes thumbnails whose original photo is gone
  4. works out a date for each photo (from its filename, else its file date)
  5. reads GPS out of each photo's EXIF and matches it to a city in
     data/travel.json; anything with coordinates that matches nothing is
     written to data/gallery-review.txt for you to look at
  6. gives each photo a readable slug -- the city where it was taken, or a
     two-word petname when there is no location -- used for /gallery#<slug>
  7. writes data/gallery.json, newest first

Slugs are sticky: once a photo has one, it keeps it. Renaming would break any
link you had shared, so a slug is only ever minted for a photo that has none.
Use --reslug to mint them all again, after adding cities or hand-labelling.

Anything you add to an entry in gallery.json by hand is kept. Set "location" on
a photo the matcher couldn't place and it stays set; add your own fields (a
"place" note for somewhere that isn't a city on the map, say) and they survive
every future run.

It does NOT change file ownership. The old shell version chowned everything to
www-data, which locked you out of your own gallery folder and forced the next
run to need sudo -- which then chowned it again. nginx only needs to *read*
these files, so this script just makes sure the read bits are set and leaves
ownership alone.

Needs ImageMagick (`magick` on v7, `convert` on v6). Nothing else beyond the
Python standard library.
"""

import argparse, hashlib, json, math, os, re, shutil, subprocess, sys, tempfile
import time, urllib.parse, urllib.request
from datetime import date, datetime
from pathlib import Path

# This script lives in korvanick/automation/, so the site root is its parent.
SITE_ROOT   = Path(__file__).resolve().parent.parent
GALLERY_DIR = SITE_ROOT / "images" / "gallery"
THUMB_DIR   = GALLERY_DIR / "thumbs"
JSON_OUT    = SITE_ROOT / "data" / "gallery.json"
TRAVEL_JSON = SITE_ROOT / "data" / "travel.json"
REVIEW_OUT  = SITE_ROOT / "data" / "gallery-review.txt"
WEB_PREFIX  = "/images/gallery"

# How close a photo has to be to a city before we call it that city. Deliberately
# tight: a wrong label is worse than no label, and anything outside this lands in
# the review file with its coordinates so you can decide yourself.
MATCH_KM = 20

# Reverse geocoding, used only by --name-unmatched, to turn the coordinates of
# an unmatched photo into a place name you can act on.
NOMINATIM  = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "korvanick-gallery/1.0 (personal website build script)"

THUMB_MAX     = 500      # longest edge, in pixels -- tiles display at ~200px
THUMB_QUALITY = 75

WEB_SUFFIXES  = {".jpg", ".jpeg", ".png", ".webp"}
HEIC_SUFFIXES = {".heic", ".heif"}

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

# Petname words, for photos with no usable location. Kept deliberately plain --
# these are identifiers, not descriptions, and a slug that oversells itself is
# worse than one that doesn't try.
ADJECTIVES = """amber ancient bright brisk calm clear copper crisp distant dusty
    early empty faded far first foggy frozen gentle golden grey hidden high idle
    late lone long low mellow narrow near old open pale plain quiet rough shaded
    sharp short silent slow small soft steep still stray sunlit tall thin warm
    weathered wide windy winter""".split()

NOUNS = """arch bay bend bluff bridge canal cliff coast corner cove crest dock
    dune ferry field forest garden gate gorge grove harbour hill inlet island
    lane ledge market marsh meadow mill mouth orchard pass path pier plain point
    quarry rail ridge river road shore slope spring square stair stone street
    summit terrace track trail valley view wall well wharf""".split()


# ----------------------------------------------------------------------------- location

def find_identify(magick):
    """ImageMagick 7 runs `magick identify`; v6 has a separate `identify`."""
    if Path(magick).name.startswith("magick"):
        return [magick, "identify"]
    found = shutil.which("identify")
    return [found] if found else None


def _rational(text):
    """EXIF stores coordinates as three rationals: '47/1, 36/1, 2247/100'."""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        return None
    out = []
    for part in parts[:3]:
        if "/" in part:
            num, _, den = part.partition("/")
            try:
                den = float(den)
                out.append(float(num) / den if den else 0.0)
            except ValueError:
                return None
        else:
            try:
                out.append(float(part))
            except ValueError:
                return None
    while len(out) < 3:
        out.append(0.0)
    return out[0] + out[1] / 60 + out[2] / 3600


def exif_gps(identify, photo):
    """(lat, lon) from the photo's EXIF, or None. Never raises."""
    if not identify:
        return None
    fmt = "%[EXIF:GPSLatitude]|%[EXIF:GPSLatitudeRef]|%[EXIF:GPSLongitude]|%[EXIF:GPSLongitudeRef]"
    try:
        out = subprocess.run(identify + ["-format", fmt, str(photo)],
                             capture_output=True, text=True, timeout=20).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    lat_s, _, rest = out.partition("|")
    lat_ref, _, rest = rest.partition("|")
    lon_s, _, lon_ref = rest.partition("|")
    lat, lon = _rational(lat_s), _rational(lon_s)
    if lat is None or lon is None:
        return None
    if lat_ref.strip().upper().startswith("S"):
        lat = -lat
    if lon_ref.strip().upper().startswith("W"):
        lon = -lon
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180) or (lat == 0 and lon == 0):
        return None
    return round(lat, 6), round(lon, 6)


def load_cities():
    """Every city on the travel map, as (name, lat, lon)."""
    if not TRAVEL_JSON.exists():
        print(f"  (no {TRAVEL_JSON.name} -- skipping location matching)")
        return []
    try:
        data = json.loads(TRAVEL_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"  (could not parse {TRAVEL_JSON.name} -- skipping location matching)")
        return []
    return [(c["name"], c["coords"][0], c["coords"][1])
            for arr in data.values() for c in arr if c.get("coords")]


def km_apart(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(a))


def match_city(cities, lat, lon, radius=MATCH_KM):
    """Nearest city within the radius, else (None, nearest_name, distance)."""
    if not cities:
        return None, None, None
    name, clat, clon = min(cities, key=lambda c: km_apart(lat, lon, c[1], c[2]))
    dist = km_apart(lat, lon, clat, clon)
    return (name if dist <= radius else None), name, dist


def place_name(lat, lon):
    """Ask OpenStreetMap what is at these coordinates. Needs internet."""
    query = urllib.parse.urlencode({"lat": lat, "lon": lon, "format": "json",
                                    "zoom": 12, "addressdetails": 1})
    req = urllib.request.Request(f"{NOMINATIM}?{query}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            hit = json.load(resp)
    except Exception as e:
        return f"(lookup failed: {e})"
    addr = hit.get("address", {})
    town = (addr.get("city") or addr.get("town") or addr.get("village")
            or addr.get("municipality") or addr.get("county") or "")
    country = addr.get("country", "")
    state = addr.get("state", "")
    if town and country == "United States" and state:
        return f"{town}, {state}"
    if town and country:
        return f"{town}, {country}"
    return hit.get("display_name", "(no name found)")


# ----------------------------------------------------------------------------- slugs

def slugify(text):
    import unicodedata
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def petname(seed):
    """Deterministic two-word name, so the same photo always gets the same one."""
    digest = hashlib.sha1(seed.encode("utf-8")).digest()
    a = ADJECTIVES[int.from_bytes(digest[:4], "big") % len(ADJECTIVES)]
    n = NOUNS[int.from_bytes(digest[4:8], "big") % len(NOUNS)]
    return f"{a}-{n}"


def assign_slug(base, taken):
    """First free slug of base, base-2, base-3, ..."""
    slug, n = base, 1
    while slug in taken:
        n += 1
        slug = f"{base}-{n}"
    taken.add(slug)
    return slug


# ----------------------------------------------------------------------------- ImageMagick
def find_magick():
    for exe in ("magick", "convert"):
        found = shutil.which(exe)
        if found:
            return found
    sys.exit(
        "ImageMagick not found -- this script needs it to resize photos.\n"
        "    sudo apt install imagemagick\n"
        "For HEIC photos you also want:\n"
        "    sudo apt install libheif1 heif-gdk-pixbuf\n"
    )


def run_magick(magick, args):
    proc = subprocess.run([magick, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        msg = (proc.stderr or proc.stdout).strip().splitlines()
        return False, (msg[0] if msg else "unknown error")
    return True, ""


# ----------------------------------------------------------------------------- dates
def parse_date(path):
    """Work out when a photo was taken.

    Filenames from phones lead with the date (20260405_142115.jpg), so that's
    the most reliable source. Falls back to a bare year (2012.jpg), then to the
    file's own modification date.

    Returns ("YYYY-MM-DD", precise) or ("YYYY", False) for year-only names.
    """
    name = path.name
    m = re.match(r"^(\d{4})(\d{2})(\d{2})(?!\d)", name)
    if m:
        y, mo, d = (int(g) for g in m.groups())
        try:
            return date(y, mo, d).isoformat(), True
        except ValueError:
            pass
    m = re.match(r"^((?:19|20)\d{2})(?!\d)", name)
    if m:
        return m.group(1), False
    stamp = datetime.fromtimestamp(path.stat().st_mtime).date()
    return stamp.isoformat(), True


def sort_key(entry):
    """Newest first. Year-only names sort under the dated photos of that year."""
    d = entry["date"]
    padded = d if len(d) > 4 else d + "-00-00"
    return (padded, entry["src"])


def pretty(datestr):
    if len(datestr) == 4:
        return datestr
    y, m, d = datestr.split("-")
    return f"{MONTHS[int(m) - 1]} {int(d)}, {y}"


# ----------------------------------------------------------------------------- steps
def convert_heic(magick, dry_run):
    """Turn .heic/.heif originals into .jpg. Originals are left in place."""
    converted, failed = [], []
    for src in sorted(GALLERY_DIR.iterdir()):
        if not src.is_file() or src.suffix.lower() not in HEIC_SUFFIXES:
            continue
        dest = src.with_suffix(".jpg")
        if dest.exists():
            continue
        print(f"  HEIC -> JPG: {src.name}")
        if dry_run:
            converted.append(dest.name)
            continue
        ok, err = run_magick(magick, [str(src), "-auto-orient", str(dest)])
        if ok:
            converted.append(dest.name)
        else:
            failed.append((src.name, err))
    return converted, failed


def gallery_photos():
    return sorted(p for p in GALLERY_DIR.iterdir()
                  if p.is_file() and p.suffix.lower() in WEB_SUFFIXES)


def sync_thumbs(magick, photos, force, dry_run, size=THUMB_MAX, quality=THUMB_QUALITY):
    """Build a thumbnail for anything new, edited, or missing one."""
    made, failed = [], []
    if not dry_run:
        THUMB_DIR.mkdir(parents=True, exist_ok=True)
    for photo in photos:
        thumb = THUMB_DIR / photo.name
        if not force and thumb.exists() and thumb.stat().st_mtime >= photo.stat().st_mtime:
            continue
        print(f"  thumbnail: {photo.name}")
        if dry_run:
            made.append(photo.name)
            continue
        ok, err = run_magick(magick, [
            str(photo), "-auto-orient",
            "-thumbnail", f"{size}x{size}>",
            "-quality", str(quality),
            str(thumb),
        ])
        if ok:
            made.append(photo.name)
        else:
            failed.append((photo.name, err))
    return made, failed


def prune_thumbs(photos, dry_run):
    """Drop thumbnails whose original photo has been deleted."""
    if not THUMB_DIR.is_dir():
        return []
    keep = {p.name for p in photos}
    gone = []
    for thumb in sorted(THUMB_DIR.iterdir()):
        if thumb.is_file() and thumb.name not in keep:
            print(f"  orphan thumbnail removed: {thumb.name}")
            gone.append(thumb.name)
            if not dry_run:
                thumb.unlink()
    return gone


def existing_entries():
    """Whatever gallery.json already says, keyed by src -- so slugs stay put."""
    if not JSON_OUT.exists():
        return {}
    try:
        data = json.loads(JSON_OUT.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    out = {}
    for item in data:
        if isinstance(item, dict) and item.get("src"):
            out[item["src"]] = item
    return out


# Fields this script owns. Everything else in an entry was put there by hand
# and is carried through untouched.
OWNED = ("src", "date", "location", "slug")


def build_index(photos, identify, cities, radius=MATCH_KM, relocate=False, reslug=False):
    known = existing_entries()
    taken = set() if reslug else {e["slug"] for e in known.values() if e.get("slug")}

    entries, review, located, unlocated = [], [], 0, 0
    for photo in sorted(photos, key=lambda p: p.name):
        src = f"{WEB_PREFIX}/{photo.name}"
        datestr, _ = parse_date(photo)
        entry = {"src": src, "date": datestr}
        was = known.get(src, {})

        # Location: only recomputed for photos we haven't placed before,
        # unless --relocate says to look at everything again.
        if "location" in was and not relocate:
            entry["location"] = was["location"]
            located += 1
        else:
            gps = exif_gps(identify, photo)
            if gps is None:
                unlocated += 1
            else:
                city, nearest, dist = match_city(cities, *gps, radius=radius)
                if city:
                    entry["location"] = city
                    located += 1
                    print(f"  located: {photo.name} -> {city}")
                else:
                    unlocated += 1
                    near = f"{nearest} ({dist:.0f} km away)" if nearest else "nothing on the map"
                    review.append([photo.name, gps, near])

        # Slug: sticky once assigned; city name where we have one, petname if not.
        if was.get("slug") and not reslug:
            entry["slug"] = was["slug"]
        else:
            base = slugify(entry["location"]) if entry.get("location") else petname(photo.name)
            entry["slug"] = assign_slug(base, taken)

        # Keep anything you added to this entry yourself.
        for key, value in was.items():
            if key not in OWNED:
                entry[key] = value

        entries.append(entry)

    entries.sort(key=sort_key, reverse=True)
    return entries, review, located, unlocated


def name_unmatched(review):
    """Reverse geocode each unmatched photo so the review file names the place."""
    print(f"\nLooking up {len(review)} unmatched locations (about {len(review)}s)...")
    for row in review:
        row.append(place_name(*row[1]))
        print(f"  {row[0]}  ->  {row[3]}")
        time.sleep(1)      # Nominatim's usage policy: one request per second


def write_review(review, dry_run):
    """Photos that have coordinates but sit near no city you've listed."""
    if dry_run or not review:
        return
    header = ("Photos with GPS that matched no city in travel.json.\n"
              f"Matching radius is {MATCH_KM:g} km. Add the city with add_city.py, or widen\n"
              "the radius with --radius, then re-run update_gallery.py.\n\n"
              "Re-run with --name-unmatched to have OpenStreetMap name each spot.\n\n"
              "photo\tcoordinates\tnearest city on your map\tlooks like\n")
    rows = ["\t".join([r[0], f"{r[1][0]}, {r[1][1]}", f"nearest: {r[2]}"] +
                      ([r[3]] if len(r) > 3 else []))
            for r in review]
    REVIEW_OUT.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_OUT.write_text(header + "\n".join(rows) + "\n", encoding="utf-8")


def prompt_alt(entries, known, ask_all=False):
    """Ask for alt text, one photo at a time, skipping is one keystroke.

    Only new photos are asked about by default -- a run that adds three photos
    asks three questions, not three hundred. --alt widens it to every photo
    that still has none, for working through a backlog in sittings.

    Alt text is not in OWNED, so once written it is carried through every
    future run like any other hand-added field.
    """
    if not sys.stdin.isatty():
        return 0                      # cron, a pipe, or called from a script

    todo = [e for e in entries
            if not e.get("alt") and (ask_all or e["src"] not in known)]
    if not todo:
        return 0

    print(f"\n{len(todo)} photo{'' if len(todo) == 1 else 's'} without alt text.")
    print("Describe what is in the picture for someone who cannot see it.")
    print("Enter on its own skips one photo.  'stop' stops asking.\n")

    written = 0
    for entry in todo:
        name = entry["src"].rsplit("/", 1)[-1]
        where = entry.get("location") or "no location"
        print(f"  {name}   {pretty(entry.get('date', ''))}   {where}")
        try:
            answer = input("  alt: ").strip()
        except EOFError:
            break
        if answer.lower() in ("stop", "q", "quit"):
            print("  Stopped. The rest keep no alt text; they will be offered again.")
            break
        if answer:
            entry["alt"] = answer
            written += 1
    return written


def write_json(entries, dry_run):
    """Write via a temp file so a failed run can never leave a half-written list."""
    if dry_run:
        return
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(JSON_OUT.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(entries, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, JSON_OUT)
        os.chmod(JSON_OUT, 0o644)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def fix_read_bits(dry_run):
    """Make sure nginx can read what we just wrote -- without touching ownership."""
    if dry_run:
        return
    targets = [(GALLERY_DIR, 0o755), (THUMB_DIR, 0o755)]
    for d, mode in targets:
        if d.is_dir():
            try:
                os.chmod(d, mode)
            except PermissionError:
                pass
    for d in (GALLERY_DIR, THUMB_DIR):
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if f.is_file() and (f.stat().st_mode & 0o044) != 0o044:
                try:
                    os.chmod(f, 0o644)
                except PermissionError:
                    print(f"  (could not chmod {f.name} -- not yours?)")


def check_writable():
    problems = [p for p in (GALLERY_DIR, JSON_OUT.parent) if not os.access(p, os.W_OK)]
    if not problems:
        return
    sys.exit(
        "\nCannot write to:\n" + "".join(f"    {p}\n" for p in problems) +
        "\nDon't reach for sudo -- that's what caused this. Take ownership once:\n\n"
        f"    sudo chown -R $USER:www-data {SITE_ROOT}\n"
        f"    sudo find {SITE_ROOT} -type d -exec chmod 2775 {{}} +\n"
        f"    sudo find {SITE_ROOT} -type f -exec chmod 664 {{}} +\n"
    )


# ----------------------------------------------------------------------------- main
def main():
    global MATCH_KM
    ap = argparse.ArgumentParser(description="Rebuild gallery thumbnails and gallery.json")
    ap.add_argument("--dry-run", action="store_true", help="report only, change nothing")
    ap.add_argument("--force", action="store_true", help="rebuild every thumbnail")
    ap.add_argument("--keep-orphans", action="store_true",
                    help="leave thumbnails whose photo was deleted")
    ap.add_argument("--size", type=int, default=THUMB_MAX, help="thumbnail longest edge")
    ap.add_argument("--quality", type=int, default=THUMB_QUALITY, help="JPEG quality")
    ap.add_argument("--radius", type=float, default=MATCH_KM,
                    help=f"km from a travel.json city to count as a match (default {MATCH_KM})")
    ap.add_argument("--name-unmatched", action="store_true",
                    help="reverse geocode unmatched photos so the review file names them")
    ap.add_argument("--relocate", action="store_true",
                    help="re-read EXIF for photos already located, and re-match them")
    ap.add_argument("--reslug", action="store_true",
                    help="mint every slug again -- changes /gallery#<slug> links")
    ap.add_argument("--alt", action="store_true",
                    help="ask about every photo missing alt text, not just new ones")
    ap.add_argument("--no-alt", action="store_true",
                    help="do not ask for alt text at all")
    args = ap.parse_args()
    MATCH_KM = args.radius

    if not GALLERY_DIR.is_dir():
        sys.exit(f"Gallery folder not found: {GALLERY_DIR}")
    if not args.dry_run:
        check_writable()

    magick = find_magick()
    if args.dry_run:
        print("DRY RUN -- nothing will be written.\n")

    print(f"Scanning {GALLERY_DIR}")
    heic, heic_failed = convert_heic(magick, args.dry_run)
    photos = gallery_photos()
    if args.dry_run and heic:
        photos += [GALLERY_DIR / n for n in heic if not (GALLERY_DIR / n).exists()]

    made, failed = sync_thumbs(magick, photos, args.force, args.dry_run,
                               args.size, args.quality)
    pruned = [] if args.keep_orphans else prune_thumbs(photos, args.dry_run)

    identify = find_identify(magick)
    if identify is None:
        print("  (ImageMagick's identify not found -- skipping location matching)")
    cities = load_cities() if identify else []

    entries, review, located, unlocated = build_index(photos, identify, cities,
                                                      args.radius, args.relocate, args.reslug)
    if review and args.name_unmatched:
        name_unmatched(review)

    alt_written = 0
    if not args.dry_run and not args.no_alt:
        alt_written = prompt_alt(entries, existing_entries(), args.alt)

    write_json(entries, args.dry_run)
    write_review(review, args.dry_run)
    fix_read_bits(args.dry_run)

    print()
    print(f"  photos in gallery : {len(entries)}")
    print(f"  thumbnails built  : {len(made)}")
    print(f"  already current   : {len(entries) - len(made)}")
    if heic:
        print(f"  HEIC converted    : {len(heic)}  (originals left in place)")
    if pruned:
        print(f"  orphans removed   : {len(pruned)}")
    print(f"  located from EXIF : {located}")
    if alt_written:
        print(f"  alt text written  : {alt_written}")
    missing_alt = sum(1 for e in entries if not e.get("alt"))
    if missing_alt:
        print(f"  still without alt : {missing_alt}   (--alt to work through them)")
    print(f"  no location       : {unlocated}")
    if review:
        print(f"  NEEDS REVIEW      : {len(review)}  ->  {REVIEW_OUT}")
    for name, err in heic_failed + failed:
        print(f"  FAILED: {name} -- {err}")
    if entries:
        print(f"  newest photo      : {pretty(entries[0]['date'])}")
        print(f"  oldest photo      : {pretty(entries[-1]['date'])}")
    print(f"\n{'Would write' if args.dry_run else 'Wrote'} {JSON_OUT}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nCancelled.")
