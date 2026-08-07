#!/usr/bin/env python3
"""
new_post.py -- start a new blog post.

Asks for a title, date and summary, then writes a ready-to-edit Markdown file
to  data/posts/<slug>.md  with the front matter already filled in.

It does not write the body. That part is yours. When the post is finished:

    python3 automation/build_blog.py

Companion to add_book.py and add_city.py. No dependencies.
"""

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
POSTS_SUBDIR = Path("data") / "posts"


def default_posts_dir():
    """Always <project>/data/posts. Deliberately not derived from the detected
    site directory -- the HTML pages live in pages/, the content does not."""
    return PROJECT_ROOT / POSTS_SUBDIR

BODY_STUB = """Start writing here.

Markdown works as you would expect: **bold**, *italic*, [links](/books),
`code`, > quotes, - lists, and ![an image](/images/gallery/example.jpg)
where an image alone on its line becomes a captioned figure.
"""


def slugify(value):
    value = unicodedata.normalize("NFKD", str(value))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[\s_-]+", "-", value).strip("-")


def ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        sys.exit(1)
    return answer or default


def ask_date():
    today = datetime.date.today().isoformat()
    while True:
        raw = ask("Date (YYYY-MM-DD, backdating is fine)", today)
        try:
            return datetime.datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("  Not a valid date. Use YYYY-MM-DD, e.g. 2024-08-12.")


# $EDITOR wins if it is set. Otherwise try these in order, first one installed.
EDITOR_FALLBACKS = ("nvim", "vim", "vi", "nano")


def pick_editor(explicit=None):
    for candidate in (explicit, os.environ.get("EDITOR"), os.environ.get("VISUAL")):
        if candidate:
            found = shutil.which(candidate)
            if found:
                return found
            print(f"  '{candidate}' is not installed; falling back.")
    for candidate in EDITOR_FALLBACKS:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def ask_yes_no(prompt, default=False):
    d = "y/N" if not default else "Y/n"
    raw = ask(f"{prompt} ({d})").lower()
    if not raw:
        return default
    return raw.startswith("y")


def main():
    ap = argparse.ArgumentParser(description="Scaffold a new blog post.")
    ap.add_argument("--posts", help="directory of .md posts (default: <project>/data/posts)")
    ap.add_argument("--no-edit", action="store_true",
                    help="don't offer to open the file in an editor")
    ap.add_argument("--editor",
                    help="editor to open the new post with (overrides $EDITOR)")
    args = ap.parse_args()

    posts_dir = (Path(args.posts).expanduser().resolve() if args.posts
                 else default_posts_dir())
    if not posts_dir.is_dir():
        sys.exit(f"No posts directory at {posts_dir} — create it first.")

    print(f"\nPosts directory: {posts_dir}\n")

    title = ""
    while not title:
        title = ask("Title")
        if not title:
            print("  A title is required.")

    suggested = slugify(title)
    slug = slugify(ask("Slug (used in the URL)", suggested)) or suggested
    date = ask_date()
    summary = ask("Summary (one line, shown on the index; optional)")

    draft = ask_yes_no("Mark as a draft for now? Drafts are skipped by the build")
    filename = f"_{slug}.md" if draft else f"{slug}.md"
    target = posts_dir / filename

    if target.exists():
        print(f"\n{target} already exists. Nothing written.")
        sys.exit(1)

    front = "---\n"
    front += f"title: {title}\n"
    front += f"date: {date.isoformat()}\n"
    front += f"summary: {summary}\n"
    front += "---\n\n"
    target.write_text(front + BODY_STUB, encoding="utf-8")

    print(f"\nCreated {target}")
    if draft:
        print("  Marked as a draft. Rename it without the leading _ to publish.")
    else:
        print(f"  Will publish at /blog/{slug}")

    print("\nNext: write the body, then run")
    print(f"  python3 {SCRIPT_DIR / 'build_blog.py'}")

    if args.no_edit:
        return
    editor = pick_editor(args.editor)
    if not editor:
        print("\nNo editor found. Set $EDITOR or pass --editor.")
        return
    if ask_yes_no(f"\nOpen it in {Path(editor).name} now?", default=True):
        try:
            subprocess.call([editor, str(target)])
        except OSError as e:
            print(f"Could not launch {editor}: {e}")


if __name__ == "__main__":
    main()
