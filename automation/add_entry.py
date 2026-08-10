#!/usr/bin/env python3
"""
add_entry.py -- add a log entry or a note to a project, without hand-editing
Markdown.

    python3 add_entry.py                 pick a project, then pick what to add
    python3 add_entry.py farmos          jump straight to that project
    python3 add_entry.py farmos --log    skip the question too
    python3 add_entry.py farmos --note

Companion to add_book.py and add_city.py, and it works the same way: it asks,
it writes, it offers to publish.

Two kinds of entry, because they are different jobs:

    LOG    one dated line. What happened. Cheap to add, never expands.
    NOTE   a titled section of prose. What you decided, and why.

The formatting rules that are easy to get wrong are handled here: a note is
inserted ABOVE the '## Log' heading (everything after that heading is read as
log entries, so a section written below it silently vanishes), a log line goes
in at the top of the list, and `updated:` in the front matter is bumped for you.

Editing something that already exists is still just opening the file. This is
only for adding.

No dependencies beyond the standard library.
"""

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PROJECTS_DIR = PROJECT_ROOT / "data" / "projects"

LOG_HEADING = re.compile(r"^(#{1,6})\s+Log\s*$", re.MULTILINE | re.IGNORECASE)
EDITOR_FALLBACKS = ("nvim", "vim", "vi", "nano")


# --------------------------------------------------------------------- asking

def ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        sys.exit("\nCancelled. Nothing written.")
    return answer or default


def ask_yes_no(prompt, default=False):
    raw = ask(f"{prompt} ({'Y/n' if default else 'y/N'})").lower()
    return default if not raw else raw.startswith("y")


# These fork and return straight away, so the file would be read back before a
# word had been typed. Their wait flag is what makes them behave like vi does.
WAIT_FLAG = {"code": "--wait", "codium": "--wait", "code-insiders": "--wait",
             "subl": "--wait", "sublime_text": "--wait", "atom": "--wait",
             "gedit": "--wait", "mate": "--wait"}


def editor_command(editor, path):
    flag = WAIT_FLAG.get(Path(editor).name)
    return [editor, flag, str(path)] if flag else [editor, str(path)]


def pick_editor(explicit=None):
    for candidate in (explicit, os.environ.get("EDITOR"), os.environ.get("VISUAL")):
        if candidate and shutil.which(candidate):
            return shutil.which(candidate)
    for candidate in EDITOR_FALLBACKS:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def write_in_editor(seed, editor):
    """Open a scratch file so the body can be written with real editing, rather
    than typed blind at a prompt terminated by a magic word."""
    with tempfile.NamedTemporaryFile("w+", suffix=".md", delete=False) as tmp:
        tmp.write(seed)
        path = Path(tmp.name)
    try:
        subprocess.call(editor_command(editor, path))
        text = path.read_text(encoding="utf-8")
    finally:
        path.unlink(missing_ok=True)
    # Drop the instruction lines: anything that starts with a marker comment.
    body = "\n".join(l for l in text.splitlines() if not l.startswith(">> "))
    return body.strip()


# ------------------------------------------------------------------- choosing

def projects():
    if not PROJECTS_DIR.is_dir():
        sys.exit(f"No projects directory at {PROJECTS_DIR}")
    return sorted(f for f in PROJECTS_DIR.glob("*.md") if not f.name.startswith("_"))


def empty_headings(text):
    """Headings with nothing under them, in file order.

    The project files are scaffolded with the sections still to be written, so
    the common case is filling one in -- not adding another. Before this, asking
    for a note always appended a NEW section at the end, which meant a second
    heading with the same name further down the page.
    """
    body = text.split("\n---\n", 1)[-1]
    offset = len(text) - len(body)
    heads = [(m.start() + offset, m.end() + offset, m.group(1).strip())
             for m in re.finditer(r"^#{1,6}[ \t]+(.+?)[ \t]*$", body, re.MULTILINE)]
    out = []
    for i, (start, end, name) in enumerate(heads):
        if name.lower() == "log":
            continue
        next_start = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        if not text[end:next_start].strip():
            out.append((name, end))
    return out


def fill_heading(text, position, body):
    """Write a body in under a heading that was left empty. `position` is the end
    of the heading's own line, so the blank line either side is added here."""
    rest = text[position:].lstrip("\n")
    return text[:position] + f"\n\n{body}\n\n" + rest


def title_of(path):
    for line in path.read_text(encoding="utf-8").splitlines()[:12]:
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip()
    return path.stem


def choose_project(named):
    files = projects()
    if not files:
        sys.exit(f"No project .md files in {PROJECTS_DIR}")

    if named:
        hits = [f for f in files if named.lower() in f.stem.lower()
                or named.lower() in title_of(f).lower()]
        if len(hits) == 1:
            return hits[0]
        if not hits:
            print(f"Nothing matching '{named}'.\n")
        else:
            files = hits

    print()
    for i, f in enumerate(files, 1):
        print(f"  {i}) {title_of(f):<34} {f.name}")
    print()
    while True:
        choice = ask("Which project (number)")
        if choice.isdigit() and 1 <= int(choice) <= len(files):
            return files[int(choice) - 1]
        print("  Pick one of the numbers above.")


# -------------------------------------------------------------------- writing

def this_month():
    return datetime.date.today().strftime("%Y-%m")


def bump_updated(text):
    """Set `updated:` in the front matter to this month, adding the line if the
    project never had one."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    front, rest = text[:end], text[end:]
    if re.search(r"^updated:", front, re.MULTILINE):
        front = re.sub(r"^updated:.*$", f"updated: {this_month()}", front,
                       count=1, flags=re.MULTILINE)
    else:
        front = front.rstrip("\n") + f"\nupdated: {this_month()}"
    return front + rest


def add_log(text, when, entry):
    """Newest first, directly under the '## Log' heading."""
    line = f"- {when} — {entry}"
    m = LOG_HEADING.search(text)
    if not m:
        # No log yet: start one at the end, where it has to live anyway.
        return text.rstrip("\n") + f"\n\n## Log\n\n{line}\n"
    head_end = m.end()
    after = text[head_end:]
    # Slide past the blank line the heading is followed by, then insert.
    lead = len(after) - len(after.lstrip("\n"))
    return text[:head_end] + after[:lead] + line + "\n" + after[lead:]


def add_note(text, heading, body):
    """A section goes ABOVE the log, because everything below '## Log' is parsed
    as log entries and would be swallowed."""
    section = f"## {heading}\n\n{body}\n"
    m = LOG_HEADING.search(text)
    if not m:
        return text.rstrip("\n") + f"\n\n{section}"
    return text[:m.start()].rstrip("\n") + f"\n\n{section}\n" + text[m.start():]


def save(path, text):
    backup = path.with_suffix(".md.bak")
    shutil.copy2(path, backup)
    tmp = path.with_suffix(".md.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return backup


# ---------------------------------------------------------------------- flows

def do_log(path, text):
    print(f"\nA log entry is one line: what happened, not why you chose it.\n")
    when = ask("When (YYYY-MM, or a year)", this_month())
    entry = ""
    while not entry:
        entry = ask("What happened")
        if not entry:
            print("  Say something, or Ctrl-C to back out.")
    return add_log(text, when, entry), f'log entry "{entry[:48]}"'


def do_note(path, text, args):
    print("\nA note is a section of prose: what you decided, and why.\n")

    # Fill a section that is already scaffolded, rather than adding a second
    # heading with the same name at the bottom of the file.
    empties = empty_headings(text)
    heading, position = "", None
    if empties:
        print("  Sections waiting to be written:")
        for i, (name, _) in enumerate(empties, 1):
            print(f"    {i}) {name}")
        print(f"    n) a new section\n")
        while True:
            choice = ask("Which", "1").lower()
            if choice.startswith("n"):
                break
            if choice.isdigit() and 1 <= int(choice) <= len(empties):
                heading, position = empties[int(choice) - 1]
                break
            print("  Pick a number, or n for a new section.")

    while not heading:
        heading = ask("Section heading")
        if not heading:
            print("  A heading is required -- it becomes the link target.")

    editor = pick_editor(args.editor)
    if not editor:
        sys.exit("No editor found. Set $EDITOR or pass --editor.")

    seed = (f">> {heading}\n"
            ">> Write the section below. These >> lines are stripped out.\n"
            ">> Markdown works: **bold**, *italic*, [links](/books), lists, quotes.\n"
            ">> An image alone on its line becomes a captioned figure:\n"
            f">>   ![Alt text for a screen reader](/images/projects/{path.stem}/shot.png \"Caption.\")\n"
            ">> Save and close when you are done.\n\n")
    body = write_in_editor(seed, editor)
    if not body:
        sys.exit(f"Nothing written, so the project is unchanged.\n"
                 f"If {Path(editor).name} opened in a window and this appeared "
                 f"before you had typed anything, it returned control straight "
                 f"away. Use a terminal editor, or one that takes a wait flag.")

    if ask_yes_no("\nAdd an image to this section?"):
        src = ask("  Image path", f"/images/projects/{path.stem}/")
        if src and not src.endswith("/"):
            on_disk = PROJECT_ROOT / src.lstrip("/")
            if not on_disk.exists():
                print(f"  note: {on_disk} is not there yet. The link is written anyway.")
            alt = ask("  Alt text (what a screen reader should say)")
            caption = ask("  Caption (shown under it; blank to reuse the alt text)")
            title = f' "{caption}"' if caption else ""
            body += f"\n\n![{alt}]({src}{title})"

    if position is not None:
        return fill_heading(text, position, body), f'note under "{heading}"'
    return add_note(text, heading, body), f'note "{heading}"'


# ----------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Add a log entry or a note to an existing project.")
    ap.add_argument("project", nargs="?", help="project slug or part of its title")
    ap.add_argument("--log", action="store_true", help="add a log entry")
    ap.add_argument("--note", action="store_true", help="add a note section")
    ap.add_argument("--editor", help="editor for writing a note (overrides $EDITOR)")
    ap.add_argument("--no-build", action="store_true",
                    help="don't offer to run publish.py afterwards")
    args = ap.parse_args()

    path = choose_project(args.project)
    text = path.read_text(encoding="utf-8")
    print(f"\n{title_of(path)}   ({path})")

    kind = "log" if args.log else "note" if args.note else ""
    while kind not in ("log", "note"):
        kind = ask("Add a (l)og entry or a (n)ote", "l").lower()
        kind = "log" if kind.startswith("l") else "note" if kind.startswith("n") else ""

    text, what = do_log(path, text) if kind == "log" else do_note(path, text, args)
    text = bump_updated(text)

    backup = save(path, text)
    print(f"\nAdded {what} to {path.name}")
    print(f"  updated: {this_month()}")
    print(f"  previous version kept at {backup.name}")

    builder = SCRIPT_DIR / "publish.py"
    if args.no_build or not builder.exists():
        print(f"\nRun this to publish it:\n  python3 {builder}")
        return
    if ask_yes_no("\nPublish now?", default=True):
        print()
        subprocess.call([sys.executable, str(builder)])
    else:
        print(f"  Later, then:  python3 {builder}")


if __name__ == "__main__":
    main()
