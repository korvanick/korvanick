#!/usr/bin/env python3
"""
add_book.py -- interactively add or edit a book in data/books.json

    python3 add_book.py                    # add new book(s)
    python3 add_book.py --edit             # find a book and change it
    python3 add_book.py --edit dune        # jump straight to matches for "dune"
    python3 add_book.py --file /var/www/korvanick/data/books.json

The data lives in data/books.json, alongside gallery.json and travel.json.
scripts/books.js fetches it at page load and is never touched by this script.
A one-time backup (books.json.bak) is made before the first write of each run,
and every write goes to a temp file first, so an interrupted run cannot leave a
half-written array behind.

Ordering: storage stays chronological (oldest -> newest) and the site flips
recently-completed, currently-reading and to-be-read to newest-first at
display time. So "move to the front of the row" just means "move to the end of
the array" -- which is what the edit mode's move option (and "mark finished")
does for you.

No dependencies beyond the Python standard library.
"""

import argparse, datetime, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

CATEGORIES = [
    ("recently-completed", "Recently completed (read)"),
    ("currently-reading",  "Currently reading"),
    ("to-be-read",         "To be read"),
    ("all-time-greats",    "All-time favorite"),
]

# Canonical key order for every entry written back out. Keys not listed here are
# preserved and appended, so an experimental field added by hand is never lost.
FIELD_ORDER = ["title", "author", "year", "cover", "tags", "rank", "summary", "quote", "notes"]

# Fields kept on every book even when empty, so books.js can test one way.
# `year` and `rank` stay sparse: absent means "not recorded" / "not ranked".
ALWAYS_PRESENT = ["title", "author", "cover", "tags", "summary", "notes"]

# This script lives in korvanick/automation/, so the site root is its parent.
SITE_ROOT = Path(__file__).resolve().parent.parent
COVER_DIR = SITE_ROOT / "images" / "bookCovers"
DEFAULT_DATA = SITE_ROOT / "data" / "books.json"


# ----------------------------------------------------------------------------- locating the file
def find_books_json(explicit):
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_file():
            sys.exit(f"File not found: {p}")
        return p
    env = os.environ.get("BOOKS_JSON")
    if env and Path(env).expanduser().is_file():
        return Path(env).expanduser().resolve()
    if DEFAULT_DATA.is_file():
        return DEFAULT_DATA

    hits = [p for p in SITE_ROOT.rglob("books.json")
            if "node_modules" not in p.parts and not p.name.endswith(".bak")]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit(f"No books.json found. Expected it at:\n    {DEFAULT_DATA}\n"
                 f"Pass --file if it lives somewhere else.")
    print("Found several books.json files:")
    for i, p in enumerate(hits, 1):
        print(f"  {i}) {p}")
    return hits[int(input("Choose one: ")) - 1]


def permission_help(path):
    return (
        f"\nCannot write to {path}\n"
        f"  (or to its folder {path.parent}, which is where the .bak goes).\n\n"
        "Don't fix this with sudo -- root-owned files just move the problem to\n"
        "your editor and git. Give your user ownership once instead:\n\n"
        f"    sudo chown -R $USER:www-data {SITE_ROOT}\n"
        f"    sudo find {SITE_ROOT} -type d -exec chmod 2775 {{}} +\n"
        f"    sudo find {SITE_ROOT} -type f -exec chmod 664 {{}} +\n\n"
        "Apache only needs to read the files, so group-read is plenty.\n"
    )


def check_writable(path):
    """Fail fast: no point answering ten prompts and then hitting Errno 13."""
    if os.access(path, os.W_OK) and os.access(path.parent, os.W_OK):
        return
    sys.exit(permission_help(path))


# ----------------------------------------------------------------------------- prompts
def ask(prompt, default=""):
    shown = f" [{default}]" if default else ""
    try:
        return input(f"{prompt}{shown}: ").strip() or default
    except EOFError:
        sys.exit("\nInput ended -- stopping here.")


def ask_int(prompt, default=""):
    """Ask for a whole number. Blank means 'skip' -- never raises on typos."""
    while True:
        raw = ask(prompt, default)
        if not raw:
            return None
        if raw.lstrip("-").isdigit():
            return int(raw)
        print("  Please enter a whole number, or leave it blank to skip.")


def open_in_editor(initial=""):
    """Hand the text off to $VISUAL / $EDITOR (nano if neither is set)."""
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "nano"
    fd, tmp = tempfile.mkstemp(suffix=".txt", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(initial)
        try:
            subprocess.call([*editor.split(), tmp])
        except FileNotFoundError:
            print(f"  Could not launch '{editor}'. Set $EDITOR to something installed.")
            return initial
        return Path(tmp).read_text(encoding="utf-8").strip()
    finally:
        os.unlink(tmp)


def ask_multiline(prompt, initial=""):
    """Read free-form notes, blank lines and all.

    Single blank lines are kept, so paragraph breaks and spacing for emphasis
    survive. Input ends on TWO blank lines in a row, on END alone on a line, or
    on Ctrl-D. Typing EDIT opens $EDITOR instead, pre-filled with whatever
    you've typed so far (or the existing notes).
    """
    print(f"{prompt}:")
    print("  (blank lines are kept -- press Enter TWICE to finish, or type "
          "EDIT to use $EDITOR)")
    lines = []
    blanks = 0
    while True:
        try:
            line = input()
        except EOFError:
            print()
            break
        stripped = line.strip()
        if stripped == "END":
            break
        if stripped == "EDIT":
            return open_in_editor("\n".join(lines).strip() or initial)
        if stripped == "":
            blanks += 1
            if blanks >= 2:
                break
            lines.append("")
            continue
        blanks = 0
        lines.append(line)
    return "\n".join(lines).strip()


def ask_tags(current=None):
    print("Category / tags:")
    for i, (slug, label) in enumerate(CATEGORIES, 1):
        mark = " *" if current and slug in current else ""
        print(f"  {i}) {label}{mark}")
    default = ""
    if current:
        default = ",".join(str(i) for i, (slug, _) in enumerate(CATEGORIES, 1)
                           if slug in current)
    raw = ask("Choose number(s), comma-separated", default or "1")
    picks = []
    for tok in re.split(r"[,\s]+", raw):
        if tok.isdigit() and 1 <= int(tok) <= len(CATEGORIES):
            slug = CATEGORIES[int(tok) - 1][0]
            if slug not in picks:
                picks.append(slug)
    return picks or (current or ["recently-completed"])


def slugify(title):
    s = title.lower().replace("&", "and").replace("\u2019", "'").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# ----------------------------------------------------------------------------- the data file
def load_books(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"\n{path} is not valid JSON:\n  {e.msg} (line {e.lineno}, col {e.colno})\n"
                 f"Fix it by hand, or restore it with:\n"
                 f"    git checkout -- {path}\n")
    if not isinstance(data, list):
        sys.exit(f"{path} should contain a JSON array of books.")
    return data


def canonical(entry):
    """Reorder keys and drop empty optional ones, keeping unknown fields."""
    out = {}
    for f in FIELD_ORDER:
        if f in entry:
            val = entry[f]
            if f in ("year", "rank") and (val is None or val == ""):
                continue                      # sparse by design
            out[f] = val
    for f in ALWAYS_PRESENT:                  # one shape for books.js to test
        out.setdefault(f, [] if f == "tags" else "")
    for f, v in entry.items():                # never silently lose a field
        out.setdefault(f, v)
    return out


def dump_books(books):
    return json.dumps([canonical(b) for b in books],
                      indent=2, ensure_ascii=False) + "\n"


def existing_titles(books):
    return {str(b.get("title", "")).lower() for b in books}


# ----------------------------------------------------------------------------- saving
class Saver:
    """Writes the file atomically, backing it up once per run."""

    def __init__(self, path):
        self.path = path
        self.backed_up = False

    def save(self, books, entry_on_failure=None):
        try:
            if not self.backed_up:
                bak = self.path.with_name(self.path.name + ".bak")
                shutil.copy2(self.path, bak)
                print(f"Backup saved: {bak}")
                self.backed_up = True

            text = dump_books(books)
            # Write beside the target so os.replace stays on one filesystem.
            fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    fh.write(text)
                    fh.flush()
                    os.fsync(fh.fileno())
                shutil.copymode(self.path, tmp)
                os.replace(tmp, self.path)     # atomic: readers see old or new
            except BaseException:
                Path(tmp).unlink(missing_ok=True)
                raise
            return True
        except PermissionError:
            print(permission_help(self.path))
            if entry_on_failure is not None:
                print("Your entry, so you can paste it in by hand:\n")
                print(json.dumps(canonical(entry_on_failure), indent=2,
                                 ensure_ascii=False) + "\n")
            sys.exit(1)


def cover_reminder(entry):
    cover_path = COVER_DIR / entry.get("cover", "")
    if entry.get("cover") and not cover_path.exists():
        print(f"  Cover not in place yet -- drop the image at:\n    {cover_path}")


# ----------------------------------------------------------------------------- add mode
def build_entry():
    title = ask("Title")
    while not title:
        title = ask("Title (required)")
    author = ask("Author")
    tags = ask_tags()
    cover = ask("Cover filename", slugify(title) + "-cover.jpg")
    summary = ask("Summary")
    notes = ask_multiline("Notes")

    entry = {"title": title, "author": author, "cover": cover,
             "summary": summary, "tags": tags, "notes": notes}

    default_year = str(datetime.date.today().year) if "recently-completed" in tags else ""
    year = ask_int("Year read (blank to skip)", default_year)
    if year is not None:
        entry["year"] = year

    if "all-time-greats" in tags:
        rank = ask_int("Favorite rank (1 = shown first; blank to skip)")
        if rank is not None:
            entry["rank"] = rank
    return entry


def add_mode(books, saver):
    while True:
        entry = build_entry()

        if entry["title"].lower() in existing_titles(books):
            if not ask(f'"{entry["title"]}" already exists. Add anyway '
                       f'(e.g. a re-read)? (y/n)', "n").lower().startswith("y"):
                print("Skipped. Tip: use --edit to update the existing entry.\n")
                if not ask("Add another? (y/n)", "n").lower().startswith("y"):
                    return books
                continue

        print("\n" + json.dumps(canonical(entry), indent=2, ensure_ascii=False) + "\n")

        if ask("Add this book? (y/n)", "y").lower().startswith("y"):
            books.append(entry)               # end of array == front of the row
            saver.save(books, entry)
            print(f"Added. ({len(books)} books)")
            cover_reminder(entry)
            print()
        else:
            print("Discarded.\n")

        if not ask("Add another? (y/n)", "n").lower().startswith("y"):
            return books


# ----------------------------------------------------------------------------- edit mode
def pick_entry(books, query):
    if not books:
        sys.exit("No books found in the array.")

    while True:
        q = (query or ask("Search by title or author (blank to list all)")).lower()
        query = None
        if q:
            matches = [(i, b) for i, b in enumerate(books)
                       if q in str(b.get("title", "")).lower()
                       or q in str(b.get("author", "")).lower()]
        else:
            matches = list(enumerate(books))
        if not matches:
            print("  No matches.")
            continue
        if len(matches) > 30:
            print(f"  {len(matches)} matches -- narrow it down a bit.")
            continue

        print()
        for n, (i, b) in enumerate(matches, 1):
            tags = ", ".join(b.get("tags", [])) or "?"
            author = b.get("author", "")
            title = b.get("title", "(untitled)")
            print(f"  {n:>3}) {title}" + (f" -- {author}" if author else "") + f"   [{tags}]")
        print()
        choice = ask("Choose a number (blank to search again)")
        if not choice:
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(matches):
            return matches[int(choice) - 1]


def show_entry(entry):
    print()
    for f in FIELD_ORDER:
        if f not in entry:
            continue
        val = entry[f]
        if f in ("notes", "quote") and val:
            first = val.splitlines()[0]
            extra = len(val.splitlines()) - 1
            val = first + (f"  (+{extra} more line{'s' if extra != 1 else ''})" if extra else "")
        elif isinstance(val, list):
            val = ", ".join(val)
        print(f"  {f:<9} {val if val != '' else '-'}")
    print()


def edit_notes(entry, field="notes", label="notes"):
    """Free-form text on a book. Two fields use it: `notes` (my reaction) and
    `quote` (a passage from the book itself)."""
    current = entry.get(field, "")
    if current:
        print(f"\nCurrent {label}:\n" + "\n".join("  | " + l for l in current.splitlines()) + "\n")
        choice = ask("(e)ditor / (a)ppend / (r)etype / (c)lear / (k)eep", "e").lower()
    else:
        choice = ask("(e)ditor / (r)etype / (k)eep", "e").lower()

    if choice.startswith("k"):
        return
    if choice.startswith("c"):
        entry.pop(field, None) if field == "quote" else entry.update({field: ""})
    elif choice.startswith("e"):
        entry[field] = open_in_editor(current)
    elif choice.startswith("a"):
        added = ask_multiline(f"{label.capitalize()} to append")
        entry[field] = (current + "\n\n" + added).strip() if added else current
    else:
        entry[field] = ask_multiline(label.capitalize())


def mark_finished(entry):
    tags = [t for t in entry.get("tags", []) if t not in
            ("currently-reading", "to-be-read")]
    if "recently-completed" not in tags:
        tags.insert(0, "recently-completed")
    entry["tags"] = tags
    year = ask_int("Year read", str(datetime.date.today().year))
    if year is not None:
        entry["year"] = year
    edit_notes(entry)
    if "all-time-greats" in tags and "rank" not in entry:
        rank = ask_int("Favorite rank (1 = shown first; blank to skip)")
        if rank is not None:
            entry["rank"] = rank
    print("  Marked as finished; it will move to the front of the row on save.")
    return True


def edit_mode(books, saver, query):
    index, entry = pick_entry(books, query)
    entry = json.loads(json.dumps(entry))     # edit a copy; quit really means quit
    original = json.dumps(entry, sort_keys=True)
    move = False

    while True:
        show_entry(entry)
        print("  1) title    2) author   3) cover    4) summary")
        print("  5) tags     6) notes    7) year     8) rank")
        print("  9) quote (a passage from the book, shown above the notes)")
        print("  f) mark finished (recently-completed + year + notes + move to front)")
        print(f"  m) move to front of its row(s)   [{'yes' if move else 'no'}]")
        print("  d) delete this book")
        print("  s) save     q) quit without saving")
        choice = ask("Choose", "s").lower()

        if choice == "1":
            entry["title"] = ask("Title", entry.get("title", ""))
        elif choice == "2":
            entry["author"] = ask("Author", entry.get("author", ""))
        elif choice == "3":
            entry["cover"] = ask("Cover filename", entry.get("cover", ""))
        elif choice == "4":
            entry["summary"] = ask("Summary", entry.get("summary", ""))
        elif choice == "5":
            entry["tags"] = ask_tags(entry.get("tags", []))
        elif choice == "6":
            edit_notes(entry)
        elif choice == "9":
            edit_notes(entry, "quote", "quote")
        elif choice == "7":
            year = ask_int("Year read (blank to remove)", str(entry.get("year", "")))
            if year is None:
                entry.pop("year", None)
            else:
                entry["year"] = year
        elif choice == "8":
            rank = ask_int("Favorite rank (blank to remove)", str(entry.get("rank", "")))
            if rank is None:
                entry.pop("rank", None)
            else:
                entry["rank"] = rank
        elif choice == "f":
            move = mark_finished(entry)
        elif choice == "m":
            move = not move
        elif choice == "d":
            if ask(f'Delete "{entry.get("title", "")}"? (y/n)', "n").lower().startswith("y"):
                books.pop(index)
                saver.save(books)
                print(f"Deleted. ({len(books)} books)")
                return books
            print("  Kept.")
        elif choice == "q":
            print("Nothing written.")
            return books
        elif choice == "s":
            if json.dumps(entry, sort_keys=True) == original and not move:
                print("No changes.")
                return books
            print("\n" + json.dumps(canonical(entry), indent=2, ensure_ascii=False))
            print(f"\nMove to the end of the array (front of the row): "
                  f"{'yes' if move else 'no'}")
            if not ask("Save? (y/n)", "y").lower().startswith("y"):
                print("Discarded.")
                return books
            if move:
                books.pop(index)
                books.append(entry)
            else:
                books[index] = entry
            saver.save(books, entry)
            print("Saved.")
            cover_reminder(entry)
            return books
        else:
            print("  ?")


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Add or edit a book in data/books.json")
    ap.add_argument("--file", help="path to books.json (otherwise auto-detected)")
    ap.add_argument("-e", "--edit", nargs="?", const="", metavar="QUERY",
                    help="edit an existing book instead of adding one")
    args = ap.parse_args()

    path = find_books_json(args.file)
    check_writable(path)
    books = load_books(path)
    print(f"\nEditing: {path}  ({len(books)} books)\n")

    saver = Saver(path)
    if args.edit is not None:
        edit_mode(books, saver, args.edit)
    else:
        add_mode(books, saver)
        print("Tip: python3 add_book.py --edit <title> updates a book you've finished.")

    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nCancelled -- nothing written.")
