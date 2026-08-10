#!/usr/bin/env python3
"""
new_page.py -- start a new blog post or a new project.

    python3 new_page.py              asks which, then asks the right questions
    python3 new_page.py post
    python3 new_page.py project

One script rather than two, because the two differ only in which questions get
asked and which folder the file lands in. Everything else -- the slug, the
refusal to overwrite, opening your editor -- is the same job.

It writes the front matter and a body stub. The body is yours. When you are
done writing it offers to run publish.py for you, so there is nothing to
remember afterwards.

    posts     data/posts/<slug>.md      ->  /blog/<slug>
    projects  data/projects/<slug>.md   ->  /projects/<slug>

To EDIT either one, just open the Markdown file and run publish.py. There is
no edit mode here and does not need to be one: these are text files, unlike
books.json, which is why add_book.py has one and this does not.

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
PROJECTS_SUBDIR = Path("data") / "projects"


def default_posts_dir():
    """Always <project>/data/posts. Deliberately not derived from the detected
    site directory -- the HTML pages live in pages/, the content does not."""
    return PROJECT_ROOT / POSTS_SUBDIR


def default_projects_dir():
    return PROJECT_ROOT / PROJECTS_SUBDIR

PROJECT_STUB = """Everything above the first heading becomes the state-of-play
block at the top of the page: what this is, where it stands, why it exists.
A paragraph or two.

## The problem

## What I tried

## Where it stands

## Log
- {month} - Started the page.
"""

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


def make_post(posts_dir, args):
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
    target = posts_dir / (f"_{slug}.md" if draft else f"{slug}.md")
    if target.exists():
        sys.exit(f"\n{target} already exists. Nothing written.")

    front = ("---\n"
             f"title: {title}\n"
             f"date: {date.isoformat()}\n"
             f"summary: {summary}\n"
             "---\n\n")
    target.write_text(front + BODY_STUB, encoding="utf-8")

    print(f"\nCreated {target}")
    if draft:
        print("  Marked as a draft. Rename it without the leading _ to publish.")
    else:
        print(f"  Will publish at /blog/{slug}")
    return target


def make_project(projects_dir, args):
    print(f"\nProjects directory: {projects_dir}\n")

    title = ""
    while not title:
        title = ask("Title")
        if not title:
            print("  A title is required.")

    suggested = slugify(title)
    slug = slugify(ask("Slug (used in the URL)", suggested)) or suggested
    summary = ask("Summary (one line, shown on the projects index)")

    status = ""
    while status not in ("active", "shelved"):
        status = ask("Status (active or shelved)", "active").lower()
        if status not in ("active", "shelved"):
            print("  Only two: active, or shelved.")

    this_month = datetime.date.today().strftime("%Y-%m")
    started = ask("Started (YYYY-MM, or blank)")
    built = ask("Built with (comma separated, or blank)")
    repo = ask("Repository URL (blank for none)")
    live = ask("Live URL (blank for none)")
    weight = ask("Weight -- orders it within its status group, lower is first", "5")

    target = projects_dir / f"{slug}.md"
    if target.exists():
        sys.exit(f"\n{target} already exists. Nothing written.")

    # Only fields with a value are written. A field left out reads as absent;
    # a field written as TODO reads as the word TODO, and that used to end up
    # on the live page.
    lines = ["---", f"title: {title}", f"slug: {slug}",
             f"summary: {summary}", f"status: {status}"]
    if started:
        lines.append(f"started: {started}")
    lines.append(f"updated: {this_month}")
    if built:
        lines.append(f"built_with: {built}")
    if repo:
        lines.append(f"repo: {repo}")
    if live:
        lines.append(f"live: {live}")
    lines.append(f"weight: {weight}")
    lines.append("---")
    lines.append("")

    target.write_text("\n".join(lines) + "\n"
                      + PROJECT_STUB.format(month=this_month), encoding="utf-8")

    print(f"\nCreated {target}")
    print(f"  Will publish at /projects/{slug}")
    print("  Bump 'updated:' whenever you add to the Log.")
    print("  To rename it later, change 'slug:' and run publish.py -- the old")
    print("  page is removed and anything still linking to it is flagged.")
    return target


def open_in_editor(target, args):
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


def offer_build(args):
    """The step everyone forgets. Ask, rather than expecting it remembered."""
    builder = SCRIPT_DIR / "publish.py"
    if args.no_build or not builder.exists():
        print(f"\nWhen the writing is done, run:\n  python3 {builder}")
        return
    if not ask_yes_no("\nBuild the site now?", default=True):
        print(f"  Later, then:  python3 {builder}")
        return
    print()
    subprocess.call([sys.executable, str(builder)])


def main():
    ap = argparse.ArgumentParser(description="Scaffold a new blog post or project.")
    ap.add_argument("kind", nargs="?", choices=["post", "project"],
                    help="what to create (asked for if omitted)")
    ap.add_argument("--posts", help="directory of .md posts (default: <project>/data/posts)")
    ap.add_argument("--projects", help="directory of .md projects (default: <project>/data/projects)")
    ap.add_argument("--no-edit", action="store_true",
                    help="don't offer to open the file in an editor")
    ap.add_argument("--no-build", action="store_true",
                    help="don't offer to run publish.py afterwards")
    ap.add_argument("--editor", help="editor to open the new file with (overrides $EDITOR)")
    args = ap.parse_args()

    kind = args.kind
    while kind not in ("post", "project"):
        kind = ask("Blog post or project?", "post").lower().rstrip("s")
        if kind not in ("post", "project"):
            print("  Type 'post' or 'project'.")

    if kind == "post":
        directory = (Path(args.posts).expanduser().resolve() if args.posts
                     else default_posts_dir())
    else:
        directory = (Path(args.projects).expanduser().resolve() if args.projects
                     else default_projects_dir())
    if not directory.is_dir():
        sys.exit(f"No directory at {directory} — create it first.")

    target = make_post(directory, args) if kind == "post" else make_project(directory, args)
    open_in_editor(target, args)
    offer_build(args)


if __name__ == "__main__":
    main()
