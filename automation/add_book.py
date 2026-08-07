#!/usr/bin/env python3
"""
add_book.py -- interactively add or edit a book in your books.js

    python3 add_book.py                    # add new book(s)
    python3 add_book.py --edit             # find a book and change it
    python3 add_book.py --edit dune        # jump straight to matches for "dune"
    python3 add_book.py --file /var/www/korvanick/scripts/books.js

It finds books.js under the site root (the parent of this automation/ folder)
automatically. A one-time backup (books.js.bak) is made before the first write
of each run. The render engine and modal in books.js are never touched.

Ordering: storage stays chronological (oldest -> newest) and the site flips
recently-completed, currently-reading and hexaseptim-tbr to newest-first at
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
    ("hexaseptim-tbr",     "To-read (hexaseptim-tbr)"),
    ("all-time-greats",    "All-time favorite"),
]
FIELD_ORDER = ["title", "author", "cover", "summary", "tags", "notes", "year", "rank"]

# This script lives in korvanick/automation/, so the site root is its parent
# and cover images live under images/bookCovers/ alongside the rest of the site.
SITE_ROOT = Path(__file__).resolve().parent.parent
COVER_DIR = SITE_ROOT / "images" / "bookCovers"


# ----------------------------------------------------------------------------- locating the file
def find_books_js(explicit):
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_file():
            sys.exit(f"File not found: {p}")
        return p
    env = os.environ.get("BOOKS_JS")
    if env and Path(env).expanduser().is_file():
        return Path(env).expanduser().resolve()

    hits = [p for p in SITE_ROOT.rglob("books.js")
            if "node_modules" not in p.parts and not p.name.endswith(".bak")]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        return Path(input("Path to books.js: ").strip()).expanduser().resolve()
    print("Found several books.js files:")
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
        "nginx only needs to read the files, so group-read is plenty.\n"
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


# ----------------------------------------------------------------------------- reading the array
def array_bounds(content):
    """Offsets just inside the myBooks [ ... ] literal."""
    key = content.find("const myBooks")
    if key == -1:
        sys.exit("Could not find 'const myBooks' in the file.")
    open_idx = content.find("[", key)
    if open_idx == -1:
        sys.exit("Could not find the start of the myBooks array.")
    m = re.search(r"^\];", content[key:], re.M)
    if not m:
        sys.exit("Could not find the end of the myBooks array (a line starting with '];').")
    return open_idx + 1, key + m.start()


def entry_spans(content):
    """(start, end) offsets of every top-level { ... } inside myBooks."""
    start, end = array_bounds(content)
    spans, depth, obj_start = [], 0, None
    in_str = esc = False
    i = start
    while i < end:
        c = content[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and obj_start is not None:
                spans.append((obj_start, i + 1))
                obj_start = None
        i += 1
    return spans


def entry_to_dict(text):
    """Turn one JS object literal into a dict, or None if it won't parse.

    Walks the text so that bare keys get quoted but anything inside a string
    value is left exactly as written.
    """
    out, i = [], 0
    in_str = esc = False
    while i < len(text):
        c = text[i]
        if in_str:
            out.append(c)
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", text[i:])
        if m:
            ident = m.group(0)
            j = i + len(ident)
            k = j
            while k < len(text) and text[k] in " \t":
                k += 1
            out.append(f'"{ident}"' if k < len(text) and text[k] == ":" else ident)
            i = j
            continue
        out.append(c)
        i += 1
    cleaned = re.sub(r",(\s*[}\]])", r"\1", "".join(out))
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def load_entries(content):
    """[(span, dict_or_None, title_string)] for every book in the file."""
    items = []
    for span in entry_spans(content):
        raw = content[span[0]:span[1]]
        data = entry_to_dict(raw)
        if data and "title" in data:
            title = data["title"]
        else:
            m = re.search(r'title:\s*"((?:[^"\\]|\\.)*)"', raw)
            title = m.group(1) if m else "(untitled)"
        items.append((span, data, title))
    return items


def existing_titles(content):
    return {t.lower() for _, _, t in load_entries(content)}


# ----------------------------------------------------------------------------- writing the array
def format_entry(entry):
    parts = []
    for f in FIELD_ORDER:
        if f in entry:
            parts.append(f"        {f}: {json.dumps(entry[f], ensure_ascii=False)}")
    for f, v in entry.items():                      # keep any field we don't know about
        if f not in FIELD_ORDER:
            parts.append(f"        {f}: {json.dumps(v, ensure_ascii=False)}")
    return "    {\n" + ",\n".join(parts) + "\n    },"


def _span_with_comma(content, span):
    """Extend a span over its trailing comma."""
    s, e = span
    j = e
    while j < len(content) and content[j] in " \t":
        j += 1
    if j < len(content) and content[j] == ",":
        e = j + 1
    return s, e


def replace_entry(content, span, entry):
    s, e = _span_with_comma(content, span)
    return content[:s] + format_entry(entry).lstrip() + content[e:]


def remove_entry(content, span):
    s, e = _span_with_comma(content, span)
    while e < len(content) and content[e] in " \t":
        e += 1
    if e < len(content) and content[e] == "\n":
        e += 1
    while s > 0 and content[s - 1] in " \t":
        s -= 1
    return content[:s] + content[e:]


def append_entry(content, entry_text):
    _, end = array_bounds(content)
    before = content[:end].rstrip()
    if not before.endswith(",") and not before.endswith("["):
        before += ","                       # keep the previous entry comma-terminated
    return before + "\n" + entry_text + "\n" + content[end:]


# ----------------------------------------------------------------------------- saving
class Saver:
    """Writes the file, backing it up once per run."""

    def __init__(self, path):
        self.path = path
        self.backed_up = False

    def save(self, content, entry_text_on_failure=None):
        try:
            if not self.backed_up:
                bak = self.path.with_name(self.path.name + ".bak")
                shutil.copy2(self.path, bak)
                print(f"Backup saved: {bak}")
                self.backed_up = True
            self.path.write_text(content, encoding="utf-8")
            return True
        except PermissionError:
            print(permission_help(self.path))
            if entry_text_on_failure:
                print("Your entry, so you can paste it in by hand:\n")
                print(entry_text_on_failure + "\n")
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


def add_mode(path, content, saver):
    while True:
        entry = build_entry()

        if entry["title"].lower() in existing_titles(content):
            if not ask(f'"{entry["title"]}" already exists. Add anyway '
                       f'(e.g. a re-read)? (y/n)', "n").lower().startswith("y"):
                print("Skipped. Tip: use --edit to update the existing entry.\n")
                if not ask("Add another? (y/n)", "n").lower().startswith("y"):
                    return content
                continue

        entry_text = format_entry(entry)
        print("\n" + entry_text + "\n")

        if ask("Add this book? (y/n)", "y").lower().startswith("y"):
            content = append_entry(content, entry_text)
            saver.save(content, entry_text)
            print("Added.")
            cover_reminder(entry)
            print()
        else:
            print("Discarded.\n")

        if not ask("Add another? (y/n)", "n").lower().startswith("y"):
            return content


# ----------------------------------------------------------------------------- edit mode
def pick_entry(content, query):
    items = load_entries(content)
    if not items:
        sys.exit("No books found in the array.")

    while True:
        q = (query or ask("Search by title or author (blank to list all)")).lower()
        query = None
        if q:
            matches = [it for it in items
                       if q in it[2].lower()
                       or q in str((it[1] or {}).get("author", "")).lower()]
        else:
            matches = items
        if not matches:
            print("  No matches.")
            continue
        if len(matches) > 30:
            print(f"  {len(matches)} matches -- narrow it down a bit.")
            continue

        print()
        for i, (_, data, title) in enumerate(matches, 1):
            tags = ", ".join((data or {}).get("tags", [])) or "?"
            author = (data or {}).get("author", "")
            print(f"  {i:>3}) {title}" + (f" -- {author}" if author else "") + f"   [{tags}]")
        print()
        choice = ask("Choose a number (blank to search again)")
        if not choice:
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(matches):
            span, data, title = matches[int(choice) - 1]
            if data is None:
                print(f'\n"{title}" is written in a style this script cannot parse '
                      f'safely.\nEdit that one by hand in books.js.\n')
                continue
            return span, data


def show_entry(entry):
    print()
    for f in FIELD_ORDER:
        if f not in entry:
            continue
        val = entry[f]
        if f == "notes" and val:
            first = val.splitlines()[0]
            extra = len(val.splitlines()) - 1
            val = first + (f"  (+{extra} more line{'s' if extra != 1 else ''})" if extra else "")
        elif isinstance(val, list):
            val = ", ".join(val)
        print(f"  {f:<9} {val if val != '' else '-'}")
    print()


def edit_notes(entry):
    current = entry.get("notes", "")
    if current:
        print("\nCurrent notes:\n" + "\n".join("  | " + l for l in current.splitlines()) + "\n")
        choice = ask("(e)ditor / (a)ppend / (r)etype / (c)lear / (k)eep", "e").lower()
    else:
        choice = ask("(e)ditor / (r)etype / (k)eep", "e").lower()

    if choice.startswith("k"):
        return
    if choice.startswith("c"):
        entry["notes"] = ""
    elif choice.startswith("e"):
        entry["notes"] = open_in_editor(current)
    elif choice.startswith("a"):
        added = ask_multiline("Notes to append")
        entry["notes"] = (current + "\n\n" + added).strip() if added else current
    else:
        entry["notes"] = ask_multiline("Notes")


def mark_finished(entry):
    tags = [t for t in entry.get("tags", []) if t not in
            ("currently-reading", "hexaseptim-tbr")]
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


def edit_mode(path, content, saver, query):
    span, entry = pick_entry(content, query)
    original = json.dumps(entry, sort_keys=True)
    move = False

    while True:
        show_entry(entry)
        print("  1) title    2) author   3) cover    4) summary")
        print("  5) tags     6) notes    7) year     8) rank")
        print("  f) mark finished (recently-completed + year + notes + move to front)")
        print(f"  m) move to front of its row(s)   [{'yes' if move else 'no'}]")
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
        elif choice == "q":
            print("Nothing written.")
            return content
        elif choice == "s":
            if json.dumps(entry, sort_keys=True) == original and not move:
                print("No changes.")
                return content
            entry_text = format_entry(entry)
            print("\n" + entry_text)
            print(f"\nMove to the end of the array (front of the row): "
                  f"{'yes' if move else 'no'}")
            if not ask("Save? (y/n)", "y").lower().startswith("y"):
                print("Discarded.")
                return content
            if move:
                content = append_entry(remove_entry(content, span), entry_text)
            else:
                content = replace_entry(content, span, entry)
            saver.save(content, entry_text)
            print("Saved.")
            cover_reminder(entry)
            return content
        else:
            print("  ?")


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Add or edit a book in books.js")
    ap.add_argument("--file", help="path to books.js (otherwise auto-detected)")
    ap.add_argument("-e", "--edit", nargs="?", const="", metavar="QUERY",
                    help="edit an existing book instead of adding one")
    args = ap.parse_args()

    path = find_books_js(args.file)
    check_writable(path)
    content = path.read_text(encoding="utf-8")
    print(f"\nEditing: {path}\n")

    saver = Saver(path)
    if args.edit is not None:
        edit_mode(path, content, saver, args.edit)
    else:
        add_mode(path, content, saver)
        print("Tip: python3 add_book.py --edit <title> updates a book you've finished.")

    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nCancelled -- nothing written.")
